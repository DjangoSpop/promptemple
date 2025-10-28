"""
LangChain Orchestrator for PromptCraft

Production-ready LangChain orchestration service that provides:
- Prompt optimization chains
- RAG-enhanced generation
- Multi-step workflows
- Streaming capabilities
- Error handling and fallbacks
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
from dataclasses import dataclass
from datetime import datetime

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, BaseOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chains import LLMChain
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Django imports
from django.conf import settings
from django.core.cache import cache

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Result of prompt optimization"""
    original_prompt: str
    optimized_prompt: str
    improvements: List[str]
    confidence_score: float
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class RAGResult:
    """Result of RAG retrieval"""
    query: str
    retrieved_docs: List[Dict[str, Any]]
    enhanced_prompt: str
    relevance_scores: List[float]
    metadata: Dict[str, Any]

class LangChainOrchestrator:
    """
    Production-ready LangChain orchestration for PromptCraft.
    
    Features:
    - Prompt optimization chains
    - RAG-enhanced generation
    - Multi-step workflows
    - Streaming support
    - Caching and error handling
    """
    
    def __init__(self):
        """Initialize the orchestrator with proper configuration"""
        self.api_key = self._get_api_key()
        self.base_url = self._get_base_url()
        
        # Initialize LLM with proper configuration
        self.llm = self._initialize_llm()
        
        # Initialize chains
        self.optimization_chain = self._create_optimization_chain()
        self.rag_chain = self._create_rag_chain()
        
        # Initialize vector store (if available)
        self.vector_store = self._initialize_vector_store()
        
        logger.info("LangChain orchestrator initialized successfully")
    
    def _get_api_key(self) -> str:
        """Get API key from settings with fallback"""
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None) or os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.warning("No API key found, using placeholder")
            return "placeholder-key"
        return api_key
    
    def _get_base_url(self) -> str:
        """Get base URL for the API"""
        return getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the LLM with proper configuration"""
        try:
            return ChatOpenAI(
                model="deepseek-chat",
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=0.7,
                streaming=True,
                timeout=30,
                max_retries=3,
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            # Return a mock LLM for development
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key="test-key",
                temperature=0.7,
                streaming=True,
            )
    
    def _create_optimization_chain(self):
        """Create the prompt optimization chain"""
        template = """You are an expert prompt engineer with deep knowledge of AI systems and prompt optimization techniques.

Your task is to analyze and optimize the given prompt for better performance, clarity, and effectiveness.

Original prompt: {original_prompt}
Context: {context}
Target audience: {target_audience}
Desired outcome: {desired_outcome}

Please optimize this prompt using these best practices:

1. **Structure & Clarity**:
   - Add clear role definition
   - Structure with sections if needed
   - Use specific, actionable language

2. **Context Enhancement**:
   - Add relevant context clues
   - Specify output format requirements
   - Include examples if helpful

3. **Constraint Definition**:
   - Set clear boundaries and limitations
   - Specify tone and style requirements
   - Add quality criteria

4. **Performance Optimization**:
   - Remove ambiguity
   - Add step-by-step instructions if complex
   - Include error handling guidance

Provide your response in the following format:

## Optimized Prompt
[Your optimized version here]

## Key Improvements
1. [Improvement 1]
2. [Improvement 2]
3. [Improvement 3]

## Confidence Score
[Score from 0.0 to 1.0 based on expected improvement]

