"""
Enhanced RAG (Retrieval-Augmented Generation) Service for Prompt Optimization
Includes streaming support and robust fallback mechanisms
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, AsyncGenerator
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
import uuid
import numpy as np

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model

# LangChain imports with fallback
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document
    from langchain_community.vectorstores import FAISS
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Local imports
from apps.templates.models import PromptLibrary
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

class SimpleEmbeddings:
    """Simple TF-IDF based embeddings as fallback"""
    
    def __init__(self):
        self.vocab = {}
        self.idf = {}
        self.fitted = False
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        import re
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency"""
        tf = {}
        total_tokens = len(tokens)
        if total_tokens == 0:
            return tf
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        # Normalize
        for token in tf:
            tf[token] = tf[token] / total_tokens
        return tf
    
    def fit(self, documents: List[str]):
        """Fit the embeddings on documents"""
        # Build vocabulary and compute IDF
        doc_count = len(documents)
        word_doc_count = {}
        
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                word_doc_count[token] = word_doc_count.get(token, 0) + 1
        
        # Compute IDF
        import math
        for word, count in word_doc_count.items():
            self.idf[word] = math.log(doc_count / count) if count > 0 else 0
        
        self.vocab = {word: i for i, word in enumerate(word_doc_count.keys())}
        self.fitted = True
        logger.info(f"✅ SimpleEmbeddings fitted on {doc_count} documents with {len(self.vocab)} vocab")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Convert texts to embeddings"""
        if not self.fitted:
            self.fit(texts)
            
        embeddings = []
        
        for text in texts:
            tokens = self._tokenize(text)
            tf = self._compute_tf(tokens)
            
            # Create TF-IDF vector
            vector = [0.0] * len(self.vocab)
            for word, tf_val in tf.items():
                if word in self.vocab:
                    idx = self.vocab[word]
                    idf_val = self.idf.get(word, 0)
                    vector[idx] = tf_val * idf_val
            
            embeddings.append(vector)
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Convert single text to embedding"""
        return self.embed_documents([text])[0]

