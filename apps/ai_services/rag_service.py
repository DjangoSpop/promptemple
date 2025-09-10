"""
RAG (Retrieval-Augmented Generation) Service for Prompt Optimization
Integrates with existing LangChain infrastructure and credit system
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
import uuid

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model

# LangChain imports
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain.schema.runnable import RunnableSequence
    from langchain.schema import BaseRetriever
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    # Removed ContextualCompressionRetriever due to pydantic pickle issues
    # from langchain.retrievers import ContextualCompressionRetriever
    # from langchain.retrievers.document_compressors import LLMChainExtractor
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Local imports
from apps.templates.models import PromptLibrary
# Use centralized RAG service locator to avoid pydantic v2 conflicts
from apps.templates.rag.services import get_langchain_service

# Legacy compatibility - remove these temporary disabled imports
# Enable LangChain services with Pydantic 2.11.7 + LangChain 0.3.27 compatibility
try:
    from apps.templates.langchain_services import get_langchain_service
    LANGCHAIN_SERVICE_AVAILABLE = True
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"LangChain service not available: {e}")
    LANGCHAIN_SERVICE_AVAILABLE = False
    def get_langchain_service():
        return None
from apps.billing.models import UsageQuota, UserSubscription

logger = logging.getLogger(__name__)
User = get_user_model()

@dataclass
class RAGDocument:
    """Document structure for RAG system"""
    id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    title: str
    path: str
    updated_at: datetime
    hash: str

@dataclass
class Citation:
    """Citation information for retrieved documents"""
    id: str
    title: str
    source: str
    score: float
    snippet: str
    
@dataclass
class OptimizationRequest:
    """Request structure for prompt optimization"""
    session_id: str
    original: str
    mode: str = "fast"  # fast|deep
    context: Dict[str, str] = None
    budget: Dict[str, int] = None
    
@dataclass
class OptimizationResponse:
    """Response structure for prompt optimization"""
    optimized: str
    citations: List[Citation]
    diff_summary: str
    usage: Dict[str, int]
    run_id: str

class DocumentIndexer:
    """Handles document loading, chunking, and indexing"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 150
        self.collection_name = 'prompt-knowledge'
        self.index_path = Path(settings.BASE_DIR) / 'rag_index'
        self.index_path.mkdir(exist_ok=True)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize embeddings
        self.embeddings = self._get_embeddings()
        
    def _get_embeddings(self):
        """Get embedding model (local preferred for cost)"""
        # Try multiple embedding approaches
        
        # First try: langchain-huggingface
        try:
            return HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.warning(f"Failed to load HuggingFaceEmbeddings: {e}")
        
        # Second try: sentence-transformers directly
        try:
            from sentence_transformers import SentenceTransformer
            from langchain.embeddings.base import Embeddings
            
            class SimpleSentenceTransformerEmbeddings(Embeddings):
                def __init__(self, model_name="all-MiniLM-L6-v2"):
                    self.model = SentenceTransformer(model_name)
                
                def embed_documents(self, texts):
                    return self.model.encode(texts).tolist()
                
                def embed_query(self, text):
                    return self.model.encode([text])[0].tolist()
            
            logger.info("Using direct SentenceTransformer embeddings")
            return SimpleSentenceTransformerEmbeddings()
            
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}")
        
        # Third try: Use OpenAI embeddings if available
        try:
            from langchain_openai import OpenAIEmbeddings
            import os
            if os.getenv('OPENAI_API_KEY'):
                logger.info("Using OpenAI embeddings")
                return OpenAIEmbeddings()
        except Exception as e:
            logger.warning(f"OpenAI embeddings not available: {e}")
        
        logger.error("No embedding model available")
        return None
    
    def load_documents(self) -> List[RAGDocument]:
        """Load documents from various sources"""
        documents = []
        
        # Load markdown files
        documents.extend(self._load_markdown_files())
        
        # Load template database
        documents.extend(self._load_template_database())
        
        # Load documentation files
        documents.extend(self._load_documentation())
        
        logger.info(f"Loaded {len(documents)} documents for indexing")
        return documents
    
    def _load_markdown_files(self) -> List[RAGDocument]:
        """Load markdown files from project root"""
        documents = []
        base_dir = Path(settings.BASE_DIR)
        
        markdown_files = list(base_dir.glob("*.md"))
        
        for file_path in markdown_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                doc = RAGDocument(
                    id=f"md_{file_path.stem}_{file_hash[:8]}",
                    content=content,
                    metadata={
                        "type": "markdown",
                        "category": "documentation",
                        "language": "en",
                        "size": len(content)
                    },
                    source="documentation",
                    title=file_path.stem.replace("_", " ").title(),
                    path=str(file_path),
                    updated_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                    hash=file_hash
                )
                documents.append(doc)
                
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
                
        return documents
    
    def _load_template_database(self) -> List[RAGDocument]:
        """Load templates from database"""
        documents = []
        
        try:
            # Get high-quality templates
            templates = PromptLibrary.objects.filter(
                is_active=True,
                quality_score__gte=0.7
            ).select_related().iterator(chunk_size=100)
            
            for template in templates:
                content = f"{template.title}\n\n{template.content}"
                # Check if usage_examples attribute exists (handle different model versions)
                usage_examples = getattr(template, 'usage_examples', None) or getattr(template, 'examples', None)
                if usage_examples:
                    content += f"\n\nExamples:\n{usage_examples}"
                
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                doc = RAGDocument(
                    id=f"tpl_{template.id}_{content_hash[:8]}",
                    content=content,
                    metadata={
                        "type": "template",
                        "category": getattr(template, 'category', 'general'),
                        "intent": getattr(template, 'intent_category', 'general'),
                        "quality_score": float(getattr(template, 'quality_score', 0.5)),
                        "usage_count": getattr(template, 'usage_count', 0),
                        "tags": getattr(template, 'tags', [])
                    },
                    source="templates",
                    title=template.title,
                    path=f"template://{template.id}",
                    updated_at=template.updated_at,
                    hash=content_hash
                )
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            
        return documents
    
    def _load_documentation(self) -> List[RAGDocument]:
        """Load additional documentation files"""
        documents = []
        
        # Look for docs in apps
        apps_dir = Path(settings.BASE_DIR) / 'apps'
        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir():
                for doc_file in app_dir.glob("**/*.md"):
                    try:
                        content = doc_file.read_text(encoding='utf-8')
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        doc = RAGDocument(
                            id=f"doc_{app_dir.name}_{doc_file.stem}_{content_hash[:8]}",
                            content=content,
                            metadata={
                                "type": "documentation",
                                "app": app_dir.name,
                                "category": "code_docs"
                            },
                            source="app_docs",
                            title=f"{app_dir.name}: {doc_file.stem}",
                            path=str(doc_file),
                            updated_at=datetime.fromtimestamp(doc_file.stat().st_mtime),
                            hash=content_hash
                        )
                        documents.append(doc)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load {doc_file}: {e}")
        
        return documents
    
    def chunk_documents(self, documents: List[RAGDocument]) -> List[Document]:
        """Chunk documents for vector storage"""
        chunked_docs = []
        
        for doc in documents:
            chunks = self.text_splitter.split_text(doc.content)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very short chunks
                    continue
                    
                langchain_doc = Document(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,
                        "doc_id": doc.id,
                        "chunk_id": f"{doc.id}_chunk_{i}",
                        "source": doc.source,
                        "title": doc.title,
                        "path": doc.path,
                        "updated_at": doc.updated_at.isoformat(),
                        "hash": doc.hash
                    }
                )
                chunked_docs.append(langchain_doc)
        
        logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
        return chunked_docs
    
    def build_index(self, force_rebuild: bool = False) -> bool:
        """Build or update the vector index"""
        if not self.embeddings or not LANGCHAIN_AVAILABLE:
            logger.error("Embeddings or LangChain not available")
            return False
        
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.json"
        
        # Check if rebuild needed
        if not force_rebuild and index_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                last_build = datetime.fromisoformat(metadata['last_build'])
                if datetime.now() - last_build < timedelta(hours=1):
                    logger.info("Index is recent, skipping rebuild")
                    return True
            except Exception:
                pass
        
        try:
            # Load and chunk documents
            documents = self.load_documents()
            if not documents:
                logger.warning("No documents found for indexing")
                return False
            
            chunked_docs = self.chunk_documents(documents)
            if not chunked_docs:
                logger.warning("No chunks created from documents")
                return False
            
            # Build FAISS index
            logger.info(f"Building FAISS index with {len(chunked_docs)} chunks...")
            vector_store = FAISS.from_documents(chunked_docs, self.embeddings)
            
            # Save index
            vector_store.save_local(str(self.index_path))
            
            # Save metadata
            metadata = {
                "last_build": datetime.now().isoformat(),
                "document_count": len(documents),
                "chunk_count": len(chunked_docs),
                "collection": self.collection_name
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("RAG index built successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            return False

class RAGRetriever:
    """Handles document retrieval and context compression"""
    
    def __init__(self):
        self.index_path = Path(settings.BASE_DIR) / 'rag_index'
        self.embeddings = self._get_embeddings()
        self.vector_store = None
        self.retriever = None
        self._load_index()
        
    def _get_embeddings(self):
        """Get same embeddings as indexer"""
        # Use the same approach as DocumentIndexer
        indexer = DocumentIndexer()
        return indexer._get_embeddings()
    
    def _load_index(self):
        """Load existing FAISS index"""
        if not self.embeddings or not LANGCHAIN_AVAILABLE:
            return
            
        index_file = self.index_path / "index.faiss"
        if index_file.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(self.index_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self.retriever = self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 6}
                )
                logger.info("RAG index loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
    
    def retrieve_documents(self, query: str, top_k: int = 6) -> List[Document]:
        """Retrieve relevant documents"""
        if not self.retriever:
            logger.warning("No retriever available")
            return []
        
        try:
            docs = self.retriever.get_relevant_documents(query)
            return docs[:top_k]
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def create_citations(self, docs: List[Document], scores: List[float] = None) -> List[Citation]:
        """Create citation objects from retrieved documents"""
        citations = []
        
        for i, doc in enumerate(docs):
            score = scores[i] if scores and i < len(scores) else 0.0
            
            citation = Citation(
                id=doc.metadata.get('doc_id', f'doc_{i}'),
                title=doc.metadata.get('title', 'Unknown'),
                source=doc.metadata.get('source', 'unknown'),
                score=score,
                snippet=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            )
            citations.append(citation)
        
        return citations

class RAGAgent:
    """Main RAG agent for prompt optimization"""
    
    def __init__(self):
        self.retriever = RAGRetriever()
        self.langchain_service = get_langchain_service()
        
        # Budget limits
        self.default_budget = {
            "tokens_in": 2000,
            "tokens_out": 800,
            "max_credits": 5
        }
        
        # Optimization prompts
        self.optimization_prompt = self._create_optimization_prompt()
        
        # Check if service is available
        self.service_available = self.langchain_service is not None
        
    def _create_optimization_prompt(self) -> str:
        """Create the prompt optimization template"""
        return """You are a prompt optimization expert. Using the provided context and original prompt, create an improved version.

Context from knowledge base:
{context}

Original prompt:
{original_prompt}

Instructions:
1. Analyze the original prompt for clarity, specificity, and effectiveness
2. Use the context to inform improvements
3. Provide a clear, actionable optimized version
4. Explain the key improvements made

Respond with:
OPTIMIZED PROMPT:
[Your improved prompt here]

IMPROVEMENTS:
- [List key improvements made]

EXPLANATION:
[Brief explanation of changes and why they help]
"""
    
    async def optimize_prompt(self, request: OptimizationRequest) -> OptimizationResponse:
        """Main optimization method"""
        run_id = str(uuid.uuid4())
        start_time = timezone.now()
        
        # Retrieve relevant context
        retrieved_docs = self.retriever.retrieve_documents(request.original, top_k=6)
        citations = self.retriever.create_citations(retrieved_docs)
        
        # Prepare context
        context = "\n\n".join([
            f"Source: {doc.metadata.get('title', 'Unknown')}\n{doc.page_content}"
            for doc in retrieved_docs[:3]  # Limit context to avoid token overflow
        ])
        
        # Generate optimization
        if self.service_available and self.langchain_service.get("enabled"):
            try:
                result = await self._optimize_with_langchain(request, context)
            except Exception as e:
                logger.warning(f"LangChain optimization failed: {e}")
                result = self._fallback_optimization(request.original, citations)
        else:
            logger.info("Using fallback optimization (LangChain service not available)")
            result = self._fallback_optimization(request.original, citations)
        
        # Calculate usage
        processing_time = (timezone.now() - start_time).total_seconds()
        usage = {
            "tokens_in": len(request.original.split()) * 2,  # Rough estimate
            "tokens_out": len(result["optimized"].split()) * 2,
            "credits": 1 if request.mode == "fast" else 3
        }
        
        return OptimizationResponse(
            optimized=result["optimized"],
            citations=citations,
            diff_summary=result["diff_summary"],
            usage=usage,
            run_id=run_id
        )
    
    async def _optimize_with_langchain(self, request: OptimizationRequest, context: str) -> Dict[str, str]:
        """Optimize using LangChain service"""
        prompt = self.optimization_prompt.format(
            context=context,
            original_prompt=request.original
        )
        
        # Use existing LangChain service
        response = await self.langchain_service.generate_response(prompt)
        
        # Parse response
        content = response.get("content", "")
        
        # Extract sections
        optimized = self._extract_section(content, "OPTIMIZED PROMPT:")
        improvements = self._extract_section(content, "IMPROVEMENTS:")
        
        if not optimized:
            optimized = request.original  # Fallback
        
        return {
            "optimized": optimized,
            "diff_summary": improvements or "No specific improvements identified"
        }
    
    def _extract_section(self, content: str, section_header: str) -> str:
        """Extract a section from formatted response"""
        lines = content.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.strip().startswith(section_header):
                in_section = True
                continue
            elif in_section and line.strip() and line.strip().isupper() and line.strip().endswith(':'):
                break
            elif in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines).strip()
    
    def _fallback_optimization(self, original: str, citations: List[Citation]) -> Dict[str, str]:
        """Fallback optimization without LLM"""
        improvements = []
        optimized = original
        
        # Basic improvements
        if not original.strip().endswith(('.', '!', '?')):
            optimized = original.strip() + "."
            improvements.append("Added proper punctuation")
        
        if len(original.split()) < 5:
            improvements.append("Consider adding more specific details")
        
        # Use citations for suggestions
        if citations:
            top_source = citations[0]
            improvements.append(f"Consider context from: {top_source.title}")
        
        if not improvements:
            improvements.append("Prompt appears well-structured")
        
        return {
            "optimized": optimized,
            "diff_summary": "; ".join(improvements)
        }

# Global instances
_document_indexer = None
_rag_agent = None

def get_document_indexer() -> DocumentIndexer:
    """Get global document indexer instance"""
    global _document_indexer
    if _document_indexer is None:
        _document_indexer = DocumentIndexer()
    return _document_indexer

def get_rag_agent() -> RAGAgent:
    """Get global RAG agent instance"""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = RAGAgent()
    return _rag_agent

# Celery task for background indexing
try:
    from celery import shared_task
    
    @shared_task
    def rebuild_rag_index():
        """Background task to rebuild RAG index"""
        indexer = get_document_indexer()
        success = indexer.build_index(force_rebuild=True)
        return {"success": success, "timestamp": timezone.now().isoformat()}
        
except ImportError:
    logger.info("Celery not available, RAG indexing will be synchronous")