"""
High-performance WebSocket consumers for real-time prompt optimization chat
Optimized for sub-50ms response times with intelligent caching and streaming
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from .models import (
    UserIntent, ChatMessage, PromptLibrary, 
    PromptOptimization, PerformanceMetrics
)
from .search_services import search_service
from .langchain_services import langchain_service

# Import RAG streaming service
try:
    from apps.ai_services.rag_service_enhanced import StreamingRAGAgent
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False

# Import DeepSeek services
try:
    from .deepseek_service import get_deepseek_service, DeepSeekService
    from .deepseek_integration import create_deepseek_llm
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    DEEPSEEK_AVAILABLE = False
    
logger = logging.getLogger(__name__)
User = get_user_model()

class PromptChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time prompt optimization chat
    Handles intent processing, search, and AI-powered optimization
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.room_group_name = None
        self.optimization_service = langchain_service
        self.message_queue = []
        self.processing_lock = asyncio.Lock()
        
        # Initialize RAG streaming agent if available
        self.rag_agent = None
        if RAG_AVAILABLE:
            try:
                self.rag_agent = StreamingRAGAgent()
                logger.info("RAG streaming agent initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG agent: {e}")
                self.rag_agent = None
        
        # Initialize DeepSeek service if available
        self.deepseek_service = None
        if DEEPSEEK_AVAILABLE:
            try:
                self.deepseek_service = get_deepseek_service()
                if self.deepseek_service and self.deepseek_service.enabled:
                    logger.info("DeepSeek service initialized successfully")
                else:
                    logger.warning("DeepSeek service is disabled (no API key)")
            except Exception as e:
                logger.warning(f"Failed to initialize DeepSeek service: {e}")
                self.deepseek_service = None
    
    async def connect(self):
        """Handle WebSocket connection with performance tracking"""
        start_time = time.time()
        
        try:
            # Extract session info
            self.session_id = self.scope['url_route']['kwargs'].get('session_id')
            if not self.session_id:
                await self.close()
                return
            
            # Get user if authenticated
            if self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
            
            self.room_group_name = f'prompt_chat_{self.session_id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Build capabilities list
            capabilities = [
                'intent_processing',
                'prompt_search',
                'ai_optimization',
                'real_time_suggestions'
            ]
            
            # Add RAG capabilities if available
            if self.rag_agent:
                capabilities.extend([
                    'rag_optimization',
                    'streaming_optimization',
                    'context_aware_enhancement'
                ])
            
            # Add DeepSeek capabilities if available
            if self.deepseek_service and self.deepseek_service.enabled:
                capabilities.extend([
                    'deepseek_chat',
                    'deepseek_optimization',
                    'cost_effective_ai',
                    'code_generation',
                    'math_reasoning'
                ])
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'session_id': self.session_id,
                'timestamp': timezone.now().isoformat(),
                'capabilities': capabilities,
                'rag_enabled': self.rag_agent is not None,
                'deepseek_enabled': self.deepseek_service is not None and self.deepseek_service.enabled
            }))
            
            # Log performance
            elapsed_ms = int((time.time() - start_time) * 1000)
            await self._log_performance("websocket_connect", elapsed_ms, True)
            
            logger.info(f"WebSocket connected: session={self.session_id}, user={self.user}")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected: session={self.session_id}, code={close_code}")
    
    async def receive(self, text_data):
        """Process incoming WebSocket messages with intelligent routing"""
        start_time = time.time()
        
        try:
            # Parse message
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            # Validate message structure
            if not self._validate_message(data):
                await self._send_error("Invalid message format")
                return
            
            # Route message based on type
            handlers = {
                'user_intent': self.handle_user_intent,
                'search_request': self.handle_search_request,
                'optimize_prompt': self.handle_optimize_prompt,
                'get_suggestions': self.handle_get_suggestions,
                'rate_response': self.handle_rate_response,
                'message': self.handle_chat_message,
                'ping': self.handle_ping,
                # RAG streaming handlers
                'rag_optimize': self.handle_rag_optimization,
                'rag_stream_optimize': self.handle_rag_stream_optimization,
                # DeepSeek handlers
                'deepseek_chat': self.handle_deepseek_chat,
                'deepseek_optimize': self.handle_deepseek_optimization
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self._send_error(f"Unknown message type: {message_type}")
            
            # Track performance
            elapsed_ms = int((time.time() - start_time) * 1000)
            await self._log_performance(f"websocket_{message_type}", elapsed_ms, True)
            
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            await self._log_performance("websocket_error", elapsed_ms, False, str(e))
            await self._send_error("Internal server error")
    
    async def handle_user_intent(self, data: Dict[str, Any]):
        """Process user intent and provide initial prompt suggestions"""
        async with self.processing_lock:
            try:
                query = data.get('query', '').strip()
                if not query:
                    await self._send_error("Empty query provided")
                    return
                
                # Process intent with LangChain
                intent_data = await self._process_intent(query)
                
                # Save intent to database
                intent = await self._save_user_intent(query, intent_data)
                
                # Get initial prompt suggestions
                suggestions = await self._get_prompt_suggestions(intent)
                
                # Send response
                await self.send(text_data=json.dumps({
                    'type': 'intent_processed',
                    'intent_id': str(intent.id),
                    'intent_category': intent.intent_category,
                    'confidence_score': intent.confidence_score,
                    'suggestions': suggestions,
                    'processing_time_ms': intent.processing_time_ms,
                    'timestamp': timezone.now().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"Intent processing error: {e}")
                await self._send_error("Failed to process intent")
    
    async def handle_search_request(self, data: Dict[str, Any]):
        """Handle real-time prompt search with caching"""
        try:
            query = data.get('query', '').strip()
            category = data.get('category')
            max_results = min(data.get('max_results', 10), 50)  # Limit for performance
            
            if not query:
                await self._send_error("Search query required")
                return
            
            # Get user intent if available
            intent = None
            if data.get('intent_id'):
                intent = await self._get_user_intent(data['intent_id'])
            
            # Perform search
            start_search = time.time()
            results, metrics = await database_sync_to_async(search_service.search_prompts)(
                query=query,
                user_intent=intent,
                category=category,
                max_results=max_results,
                session_id=self.session_id
            )
            
            # Format results for WebSocket
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': str(result.prompt.id),
                    'title': result.prompt.title,
                    'content': result.prompt.content[:500],  # Truncate for performance
                    'category': result.prompt.category,
                    'tags': result.prompt.tags,
                    'score': round(result.score, 3),
                    'relevance_reason': result.relevance_reason,
                    'usage_count': result.prompt.usage_count,
                    'average_rating': result.prompt.average_rating
                })
            
            # Send results
            await self.send(text_data=json.dumps({
                'type': 'search_results',
                'query': query,
                'results': formatted_results,
                'total_results': len(formatted_results),
                'search_time_ms': metrics.get('total_time_ms', 0),
                'from_cache': metrics.get('from_cache', False),
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await self._send_error("Search failed")
    
    async def handle_optimize_prompt(self, data: Dict[str, Any]):
        """Handle AI-powered prompt optimization with optional RAG streaming"""
        try:
            prompt_id = data.get('prompt_id')
            user_context = data.get('context', {})
            optimization_type = data.get('optimization_type', 'enhancement')
            use_rag = data.get('use_rag', False)
            stream_mode = data.get('stream', False)
            
            # If RAG streaming is requested and available
            if use_rag and stream_mode and self.rag_agent:
                # Get the prompt content if prompt_id is provided
                if prompt_id:
                    original_prompt = await self._get_prompt_by_id(prompt_id)
                    if not original_prompt:
                        await self._send_error("Prompt not found")
                        return
                    prompt_content = original_prompt.content
                else:
                    prompt_content = data.get('prompt', '').strip()
                    if not prompt_content:
                        await self._send_error("Prompt content required")
                        return
                
                # Delegate to RAG streaming handler
                await self.handle_rag_stream_optimization({
                    'prompt': prompt_content,
                    'context': user_context
                })
                return
            
            # If non-streaming RAG is requested
            if use_rag and self.rag_agent:
                # Get the prompt content
                if prompt_id:
                    original_prompt = await self._get_prompt_by_id(prompt_id)
                    if not original_prompt:
                        await self._send_error("Prompt not found")
                        return
                    prompt_content = original_prompt.content
                else:
                    prompt_content = data.get('prompt', '').strip()
                    if not prompt_content:
                        await self._send_error("Prompt content required")
                        return
                
                # Delegate to RAG optimization handler
                await self.handle_rag_optimization({
                    'prompt': prompt_content,
                    'context': user_context
                })
                return
            
            # Fall back to original optimization logic
            if not prompt_id:
                await self._send_error("Prompt ID required for standard optimization")
                return
            
            # Get original prompt
            original_prompt = await self._get_prompt_by_id(prompt_id)
            if not original_prompt:
                await self._send_error("Prompt not found")
                return
            
            # Get user intent
            intent = None
            if data.get('intent_id'):
                intent = await self._get_user_intent(data['intent_id'])
            
            # Perform optimization using langchain service
            optimization_result = await self.optimization_service.optimize_prompt(
                original_prompt=original_prompt,
                user_intent=intent,
                context=user_context,
                optimization_type=optimization_type
            )
            
            # Save optimization
            optimization = await self._save_optimization(
                original_prompt, intent, optimization_result
            )
            
            # Send optimized result
            await self.send(text_data=json.dumps({
                'type': 'prompt_optimized',
                'optimization_id': str(optimization.id),
                'original_content': original_prompt.content,
                'optimized_content': optimization.optimized_content,
                'improvements': optimization.improvements,
                'relevance_score': optimization.relevance_score,
                'optimization_type': optimization_type,
                'processing_time_ms': optimization.processing_time_ms,
                'method': 'langchain',
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            await self._send_error("Prompt optimization failed")
    
    async def handle_get_suggestions(self, data: Dict[str, Any]):
        """Provide real-time suggestions based on user input"""
        try:
            partial_input = data.get('input', '').strip()
            intent_id = data.get('intent_id')
            
            if len(partial_input) < 3:  # Minimum length for suggestions
                return
            
            # Get cached suggestions first
            cache_key = f"suggestions:{self.session_id}:{hash(partial_input)}"
            cached_suggestions = cache.get(cache_key)
            
            if cached_suggestions:
                await self.send(text_data=json.dumps({
                    'type': 'suggestions',
                    'input': partial_input,
                    'suggestions': cached_suggestions,
                    'from_cache': True,
                    'timestamp': timezone.now().isoformat()
                }))
                return
            
            # Generate new suggestions
            intent = await self._get_user_intent(intent_id) if intent_id else None
            suggestions = await self._generate_suggestions(partial_input, intent)
            
            # Cache suggestions
            cache.set(cache_key, suggestions, 60)  # Cache for 1 minute
            
            await self.send(text_data=json.dumps({
                'type': 'suggestions',
                'input': partial_input,
                'suggestions': suggestions,
                'from_cache': False,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Suggestions error: {e}")
    
    async def handle_chat_message(self, data: Dict[str, Any]):
        """Handle general chat messages with context awareness"""
        try:
            content = data.get('content', '').strip()
            if not content:
                return
            
            # Save message
            message = await self._save_chat_message(
                content=content,
                message_type='user',
                intent_id=data.get('intent_id')
            )
            
            # Generate AI response
            ai_response = await self._generate_ai_response(content, data.get('intent_id'))
            
            # Save AI response
            ai_message = await self._save_chat_message(
                content=ai_response['content'],
                message_type='ai',
                intent_id=data.get('intent_id'),
                optimization_score=ai_response.get('confidence', 0.0)
            )
            
            # Send response
            await self.send(text_data=json.dumps({
                'type': 'chat_response',
                'user_message_id': str(message.id),
                'ai_message_id': str(ai_message.id),
                'response': ai_response['content'],
                'confidence': ai_response.get('confidence', 0.0),
                'suggestions': ai_response.get('suggestions', []),
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Chat message error: {e}")
            await self._send_error("Failed to process message")
    
    async def handle_rag_optimization(self, data: Dict[str, Any]):
        """Handle RAG-powered prompt optimization (non-streaming)"""
        try:
            if not self.rag_agent:
                await self._send_error("RAG optimization not available")
                return
            
            prompt = data.get('prompt', '').strip()
            if not prompt:
                await self._send_error("Prompt required for RAG optimization")
                return
            
            # Send processing status
            await self.send(text_data=json.dumps({
                'type': 'rag_processing_started',
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                'timestamp': timezone.now().isoformat()
            }))
            
            start_time = time.time()
            
            # Perform RAG optimization
            result = await self.rag_agent.optimize_prompt(prompt)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Send optimized result
            await self.send(text_data=json.dumps({
                'type': 'rag_optimized',
                'original_prompt': prompt,
                'optimized_prompt': result['optimized_prompt'],
                'improvements': result['improvements'],
                'confidence_score': result['confidence_score'],
                'processing_time_ms': processing_time,
                'sources_used': result.get('sources_used', []),
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"RAG optimization error: {e}")
            await self._send_error(f"RAG optimization failed: {str(e)}")
    
    async def handle_rag_stream_optimization(self, data: Dict[str, Any]):
        """Handle RAG-powered prompt optimization with streaming updates"""
        try:
            if not self.rag_agent:
                await self._send_error("RAG streaming not available")
                return
            
            prompt = data.get('prompt', '').strip()
            if not prompt:
                await self._send_error("Prompt required for streaming optimization")
                return
            
            # Send streaming start notification
            await self.send(text_data=json.dumps({
                'type': 'rag_stream_started',
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                'timestamp': timezone.now().isoformat()
            }))
            
            start_time = time.time()
            chunk_count = 0
            
            # Stream optimization updates
            async for chunk in self.rag_agent.optimize_prompt_stream(prompt):
                chunk_count += 1
                
                await self.send(text_data=json.dumps({
                    'type': 'rag_stream_chunk',
                    'chunk_index': chunk_count,
                    'chunk_type': chunk['type'],
                    'content': chunk['content'],
                    'metadata': chunk.get('metadata', {}),
                    'is_final': chunk.get('is_final', False),
                    'timestamp': timezone.now().isoformat()
                }))
                
                # Small delay to prevent overwhelming the WebSocket
                await asyncio.sleep(0.05)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Send completion notification
            await self.send(text_data=json.dumps({
                'type': 'rag_stream_completed',
                'total_chunks': chunk_count,
                'processing_time_ms': processing_time,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"RAG streaming error: {e}")
            await self._send_error(f"RAG streaming failed: {str(e)}")
    
    async def handle_ping(self, data: Dict[str, Any]):
        """Handle ping/pong for connection health"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_rate_response(self, data: Dict[str, Any]):
        """Handle user feedback on AI responses"""
        try:
            message_id = data.get('message_id')
            rating = data.get('rating')  # 1-5 scale
            
            if message_id and rating:
                await self._update_message_rating(message_id, rating)
                
                await self.send(text_data=json.dumps({
                    'type': 'rating_recorded',
                    'message_id': message_id,
                    'rating': rating,
                    'timestamp': timezone.now().isoformat()
                }))
        except Exception as e:
            logger.error(f"Rating error: {e}")
    
    async def handle_deepseek_chat(self, data: Dict[str, Any]):
        """Handle DeepSeek chat messages"""
        try:
            if not self.deepseek_service or not self.deepseek_service.enabled:
                await self._send_error("DeepSeek service not available")
                return
            
            messages = data.get('messages', [])
            model = data.get('model', 'deepseek-chat')
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 1000)
            
            if not messages:
                await self._send_error("Messages are required for DeepSeek chat")
                return
            
            # Send processing status
            await self.send(text_data=json.dumps({
                'type': 'deepseek_processing',
                'model': model,
                'timestamp': timezone.now().isoformat()
            }))
            
            start_time = time.time()
            
            # Process with DeepSeek
            response = await self.deepseek_service._make_request(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if response.success:
                # Save the conversation
                if len(messages) > 0:
                    user_message = messages[-1]['content']
                    await self._save_chat_message(
                        content=user_message,
                        message_type='user'
                    )
                
                ai_message = await self._save_chat_message(
                    content=response.content,
                    message_type='ai',
                    optimization_score=0.8  # Default good score for DeepSeek
                )
                
                # Send response
                await self.send(text_data=json.dumps({
                    'type': 'deepseek_response',
                    'message': {
                        'role': 'assistant',
                        'content': response.content
                    },
                    'message_id': str(ai_message.id),
                    'model': response.model,
                    'tokens_used': response.tokens_used,
                    'processing_time_ms': processing_time,
                    'cost_estimate': response.tokens_used * 0.0014 / 1000,
                    'provider': 'deepseek',
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                await self._send_error(f"DeepSeek chat failed: {response.error}")
                
        except Exception as e:
            logger.error(f"DeepSeek chat error: {e}")
            await self._send_error(f"DeepSeek chat error: {str(e)}")
    
    async def handle_deepseek_optimization(self, data: Dict[str, Any]):
        """Handle DeepSeek-powered prompt optimization"""
        try:
            if not self.deepseek_service or not self.deepseek_service.enabled:
                await self._send_error("DeepSeek service not available")
                return
            
            prompt = data.get('prompt', '').strip()
            optimization_type = data.get('optimization_type', 'enhancement')
            context = data.get('context', {})
            
            if not prompt:
                await self._send_error("Prompt is required for optimization")
                return
            
            # Send processing status
            await self.send(text_data=json.dumps({
                'type': 'deepseek_optimization_started',
                'prompt_preview': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                'optimization_type': optimization_type,
                'timestamp': timezone.now().isoformat()
            }))
            
            start_time = time.time()
            
            # Use DeepSeek for optimization
            result = await self.deepseek_service.optimize_prompt(
                original_prompt=prompt,
                user_intent=context.get('intent'),
                optimization_type=optimization_type
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Send optimized result
            await self.send(text_data=json.dumps({
                'type': 'deepseek_optimization_complete',
                'original_prompt': prompt,
                'optimized_prompt': result['optimized_content'],
                'improvements': result['improvements'],
                'confidence_score': result['confidence'],
                'processing_time_ms': processing_time,
                'tokens_used': result.get('tokens_used', 0),
                'cost_estimate': result.get('tokens_used', 0) * 0.0014 / 1000,
                'provider': 'deepseek',
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"DeepSeek optimization error: {e}")
            await self._send_error(f"DeepSeek optimization failed: {str(e)}")
    
    # Database operations (async wrappers)
    
    @database_sync_to_async
    def _get_user_intent(self, intent_id: str) -> Optional[UserIntent]:
        try:
            return UserIntent.objects.get(id=intent_id)
        except UserIntent.DoesNotExist:
            return None
    
    @database_sync_to_async
    def _get_prompt_by_id(self, prompt_id: str) -> Optional[PromptLibrary]:
        try:
            return PromptLibrary.objects.get(id=prompt_id)
        except PromptLibrary.DoesNotExist:
            return None
    
    @database_sync_to_async
    def _save_user_intent(self, query: str, intent_data: Dict) -> UserIntent:
        return UserIntent.objects.create(
            session_id=self.session_id,
            user=self.user,
            original_query=query,
            processed_intent=intent_data.get('processed_data', {}),
            intent_category=intent_data.get('category', 'general'),
            confidence_score=intent_data.get('confidence', 0.0),
            processing_time_ms=intent_data.get('processing_time_ms', 0)
        )
    
    @database_sync_to_async
    def _save_chat_message(
        self, 
        content: str, 
        message_type: str,
        intent_id: Optional[str] = None,
        optimization_score: float = 0.0
    ) -> ChatMessage:
        intent = None
        if intent_id:
            try:
                intent = UserIntent.objects.get(id=intent_id)
            except UserIntent.DoesNotExist:
                pass
        
        return ChatMessage.objects.create(
            session_id=self.session_id,
            user=self.user,
            intent=intent,
            message_type=message_type,
            content=content,
            optimization_score=optimization_score,
            delivered_at=timezone.now()
        )
    
    @database_sync_to_async
    def _save_optimization(
        self, 
        original_prompt: PromptLibrary, 
        intent: Optional[UserIntent], 
        optimization_result: Dict
    ) -> PromptOptimization:
        return PromptOptimization.objects.create(
            original_prompt=original_prompt,
            user_intent=intent,
            optimized_content=optimization_result['optimized_content'],
            optimization_type=optimization_result.get('type', 'enhancement'),
            improvements=optimization_result.get('improvements', []),
            similarity_score=optimization_result.get('similarity_score', 0.0),
            relevance_score=optimization_result.get('relevance_score', 0.0),
            model_used=optimization_result.get('model_used', ''),
            processing_time_ms=optimization_result.get('processing_time_ms', 0)
        )
    
    @database_sync_to_async
    def _log_performance(
        self, 
        operation_type: str, 
        response_time_ms: int, 
        success: bool, 
        error_message: str = ""
    ):
        try:
            PerformanceMetrics.objects.create(
                operation_type=operation_type,
                session_id=self.session_id,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                endpoint="websocket_consumer"
            )
        except Exception as e:
            logger.error(f"Failed to log performance: {e}")
    
    @database_sync_to_async
    def _update_message_rating(self, message_id: str, rating: int):
        try:
            ChatMessage.objects.filter(id=message_id).update(
                optimization_score=rating / 5.0  # Normalize to 0-1
            )
        except Exception as e:
            logger.error(f"Failed to update rating: {e}")
    
    # Utility methods
    
    async def _process_intent(self, query: str) -> Dict:
        """Process user intent using LangChain"""
        return await self.optimization_service.process_intent(query)
    
    async def _get_prompt_suggestions(self, intent: UserIntent) -> list:
        """Get initial prompt suggestions based on intent"""
        results = await database_sync_to_async(search_service.search_by_intent)(
            intent_category=intent.intent_category,
            max_results=5
        )
        
        return [{
            'id': str(r.prompt.id),
            'title': r.prompt.title,
            'content': r.prompt.content[:200],  # Preview
            'score': round(r.score, 3)
        } for r in results]
    
    async def _generate_suggestions(self, partial_input: str, intent: Optional[UserIntent]) -> list:
        """Generate real-time suggestions"""
        # Use quick keyword-based suggestions for speed
        suggestions = []
        
        if intent and intent.intent_category:
            results = await database_sync_to_async(search_service.search_by_intent)(
                intent_category=intent.intent_category,
                max_results=3
            )
            suggestions.extend([r.prompt.title for r in results])
        
        # Add common completions
        common_completions = await self._get_common_completions(partial_input)
        suggestions.extend(common_completions)
        
        return list(set(suggestions))[:5]  # Remove duplicates and limit
    
    async def _get_common_completions(self, partial_input: str) -> list:
        """Get common completions from cache or database"""
        # This would typically use a trie or similar structure for efficiency
        cache_key = f"completions:{partial_input.lower()[:20]}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        # Simple implementation - in production, use more sophisticated matching
        completions = [
            "Write a professional email about",
            "Create a marketing copy for",
            "Generate a technical document for",
            "Draft a proposal for",
            "Summarize the key points of"
        ]
        
        filtered = [c for c in completions if partial_input.lower() in c.lower()]
        cache.set(cache_key, filtered, 300)  # Cache for 5 minutes
        
        return filtered
    
    async def _generate_ai_response(self, content: str, intent_id: Optional[str]) -> Dict:
        """Generate AI response to user message"""
        intent = await self._get_user_intent(intent_id) if intent_id else None
        return await self.optimization_service.generate_response(content, intent)
    
    def _validate_message(self, data: Dict) -> bool:
        """Validate incoming message structure"""
        return isinstance(data, dict) and 'type' in data
    
    async def _send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }))


# Import Socket.IO compatibility consumer
try:
    from .socketio_consumer import SocketIOCompatibilityConsumer
except ImportError:
    # Fallback if channels is not installed
    class SocketIOCompatibilityConsumer:
        @classmethod
        def as_asgi(cls):
            return None