class EnhancedDocumentIndexer:
    """Enhanced document indexer with robust fallbacks"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 150
        self.collection_name = 'prompt-knowledge'
        self.index_path = Path(settings.BASE_DIR) / 'rag_index'
        self.index_path.mkdir(exist_ok=True)
        
        # Initialize text splitter
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )
        else:
            self.text_splitter = None
        
        # Initialize embeddings with fallback
        self.embeddings = self._get_embeddings()
        
    def _get_embeddings(self):
        """Get embedding model with robust fallback strategy"""
        
        # Try HuggingFace embeddings with sentence-transformers
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            # Test the embeddings work
            test_result = embeddings.embed_query("test")
            if test_result:
                logger.info("✅ Using HuggingFace embeddings with sentence-transformers")
                return embeddings
        except Exception as e:
            logger.warning(f"HuggingFace embeddings failed: {e}")
        
        # Try sentence-transformers directly
        try:
            from sentence_transformers import SentenceTransformer
            
            class SentenceTransformerEmbeddings:
                def __init__(self, model_name="all-MiniLM-L6-v2"):
                    self.model = SentenceTransformer(model_name)
                
                def embed_documents(self, texts):
                    return self.model.encode(texts).tolist()
                
                def embed_query(self, text):
                    return self.model.encode([text])[0].tolist()
            
            embeddings = SentenceTransformerEmbeddings()
            # Test the embeddings work
            test_result = embeddings.embed_query("test")
            if test_result:
                logger.info("✅ Using SentenceTransformer embeddings directly")
                return embeddings
        except Exception as e:
            logger.warning(f"SentenceTransformer direct failed: {e}")
        
        # Fallback to simple TF-IDF embeddings
        logger.info("📊 Using SimpleEmbeddings (TF-IDF) as fallback")
        return SimpleEmbeddings()
    
    def load_documents(self) -> List[RAGDocument]:
        """Load documents from various sources"""
        documents = []
        
        # Load markdown files
        documents.extend(self._load_markdown_files())
        
        # Load template database
        documents.extend(self._load_template_database())
        
        # Load documentation files
        documents.extend(self._load_documentation())
        
        logger.info(f"✅ Loaded {len(documents)} documents for indexing")
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
            templates = PromptLibrary.objects.filter(
                is_active=True,
                quality_score__gte=0.7
            ).select_related().iterator(chunk_size=100)
            
            for template in templates:
                content = f"{template.title}\n\n{template.content}"
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
            if self.text_splitter:
                chunks = self.text_splitter.split_text(doc.content)
            else:
                # Simple chunking fallback
                chunks = [doc.content[i:i+self.chunk_size] 
                         for i in range(0, len(doc.content), self.chunk_size - self.chunk_overlap)]
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:
                    continue
                    
                if LANGCHAIN_AVAILABLE:
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
        
        logger.info(f"🔨 Created {len(chunked_docs)} chunks from {len(documents)} documents")
        return chunked_docs
    
    def build_index(self, force_rebuild: bool = False) -> bool:
        """Build or update the vector index"""
        if not self.embeddings:
            logger.error("❌ No embeddings available")
            return False
        
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.json"
        simple_index_file = self.index_path / "simple_index.json"
        
        # Check if rebuild needed
        if not force_rebuild and (index_file.exists() or simple_index_file.exists()):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                last_build = datetime.fromisoformat(metadata['last_build'])
                if datetime.now() - last_build < timedelta(hours=1):
                    logger.info("📋 Index is recent, skipping rebuild")
                    return True
            except Exception:
                pass
        
        try:
            # Load and chunk documents
            documents = self.load_documents()
            if not documents:
                logger.warning("⚠️ No documents found for indexing")
                return False
            
            # Build index based on available libraries
            if LANGCHAIN_AVAILABLE and hasattr(self.embeddings, 'embed_documents'):
                # Use FAISS if available
                chunked_docs = self.chunk_documents(documents)
                if not chunked_docs:
                    logger.warning("⚠️ No chunks created from documents")
                    return False
                
                logger.info(f"🚀 Building FAISS index with {len(chunked_docs)} chunks...")
                vector_store = FAISS.from_documents(chunked_docs, self.embeddings)
                vector_store.save_local(str(self.index_path))
                
                # Save metadata
                metadata = {
                    "last_build": datetime.now().isoformat(),
                    "document_count": len(documents),
                    "chunk_count": len(chunked_docs),
                    "collection": self.collection_name,
                    "index_type": "faiss"
                }
                logger.info("✅ FAISS index built successfully")
            else:
                # Build simple index
                logger.info(f"🚀 Building simple index with {len(documents)} documents...")
                
                # Fit embeddings if needed
                doc_texts = [doc.content for doc in documents]
                if hasattr(self.embeddings, 'fit'):
                    self.embeddings.fit(doc_texts)
                
                # Create simple index
                simple_index = {
                    "documents": [asdict(doc) for doc in documents],
                    "embeddings": self.embeddings.embed_documents(doc_texts)
                }
                
                with open(simple_index_file, 'w') as f:
                    json.dump(simple_index, f, default=str)
                
                # Save metadata
                metadata = {
                    "last_build": datetime.now().isoformat(),
                    "document_count": len(documents),
                    "chunk_count": len(documents),
                    "collection": self.collection_name,
                    "index_type": "simple"
                }
                logger.info("✅ Simple index built successfully")
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("🎉 RAG index built successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to build index: {e}")
            import traceback
            traceback.print_exc()
            return False

class StreamingRAGAgent:
    """Streaming RAG agent for real-time prompt optimization"""
    
    def __init__(self):
        self.index_path = Path(settings.BASE_DIR) / 'rag_index'
        self.embeddings = None
        self.vector_store = None
        self.simple_index = None
        self._load_index()
        
    def _load_index(self):
        """Load existing index"""
        # Try FAISS first
        index_file = self.index_path / "index.faiss"
        simple_index_file = self.index_path / "simple_index.json"
        
        if index_file.exists() and LANGCHAIN_AVAILABLE:
            try:
                indexer = EnhancedDocumentIndexer()
                self.embeddings = indexer._get_embeddings()
                if self.embeddings and hasattr(self.embeddings, 'embed_query'):
                    self.vector_store = FAISS.load_local(
                        str(self.index_path), 
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    logger.info("✅ FAISS index loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
        
        # Try simple index
        if simple_index_file.exists() and not self.vector_store:
            try:
                with open(simple_index_file, 'r') as f:
                    self.simple_index = json.load(f)
                
                # Recreate embeddings
                indexer = EnhancedDocumentIndexer()
                self.embeddings = indexer._get_embeddings()
                if hasattr(self.embeddings, 'fit'):
                    doc_texts = [doc['content'] for doc in self.simple_index['documents']]
                    self.embeddings.fit(doc_texts)
                
                logger.info("✅ Simple index loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load simple index: {e}")
    
    def retrieve_documents(self, query: str, top_k: int = 6) -> List[Dict]:
        """Retrieve relevant documents"""
        if self.vector_store:
            return self._retrieve_faiss(query, top_k)
        elif self.simple_index:
            return self._retrieve_simple(query, top_k)
        else:
            logger.warning("⚠️ No index available for retrieval")
            return []
    
    def _retrieve_faiss(self, query: str, top_k: int) -> List[Dict]:
        """Retrieve using FAISS"""
        try:
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k}
            )
            docs = retriever.get_relevant_documents(query)
            
            return [{
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": 0.8  # Default score
            } for doc in docs]
        except Exception as e:
            logger.error(f"FAISS retrieval failed: {e}")
            return []
    
    def _retrieve_simple(self, query: str, top_k: int) -> List[Dict]:
        """Retrieve using simple cosine similarity"""
        try:
            query_embedding = self.embeddings.embed_query(query)
            doc_embeddings = self.simple_index['embeddings']
            
            # Calculate cosine similarities
            similarities = []
            for i, doc_embedding in enumerate(doc_embeddings):
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                similarities.append((similarity, i))
            
            # Sort by similarity and get top_k
            similarities.sort(reverse=True)
            top_docs = []
            
            for sim_score, doc_idx in similarities[:top_k]:
                doc = self.simple_index['documents'][doc_idx]
                top_docs.append({
                    "content": doc['content'],
                    "metadata": doc['metadata'],
                    "score": sim_score
                })
            
            return top_docs
        except Exception as e:
            logger.error(f"Simple retrieval failed: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not a or not b or len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    async def optimize_prompt_stream(self, request: OptimizationRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream prompt optimization with real-time updates"""
        run_id = str(uuid.uuid4())
        
        # Yield initial status
        yield {
            "type": "status",
            "message": "🔍 Retrieving relevant context...",
            "run_id": run_id
        }
        
        # Retrieve documents
        retrieved_docs = self.retrieve_documents(request.original, top_k=6)
        
        yield {
            "type": "status", 
            "message": f"📚 Found {len(retrieved_docs)} relevant documents",
            "run_id": run_id
        }
        
        # Create citations
        citations = []
        for i, doc in enumerate(retrieved_docs[:3]):
            citations.append({
                "id": doc["metadata"].get("doc_id", f"doc_{i}"),
                "title": doc["metadata"].get("title", "Unknown"),
                "source": doc["metadata"].get("source", "unknown"),
                "score": doc.get("score", 0.0),
                "snippet": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
            })
        
        yield {
            "type": "citations",
            "citations": citations,
            "run_id": run_id
        }
        
        yield {
            "type": "status",
            "message": "🤖 Generating optimization...",
            "run_id": run_id
        }
        
        # Generate optimization (streaming simulation)
        context = "\n\n".join([
            f"Source: {doc['metadata'].get('title', 'Unknown')}\n{doc['content'][:500]}"
            for doc in retrieved_docs[:3]
        ])
        
        # Simulate streaming optimization
        optimized_parts = await self._generate_optimization_stream(request.original, context)
        
        full_optimized = ""
        for part in optimized_parts:
            full_optimized += part
            yield {
                "type": "optimization_chunk",
                "chunk": part,
                "full_text": full_optimized,
                "run_id": run_id
            }
            await asyncio.sleep(0.1)  # Simulate processing time
        
        # Generate improvements summary
        improvements = await self._generate_improvements(request.original, full_optimized, retrieved_docs)
        
        yield {
            "type": "improvements",
            "improvements": improvements,
            "run_id": run_id
        }
        
        # Final response
        usage = {
            "tokens_in": len(request.original.split()) * 2,
            "tokens_out": len(full_optimized.split()) * 2,
            "credits": 1 if request.mode == "fast" else 3
        }
        
        yield {
            "type": "complete",
            "optimized": full_optimized,
            "citations": citations,
            "improvements": improvements,
            "usage": usage,
            "run_id": run_id
        }
    
    async def _generate_optimization_stream(self, original: str, context: str) -> List[str]:
        """Generate optimization in chunks for streaming"""
        # Enhanced rule-based optimization
        optimized = original.strip()
        
        # Basic improvements
        if not optimized.endswith(('.', '!', '?')):
            optimized += "."
        
        # Add context-based improvements
        if context:
            if "template" in context.lower() and "specific" not in optimized.lower():
                optimized = optimized.replace(".", " with specific details.")
            
            if "example" in context.lower() and "example" not in optimized.lower():
                optimized += " Please provide examples."
            
            if "step" in context.lower() and "step" not in optimized.lower():
                optimized += " Break this down into steps."
        
        # Split optimized text into chunks for streaming
        words = optimized.split()
        chunk_size = max(1, len(words) // 5)  # 5 chunks
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if i + chunk_size < len(words):
                chunk += " "
            chunks.append(chunk)
        
        return chunks
    
    async def _generate_improvements(self, original: str, optimized: str, docs: List[Dict]) -> List[str]:
        """Generate list of improvements made"""
        improvements = []
        
        if len(optimized) > len(original):
            improvements.append("Enhanced with additional context")
        
        if "specific" in optimized.lower() and "specific" not in original.lower():
            improvements.append("Added specificity requirement")
        
        if "example" in optimized.lower() and "example" not in original.lower():
            improvements.append("Added request for examples")
        
        if "step" in optimized.lower() and "step" not in original.lower():
            improvements.append("Added step-by-step breakdown request")
        
        if optimized.endswith('.') and not original.endswith('.'):
            improvements.append("Added proper punctuation")
        
        if len(docs) > 0:
            improvements.append(f"Informed by {len(docs)} relevant documents")
        
        if not improvements:
            improvements.append("Prompt structure validated")
        
        return improvements

# Global instances for backward compatibility
def get_document_indexer():
    """Get enhanced document indexer instance"""
    return EnhancedDocumentIndexer()

def get_rag_agent():
    """Get streaming RAG agent instance"""
    return StreamingRAGAgent()

# Export enhanced classes
__all__ = [
    'EnhancedDocumentIndexer', 
    'StreamingRAGAgent', 
    'OptimizationRequest', 
    'OptimizationResponse',
    'get_document_indexer',
    'get_rag_agent'
]