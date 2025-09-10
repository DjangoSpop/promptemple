"""
LangChain integration for intent processing and prompt optimization
Optimized for high performance with caching and efficient model usage
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# LangChain imports - with comprehensive fallbacks and error handling
ChatOpenAI = None
OpenAI = None
PromptTemplate = None
ChatPromptTemplate = None
LLMChain = None
HumanMessage = None
SystemMessage = None
ConversationBufferWindowMemory = None

# Import DeepSeek integration
try:
    from .deepseek_integration import create_deepseek_llm, DeepSeekLangChainWrapper
    DEEPSEEK_AVAILABLE = True
    logger.info("DeepSeek integration loaded successfully")
except ImportError as e:
    DEEPSEEK_AVAILABLE = False
    create_deepseek_llm = None
    DeepSeekLangChainWrapper = None
    logger.warning(f"DeepSeek integration not available: {e}")

# Suppress pydantic warnings that cause conflicts
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Enable LangChain with modern split package architecture (Pydantic 2.11.7 + LangChain 0.3.27 compatible)
try:
    # Try newer langchain versions with direct imports (recommended approach)
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
    logger.info("LangChain new version loaded (langchain-openai)")
except ImportError:
    try:
        # Fallback to community versions
        from langchain_community.chat_models import ChatOpenAI
        from langchain.prompts import PromptTemplate, ChatPromptTemplate
        from langchain.schema import HumanMessage, SystemMessage
        LANGCHAIN_AVAILABLE = True
        logger.info("LangChain community version loaded")
    except (ImportError, Exception) as e:
        try:
            # Last resort - basic langchain
            from langchain.chat_models import ChatOpenAI
            from langchain.prompts import PromptTemplate, ChatPromptTemplate
            from langchain.schema import HumanMessage, SystemMessage
            LANGCHAIN_AVAILABLE = True
            logger.info("LangChain legacy version loaded")
        except (ImportError, Exception):
            LANGCHAIN_AVAILABLE = False
            logger.warning("LangChain not available - using fallback implementations")

from .models import UserIntent, PromptLibrary

# Import DeepSeek service and mock service as fallbacks
try:
    from .deepseek_service import DeepSeekService, get_deepseek_service
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DeepSeekService = None
    get_deepseek_service = None
    DEEPSEEK_AVAILABLE = False

try:
    from .mock_langchain import MockLangChainOptimizationService
except ImportError:
    MockLangChainOptimizationService = None

@dataclass
class OptimizationResult:
    """Result structure for prompt optimization"""
    optimized_content: str
    improvements: List[str]
    similarity_score: float
    relevance_score: float
    processing_time_ms: int
    model_used: str
    confidence: float

class LangChainOptimizationService:
    """High-performance LangChain service for intent processing and optimization"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.deepseek_service = None
        self._initialize_services()
        # Initialize memory only if ConversationBufferWindowMemory is available
        if ConversationBufferWindowMemory:
            self.memory = ConversationBufferWindowMemory(k=5)  # Keep last 5 exchanges
        else:
            self.memory = None
        
    def _initialize_services(self):
        """Initialize AI services (DeepSeek preferred, OpenAI fallback)"""
        # Try DeepSeek first (cost-effective and powerful)
        if DEEPSEEK_AVAILABLE:
            try:
                self.deepseek_service = get_deepseek_service()
                if self.deepseek_service:
                    logger.info("DeepSeek service initialized successfully - using as primary AI provider")
                    self.intent_model = self.optimization_model = self.chat_model = "deepseek"
                    return
            except Exception as e:
                logger.warning(f"DeepSeek initialization failed: {e}, trying OpenAI fallback")
        
        # Fallback to OpenAI/LangChain if DeepSeek not available
        if LANGCHAIN_AVAILABLE and ChatOpenAI:
            try:
                openai_key = os.environ.get('OPENAI_API_KEY')
                if openai_key:
                    self.intent_model = ChatOpenAI(
                        model="gpt-3.5-turbo",
                        temperature=0.1,
                        max_tokens=200,
                        timeout=10,
                        api_key=openai_key
                    )
                    self.optimization_model = ChatOpenAI(
                        model="gpt-4",
                        temperature=0.3,
                        max_tokens=1000,
                        timeout=30,
                        api_key=openai_key
                    )
                    self.chat_model = ChatOpenAI(
                        model="gpt-3.5-turbo",
                        temperature=0.7,
                        max_tokens=500,
                        timeout=15,
                        api_key=openai_key
                    )
                    logger.info("OpenAI LangChain models initialized as fallback")
                    return
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI models: {e}")
        
        # No AI services available
        logger.warning("No AI services available - using mock implementations")
        self.intent_model = self.optimization_model = self.chat_model = None
    
    async def process_intent(self, query: str) -> Dict[str, Any]:
        """Process user intent with caching for performance"""
        start_time = time.time()
        
        # Check cache first
        cache_key = f"intent:{hash(query.lower())}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Use DeepSeek if available
            if self.deepseek_service:
                result = await self.deepseek_service.process_intent(query)
                
                # Cache for 1 hour
                cache.set(cache_key, result, 3600)
                return result
            
            # Fallback to OpenAI/LangChain
            elif self.intent_model and self.intent_model != "deepseek":
                # OpenAI LangChain approach
                if ChatPromptTemplate and SystemMessage and HumanMessage:
                    intent_prompt = ChatPromptTemplate.from_messages([
                        SystemMessage(content="""You are an expert at understanding user intent for prompt engineering.
                        Analyze the user's query and classify it into one of these categories:
                        - content_creation: Writing articles, stories, marketing copy
                        - technical_writing: Documentation, tutorials, technical specs  
                        - communication: Emails, messages, formal letters
                        - analysis: Data analysis, research, summarization
                        - creative: Brainstorming, ideation, creative writing
                        - coding: Programming, code review, technical solutions
                        - business: Proposals, reports, presentations
                        - education: Teaching materials, explanations, learning
                        - general: Other or unclear intent
                        
                        Respond with JSON format:
                        {
                            "category": "category_name",
                            "confidence": 0.95,
                            "keywords": ["key1", "key2"],
                            "context": "brief explanation",
                            "suggested_approach": "optimization strategy"
                        }"""),
                        HumanMessage(content=f"Query: {query}")
                    ])
                else:
                    # Fallback prompt structure
                    intent_prompt = {
                        "system_message": """You are an expert at understanding user intent for prompt engineering.
                        Classify the query and respond with JSON format.""",
                        "human_message": f"Query: {query}"
                    }
                
                # Run intent classification
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    self.executor,
                    self._run_intent_classification,
                    intent_prompt,
                    query
                )
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                result = {
                    "processed_data": response,
                    "category": response.get("category", "general"),
                    "confidence": response.get("confidence", 0.5),
                    "keywords": response.get("keywords", []),
                    "context": response.get("context", ""),
                    "processing_time_ms": processing_time_ms
                }
                
                # Cache for 1 hour
                cache.set(cache_key, result, 3600)
                return result
            
            else:
                # Ultimate fallback - simple keyword matching
                return self._simple_intent_classification(query, start_time)
                
        except Exception as e:
            logger.error(f"Intent processing error: {e}")
            return self._simple_intent_classification(query, start_time, str(e))
    
    def _run_intent_classification(self, prompt, query: str) -> Dict:
        """Synchronous intent classification"""
        try:
            if not self.intent_model:
                return {"category": "general", "confidence": 0.1}
            
            if hasattr(prompt, 'format_messages'):
                # New ChatPromptTemplate style
                response = self.intent_model.invoke(prompt.format_messages())
            else:
                # Fallback for dictionary-style prompts
                system_msg = prompt.get("system_message", "Classify this query.")
                user_msg = prompt.get("human_message", "").format(query=query)
                
                if SystemMessage and HumanMessage:
                    messages = [SystemMessage(content=system_msg), HumanMessage(content=user_msg)]
                    response = self.intent_model.invoke(messages)
                else:
                    # Ultimate fallback
                    response = self.intent_model.invoke(f"{system_msg}\n\nUser: {user_msg}")
            
            # Parse JSON response
            try:
                if hasattr(response, 'content'):
                    return json.loads(response.content)
                else:
                    return json.loads(str(response))
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_fallback_intent(str(response), query)
                
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {"category": "general", "confidence": 0.1}
    
    async def optimize_prompt(
        self,
        original_prompt: PromptLibrary,
        user_intent: Optional[UserIntent] = None,
        context: Dict = None,
        optimization_type: str = "enhancement"
    ) -> OptimizationResult:
        """Optimize a prompt using AI with context awareness"""
        start_time = time.time()
        
        try:
            # Use DeepSeek if available
            if self.deepseek_service:
                # Convert to format expected by DeepSeek service
                prompt_text = original_prompt.content
                intent_data = None
                if user_intent:
                    intent_data = {
                        "category": user_intent.category,
                        "confidence": user_intent.confidence,
                        "keywords": getattr(user_intent, 'keywords', []),
                        "context": user_intent.description or ""
                    }
                
                result = await self.deepseek_service.optimize_prompt(prompt_text, intent_data)
                
                # Convert DeepSeek result to OptimizationResult format
                return OptimizationResult(
                    optimized_content=result.get("optimized_prompt", prompt_text),
                    improvements=result.get("improvements", []),
                    similarity_score=result.get("similarity_score", 0.8),
                    relevance_score=result.get("effectiveness_score", 0.8),
                    processing_time_ms=result.get("processing_time_ms", 
                                                  int((time.time() - start_time) * 1000)),
                    model_used="deepseek-chat",
                    confidence=result.get("confidence", 0.8)
                )
            
            # Fallback to OpenAI/LangChain if DeepSeek unavailable
            else:
                # Build optimization context
                optimization_context = self._build_optimization_context(
                    original_prompt, user_intent, context, optimization_type
                )
                
                # Create optimization prompt
                optimization_prompt = self._create_optimization_prompt(
                    optimization_context, optimization_type
                )
                
                # Run optimization
                loop = asyncio.get_event_loop()
                optimized_result = await loop.run_in_executor(
                    self.executor,
                    self._run_optimization,
                    optimization_prompt,
                    original_prompt.content
                )
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Calculate similarity and relevance scores
                similarity_score = await self._calculate_similarity(
                    original_prompt.content, 
                    optimized_result.get("optimized_content", "")
                )
                
                relevance_score = await self._calculate_relevance(
                    optimized_result.get("optimized_content", ""),
                    user_intent
                )
                
                return OptimizationResult(
                    optimized_content=optimized_result.get("optimized_content", ""),
                    improvements=optimized_result.get("improvements", []),
                    similarity_score=similarity_score,
                    relevance_score=relevance_score,
                    processing_time_ms=processing_time_ms,
                    model_used="gpt-4",
                    confidence=optimized_result.get("confidence", 0.8)
                )
            
        except Exception as e:
            logger.error(f"Prompt optimization error: {e}")
            return OptimizationResult(
                optimized_content=original_prompt.content,
                improvements=["Error during optimization"],
                similarity_score=1.0,
                relevance_score=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                model_used="error",
                confidence=0.0
            )
    
    def _build_optimization_context(
        self,
        original_prompt: PromptLibrary,
        user_intent: Optional[UserIntent],
        context: Dict,
        optimization_type: str
    ) -> Dict:
        """Build comprehensive context for optimization"""
        return {
            "original_prompt": {
                "content": original_prompt.content,
                "category": original_prompt.category,
                "tags": original_prompt.tags,
                "usage_count": original_prompt.usage_count,
                "success_rate": original_prompt.success_rate,
                "complexity_score": original_prompt.complexity_score
            },
            "user_intent": {
                "category": user_intent.intent_category if user_intent else "general",
                "confidence": user_intent.confidence_score if user_intent else 0.5,
                "original_query": user_intent.original_query if user_intent else "",
                "context_data": user_intent.context_data if user_intent else {}
            },
            "optimization_type": optimization_type,
            "additional_context": context or {},
            "performance_targets": {
                "clarity": True,
                "conciseness": True,
                "actionability": True,
                "engagement": True
            }
        }
    
    def _create_optimization_prompt(self, context: Dict, optimization_type: str):
        """Create specialized optimization prompt based on type"""
        
        if not ChatPromptTemplate:
            # Return a simple fallback structure
            return {
                "system_message": "You are an expert prompt engineer.",
                "human_message": "Original Prompt: {original_prompt}"
            }
        
        base_system_message = """You are an expert prompt engineer specializing in optimization.
        Your task is to improve prompts while maintaining their core intent and effectiveness.
        
        Guidelines:
        - Maintain the original intent and purpose
        - Improve clarity and specificity
        - Enhance actionability and outcomes
        - Consider the user's context and intent
        - Provide specific, measurable improvements
        
        Context: {context}
        Optimization Type: {optimization_type}
        
        Respond with JSON:
        {{
            "optimized_content": "improved prompt content",
            "improvements": ["specific improvement 1", "improvement 2"],
            "rationale": "explanation of changes",
            "confidence": 0.85
        }}"""
        
        try:
            return ChatPromptTemplate.from_messages([
                SystemMessage(content=base_system_message),
                HumanMessage(content="Original Prompt: {original_prompt}")
            ])
        except Exception:
            # Fallback if ChatPromptTemplate creation fails
            return {
                "system_message": base_system_message,
                "human_message": "Original Prompt: {original_prompt}"
            }
    
    def _run_optimization(self, prompt, original_content: str) -> Dict:
        """Synchronous optimization execution"""
        try:
            if not self.optimization_model:
                return {"optimized_content": original_content, "improvements": [], "confidence": 0.1}
            
            # Format the prompt with context
            formatted_prompt = prompt.format_messages(
                original_prompt=original_content
            )
            
            response = self.optimization_model(formatted_prompt)
            
            # Parse JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return self._parse_fallback_optimization(response.content, original_content)
                
        except Exception as e:
            logger.error(f"Optimization execution error: {e}")
            return {
                "optimized_content": original_content,
                "improvements": [f"Error: {str(e)}"],
                "confidence": 0.0
            }
    
    async def generate_response(self, user_message: str, user_intent: Optional[UserIntent] = None) -> Dict:
        """Generate conversational AI response with context"""
        start_time = time.time()
        
        try:
            # Build conversation context
            context = self._build_conversation_context(user_message, user_intent)
            
            # Create response prompt
            response_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a helpful AI assistant specializing in prompt engineering and optimization.
                You help users refine their prompts and provide guidance on creating effective AI interactions.
                
                Be concise, helpful, and actionable in your responses.
                If the user is asking about prompts, provide specific suggestions.
                
                Context: {context}"""),
                HumanMessage(content=user_message)
            ])
            
            # Generate response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._run_response_generation,
                response_prompt,
                context
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Generate suggestions
            suggestions = await self._generate_contextual_suggestions(user_message, user_intent)
            
            return {
                "content": response.get("content", "I'm sorry, I couldn't generate a response."),
                "confidence": response.get("confidence", 0.8),
                "suggestions": suggestions,
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {
                "content": "I'm experiencing technical difficulties. Please try again.",
                "confidence": 0.0,
                "suggestions": [],
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def _build_conversation_context(self, user_message: str, user_intent: Optional[UserIntent]) -> Dict:
        """Build context for conversation"""
        return {
            "user_intent": {
                "category": user_intent.intent_category if user_intent else "general",
                "original_query": user_intent.original_query if user_intent else "",
                "confidence": user_intent.confidence_score if user_intent else 0.5
            },
            "conversation_stage": "interactive",
            "user_message": user_message
        }
    
    def _run_response_generation(self, prompt, context: Dict) -> Dict:
        """Synchronous response generation"""
        try:
            if not self.chat_model:
                return {"content": "Chat model not available", "confidence": 0.1}
            
            formatted_prompt = prompt.format_messages(context=json.dumps(context, indent=2))
            response = self.chat_model(formatted_prompt)
            
            return {
                "content": response.content,
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
        return {
            "content": f"Error generating response: {str(e)}",
            "confidence": 0.0
        }
    
    def _simple_intent_classification(self, query: str, start_time: float, error: str = None) -> Dict[str, Any]:
        """Simple fallback intent classification using keyword matching"""
        query_lower = query.lower()
        
        # Simple keyword-based classification
        if any(word in query_lower for word in ['write', 'create', 'generate', 'compose']):
            category = 'content_creation'
        elif any(word in query_lower for word in ['code', 'program', 'debug', 'function']):
            category = 'coding'
        elif any(word in query_lower for word in ['analyze', 'research', 'study', 'examine']):
            category = 'analysis'
        elif any(word in query_lower for word in ['email', 'letter', 'message', 'communication']):
            category = 'communication'
        elif any(word in query_lower for word in ['business', 'proposal', 'report', 'presentation']):
            category = 'business'
        elif any(word in query_lower for word in ['creative', 'brainstorm', 'idea', 'innovative']):
            category = 'creative'
        elif any(word in query_lower for word in ['teach', 'explain', 'tutorial', 'learn']):
            category = 'education'
        elif any(word in query_lower for word in ['document', 'technical', 'specification']):
            category = 'technical_writing'
        else:
            category = 'general'
        
        keywords = [word for word in query_lower.split() if len(word) > 3][:5]
        
        return {
            "processed_data": {
                "category": category,
                "confidence": 0.6,
                "keywords": keywords,
                "context": f"Simple classification{' (error: ' + error + ')' if error else ''}",
                "suggested_approach": f"Basic {category} optimization"
            },
            "category": category,
            "confidence": 0.6,
            "keywords": keywords,
            "context": f"Simple classification{' (error: ' + error + ')' if error else ''}",
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
    
    def _simple_prompt_optimization(self, prompt: str, start_time: float, error: str = None) -> Dict[str, Any]:
        """Simple fallback prompt optimization"""
        # Basic optimization suggestions
        improvements = []
        optimized = prompt
        
        # Check for basic improvements
        if not prompt.strip().endswith(('?', '.', '!')):
            improvements.append("Add clear punctuation to end the prompt")
            optimized = prompt.strip() + "."
        
        if len(prompt.split()) < 5:
            improvements.append("Consider adding more specific details")
        
        if prompt.isupper():
            improvements.append("Use normal capitalization instead of all caps")
            optimized = prompt.capitalize()
        
        if not improvements:
            improvements.append("Prompt appears well-formed")
        
        return {
            "original_prompt": prompt,
            "optimized_prompt": optimized,
            "improvements": improvements,
            "clarity_score": 0.7,
            "specificity_score": 0.6,
            "effectiveness_score": 0.6,
            "suggestions": improvements,
            "intent_category": "general",
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "note": f"Fallback optimization{' (error: ' + error + ')' if error else ''}"
        }

def get_langchain_service():
    """Factory function to get the appropriate LangChain service"""
    if LANGCHAIN_AVAILABLE and MockLangChainOptimizationService:
        try:
            # Try to create a real service first
            service = LangChainOptimizationService()
            if service.intent_model is not None:
                logger.info("Using real LangChain service")
                return service
            else:
                logger.info("LangChain models not available, using mock service")
                return MockLangChainOptimizationService()
        except Exception as e:
            logger.warning(f"Failed to initialize real LangChain service: {e}, using mock")
            return MockLangChainOptimizationService()
    elif MockLangChainOptimizationService:
        logger.info("Using mock LangChain service")
        return MockLangChainOptimizationService()
    else:
        logger.error("No LangChain service available")
        return None

# Create a global service instance
try:
    langchain_service = get_langchain_service()
except Exception as e:
    logger.error(f"Failed to initialize any LangChain service: {e}")
    langchain_service = None