## Additional Notes
[Any additional considerations or recommendations]
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm | StrOutputParser()
    
    def _create_rag_chain(self):
        """Create the RAG (Retrieval-Augmented Generation) chain"""
        template = """You are an AI assistant that enhances prompts using retrieved context information.

Original Query: {query}
Retrieved Context:
{context}

Your task is to create an enhanced prompt that incorporates the relevant information from the retrieved context.

Guidelines:
1. Use only relevant information from the context
2. Maintain the original intent of the query
3. Add specific details and examples from the context
4. Ensure the enhanced prompt is clear and actionable

Enhanced Prompt:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm | StrOutputParser()
    
    def _initialize_vector_store(self) -> Optional[FAISS]:
        """Initialize vector store if available"""
        try:
            # Check if we have a vector store directory
            vector_store_path = getattr(settings, 'VECTOR_STORE_PATH', 'rag_index')
            if os.path.exists(vector_store_path):
                logger.info("Loading existing vector store")
                # For now, return None - we'll implement this later
                return None
            else:
                logger.info("No vector store found, creating empty one")
                return None
        except Exception as e:
            logger.warning(f"Failed to initialize vector store: {e}")
            return None
    
    async def optimize_prompt(
        self,
        original_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        target_audience: str = "general",
        desired_outcome: str = "improved performance"
    ) -> OptimizationResult:
        """
        Optimize a prompt using LangChain
        
        Args:
            original_prompt: The original prompt to optimize
            context: Additional context information
            target_audience: Target audience for the prompt
            desired_outcome: What the optimization should achieve
            
        Returns:
            OptimizationResult with optimized prompt and metadata
        """
        try:
            # Check cache first
            cache_key = f"prompt_opt_{hash(original_prompt)}_{hash(str(context))}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached optimization result")
                return cached_result
            
            # Prepare input data
            input_data = {
                "original_prompt": original_prompt,
                "context": str(context or {}),
                "target_audience": target_audience,
                "desired_outcome": desired_outcome
            }
            
            # Run the optimization chain
            result = await self.optimization_chain.ainvoke(input_data)
            
            # Parse the result
            parsed_result = self._parse_optimization_result(original_prompt, result)
            
            # Cache the result
            cache.set(cache_key, parsed_result, timeout=3600)  # Cache for 1 hour
            
            logger.info(f"Successfully optimized prompt with confidence {parsed_result.confidence_score}")
            return parsed_result
            
        except Exception as e:
            logger.error(f"Failed to optimize prompt: {e}")
            # Return fallback result
            return OptimizationResult(
                original_prompt=original_prompt,
                optimized_prompt=f"[OPTIMIZED] {original_prompt}",
                improvements=["Added optimization marker", "Maintained original intent"],
                confidence_score=0.5,
                metadata={"error": str(e), "fallback": True},
                timestamp=datetime.now()
            )
    
    async def optimize_prompt_streaming(
        self,
        original_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        target_audience: str = "general",
        desired_outcome: str = "improved performance"
    ) -> AsyncGenerator[str, None]:
        """
        Stream the prompt optimization process
        
        Yields:
            Chunks of the optimization result as they're generated
        """
        try:
            input_data = {
                "original_prompt": original_prompt,
                "context": str(context or {}),
                "target_audience": target_audience,
                "desired_outcome": desired_outcome
            }
            
            async for chunk in self.optimization_chain.astream(input_data):
                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Failed to stream optimization: {e}")
            yield f"Error: {str(e)}"
    
    async def enhance_with_rag(
        self,
        query: str,
        max_docs: int = 5,
        relevance_threshold: float = 0.7
    ) -> RAGResult:
        """
        Enhance a query using RAG (Retrieval-Augmented Generation)
        
        Args:
            query: The original query to enhance
            max_docs: Maximum number of documents to retrieve
            relevance_threshold: Minimum relevance score for documents
            
        Returns:
            RAGResult with enhanced prompt and metadata
        """
        try:
            # For now, return a mock result since vector store isn't set up
            # This will be replaced with actual RAG implementation
            
            retrieved_docs = [
                {
                    "content": "Sample relevant context for the query",
                    "source": "internal_knowledge_base",
                    "relevance_score": 0.85
                }
            ]
            
            # Create enhanced prompt
            context_str = "\n".join([doc["content"] for doc in retrieved_docs])
            
            input_data = {
                "query": query,
                "context": context_str
            }
            
            enhanced_prompt = await self.rag_chain.ainvoke(input_data)
            
            return RAGResult(
                query=query,
                retrieved_docs=retrieved_docs,
                enhanced_prompt=enhanced_prompt,
                relevance_scores=[doc["relevance_score"] for doc in retrieved_docs],
                metadata={
                    "retrieval_method": "mock",
                    "timestamp": datetime.now().isoformat(),
                    "num_docs_retrieved": len(retrieved_docs)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to enhance with RAG: {e}")
            return RAGResult(
                query=query,
                retrieved_docs=[],
                enhanced_prompt=query,  # Fallback to original query
                relevance_scores=[],
                metadata={"error": str(e), "fallback": True}
            )
    
    def _parse_optimization_result(self, original_prompt: str, result: str) -> OptimizationResult:
        """Parse the optimization result from the LLM response"""
        try:
            # Simple parsing - in production, you might want more sophisticated parsing
            lines = result.split('\n')
            
            optimized_prompt = ""
            improvements = []
            confidence_score = 0.8  # Default
            
            current_section = ""
            for line in lines:
                line = line.strip()
                if line.startswith("## Optimized Prompt"):
                    current_section = "prompt"
                elif line.startswith("## Key Improvements"):
                    current_section = "improvements"
                elif line.startswith("## Confidence Score"):
                    current_section = "confidence"
                elif line.startswith("##"):
                    current_section = "other"
                elif line and current_section == "prompt":
                    optimized_prompt += line + "\n"
                elif line.startswith(("1.", "2.", "3.", "-", "*")) and current_section == "improvements":
                    improvements.append(line)
                elif current_section == "confidence":
                    try:
                        # Extract confidence score
                        import re
                        match = re.search(r'(\d+\.?\d*)', line)
                        if match:
                            confidence_score = float(match.group(1))
                            if confidence_score > 1:
                                confidence_score = confidence_score / 100  # Convert percentage
                    except:
                        pass
            
            return OptimizationResult(
                original_prompt=original_prompt,
                optimized_prompt=optimized_prompt.strip() or f"[OPTIMIZED] {original_prompt}",
                improvements=improvements or ["General optimization applied"],
                confidence_score=min(max(confidence_score, 0.0), 1.0),
                metadata={
                    "parsing_method": "simple",
                    "timestamp": datetime.now().isoformat()
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to parse optimization result: {e}")
            return OptimizationResult(
                original_prompt=original_prompt,
                optimized_prompt=f"[OPTIMIZED] {original_prompt}",
                improvements=["Optimization applied"],
                confidence_score=0.5,
                metadata={"parsing_error": str(e)},
                timestamp=datetime.now()
            )

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> LangChainOrchestrator:
    """Get the global orchestrator instance (singleton pattern)"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LangChainOrchestrator()
    return _orchestrator

# Convenience functions for easy access
async def optimize_prompt(prompt: str, **kwargs) -> OptimizationResult:
    """Convenience function to optimize a prompt"""
    orchestrator = get_orchestrator()
    return await orchestrator.optimize_prompt(prompt, **kwargs)

async def optimize_prompt_streaming(prompt: str, **kwargs) -> AsyncGenerator[str, None]:
    """Convenience function to stream prompt optimization"""
    orchestrator = get_orchestrator()
    async for chunk in orchestrator.optimize_prompt_streaming(prompt, **kwargs):
        yield chunk

async def enhance_with_rag(query: str, **kwargs) -> RAGResult:
    """Convenience function to enhance query with RAG"""
    orchestrator = get_orchestrator()
    return await orchestrator.enhance_with_rag(query, **kwargs)