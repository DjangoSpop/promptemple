"""
Enhanced Chat Consumer with RAG Agent Integration
Extends existing WebSocket protocol with agent.* events for streaming RAG optimization
"""

import json
import time
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

# Import existing services
from .deepseek_service import DeepSeekService
from .langchain_services import get_langchain_service
from .models import ChatMessage, UserIntent

# Import RAG services
from apps.ai_services.rag_service import get_rag_agent, OptimizationRequest
from apps.billing.models import UsageQuota, UserSubscription

logger = logging.getLogger(__name__)
User = get_user_model()


class EnhancedChatConsumer(AsyncWebsocketConsumer):
    """
    Enhanced WebSocket consumer that adds RAG agent capabilities
    while maintaining compatibility with existing chat protocol
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.user_id = None
        self.deepseek_service = DeepSeekService()
        self.langchain_service = get_langchain_service()
        self.rag_agent = get_rag_agent()
        self.heartbeat_task = None
        self.last_activity = time.time()
        self.active_agent_runs = {}  # Track running agent sessions
    
    async def connect(self):
        """Handle WebSocket connection with JWT auth support"""
        try:
            # Extract session_id from URL
            self.session_id = self.scope['url_route']['kwargs'].get('session_id', str(uuid.uuid4()))
            
            # Handle authentication
            await self._authenticate_ws_user()
            
            # Accept connection
            await self.accept()
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Send welcome message with RAG capabilities
            await self.send(text_data=json.dumps({
                'type': 'connection_ack',
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'user_id': str(self.user_id) if self.user_id else None,
                'authenticated': self.user is not None and not isinstance(self.user, AnonymousUser),
                'capabilities': {
                    'rag_agent': True,
                    'prompt_optimization': True,
                    'citations': True,
                    'streaming_optimization': True
                }
            }))
            
            logger.info(f"Enhanced Chat WebSocket connected: session={self.session_id}, user={self.user_id}")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Clean up on disconnect"""
        try:
            # Cancel any running agent tasks
            for run_id, task in self.active_agent_runs.items():
                if not task.done():
                    task.cancel()
                    
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                
            logger.info(f"Enhanced Chat WebSocket disconnected: session={self.session_id}, code={close_code}")
        except Exception as e:
            logger.error(f"Disconnect cleanup error: {e}")
    
    async def receive(self, text_data):
        """Handle incoming messages with RAG agent support"""
        start_time = time.time()
        self.last_activity = start_time
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Extended message handlers including RAG agent
            handlers = {
                # Existing handlers
                'chat_message': self.handle_chat_message,
                'optimize_prompt': self.handle_optimize_prompt,
                'intent_analysis': self.handle_intent_analysis,
                'ping': self.handle_ping,
                'pong': self.handle_pong,
                'slash_command': self.handle_slash_command,
                
                # New RAG agent handlers
                'agent_optimize': self.handle_agent_optimize,
                'agent_cancel': self.handle_agent_cancel,
                'agent_status': self.handle_agent_status
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data, start_time)
            else:
                await self._send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON message")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self._send_error("Message processing failed")
    
    async def handle_agent_optimize(self, data: Dict[str, Any], start_time: float):
        """Handle RAG agent optimization requests with streaming"""
        try:
            # Extract parameters
            original_prompt = data.get('original')
            mode = data.get('mode', 'fast')
            context = data.get('context', {})
            budget = data.get('budget', {})
            
            if not original_prompt:
                await self._send_error("Original prompt is required")
                return
            
            # Check user credits
            credits_needed = 1 if mode == 'fast' else 3
            if not await self._check_user_credits(credits_needed):
                await self.send(text_data=json.dumps({
                    'type': 'agent.error',
                    'run_id': None,
                    'code': 'insufficient_credits',
                    'message': f'Insufficient credits. Need {credits_needed} credits for {mode} mode.'
                }))
                return
            
            # Generate run ID
            run_id = str(uuid.uuid4())
            
            # Send agent.start event
            await self.send(text_data=json.dumps({
                'type': 'agent.start',
                'run_id': run_id,
                'session_id': self.session_id,
                'mode': mode,
                'budget': budget,
                'timestamp': datetime.now().isoformat()
            }))
            
            # Start optimization task
            task = asyncio.create_task(
                self._run_agent_optimization(run_id, original_prompt, mode, context, budget)
            )
            self.active_agent_runs[run_id] = task
            
        except Exception as e:
            logger.error(f"Agent optimize error: {e}")
            await self._send_error("Failed to start agent optimization")
    
    async def _run_agent_optimization(self, run_id: str, original: str, mode: str, context: Dict, budget: Dict):
        """Run the actual RAG optimization with streaming events"""
        try:
            # Send step event
            await self.send(text_data=json.dumps({
                'type': 'agent.step',
                'run_id': run_id,
                'tool': 'retriever',
                'note': 'Searching knowledge base for relevant context...'
            }))
            
            # Simulate some processing time for retrieval
            await asyncio.sleep(0.3)
            
            # Create optimization request
            opt_request = OptimizationRequest(
                session_id=self.session_id,
                original=original,
                mode=mode,
                context=context,
                budget=budget
            )
            
            # Send another step event
            await self.send(text_data=json.dumps({
                'type': 'agent.step',
                'run_id': run_id,
                'tool': 'optimizer',
                'note': 'Analyzing prompt and generating optimization...'
            }))
            
            # Run the optimization
            result = await self.rag_agent.optimize_prompt(opt_request)
            
            # Stream tokens if available
            optimized_content = result.optimized
            
            # Send streaming tokens
            words = optimized_content.split()
            for i, word in enumerate(words):
                if i % 3 == 0:  # Send every 3 words to simulate streaming
                    content_so_far = ' '.join(words[:i+3])
                    await self.send(text_data=json.dumps({
                        'type': 'agent.token',
                        'run_id': run_id,
                        'content': content_so_far
                    }))
                    await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send citations
            await self.send(text_data=json.dumps({
                'type': 'agent.citations',
                'run_id': run_id,
                'citations': [
                    {
                        'id': c.id,
                        'title': c.title,
                        'source': c.source,
                        'score': c.score,
                        'snippet': c.snippet
                    }
                    for c in result.citations
                ]
            }))
            
            # Consume credits
            credits_used = 1 if mode == 'fast' else 3
            await self._consume_user_credits(credits_used, result.usage["tokens_in"], result.usage["tokens_out"])
            
            # Send completion event
            await self.send(text_data=json.dumps({
                'type': 'agent.done',
                'run_id': run_id,
                'optimized': result.optimized,
                'diff_summary': result.diff_summary,
                'usage': result.usage,
                'processing_time_ms': int((time.time() - time.time()) * 1000)
            }))
            
        except asyncio.CancelledError:
            # Send cancellation event
            await self.send(text_data=json.dumps({
                'type': 'agent.error',
                'run_id': run_id,
                'code': 'cancelled',
                'message': 'Optimization was cancelled'
            }))
        except Exception as e:
            logger.error(f"Agent optimization error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'agent.error',
                'run_id': run_id,
                'code': 'optimization_failed',
                'message': 'Optimization failed due to an internal error'
            }))
        finally:
            # Clean up
            if run_id in self.active_agent_runs:
                del self.active_agent_runs[run_id]
    
    async def handle_agent_cancel(self, data: Dict[str, Any], start_time: float):
        """Cancel a running agent optimization"""
        run_id = data.get('run_id')
        if run_id and run_id in self.active_agent_runs:
            task = self.active_agent_runs[run_id]
            if not task.done():
                task.cancel()
                await self.send(text_data=json.dumps({
                    'type': 'agent.cancelled',
                    'run_id': run_id
                }))
    
    async def handle_agent_status(self, data: Dict[str, Any], start_time: float):
        """Get status of agent optimizations"""
        active_runs = [
            {
                'run_id': run_id,
                'status': 'running' if not task.done() else 'completed'
            }
            for run_id, task in self.active_agent_runs.items()
        ]
        
        await self.send(text_data=json.dumps({
            'type': 'agent.status',
            'active_runs': active_runs,
            'timestamp': datetime.now().isoformat()
        }))
    
    @database_sync_to_async
    def _check_user_credits(self, credits_needed: int) -> bool:
        """Check if user has sufficient credits"""
        if not self.user or isinstance(self.user, AnonymousUser):
            return credits_needed <= 1  # Allow 1 credit for anonymous users
        
        try:
            subscription = UserSubscription.objects.get(user=self.user)
            today = timezone.now().date()
            quota, created = UsageQuota.objects.get_or_create(
                user=self.user,
                quota_type='daily',
                quota_date=today,
                defaults={
                    'api_call_limit': subscription.plan.daily_template_limit + 10
                }
            )
            
            available = quota.api_call_limit - quota.api_calls_made
            return available >= credits_needed
            
        except UserSubscription.DoesNotExist:
            return credits_needed <= 3  # Trial limit
    
    @database_sync_to_async
    def _consume_user_credits(self, credits: int, tokens_in: int, tokens_out: int) -> bool:
        """Consume user credits"""
        if not self.user or isinstance(self.user, AnonymousUser):
            return True  # Don't track for anonymous users
        
        try:
            today = timezone.now().date()
            quota, created = UsageQuota.objects.get_or_create(
                user=self.user,
                quota_type='daily',
                quota_date=today,
                defaults={'api_call_limit': 50}
            )
            
            quota.api_calls_made += credits
            quota.save()
            return True
            
        except Exception as e:
            logger.error(f"Credit consumption failed: {e}")
            return False
    
    async def _authenticate_ws_user(self):
        """Authenticate WebSocket user"""
        # Use existing authentication logic from the original consumer
        self.user = self.scope.get("user", AnonymousUser())
        if hasattr(self.user, 'id'):
            self.user_id = self.user.id
        else:
            self.user_id = None
    
    # Include all existing methods from the original ChatConsumer
    async def handle_chat_message(self, data: Dict[str, Any], start_time: float):
        """Handle regular chat messages (existing functionality)"""
        # This would include the existing chat message handling logic
        pass
    
    async def handle_optimize_prompt(self, data: Dict[str, Any], start_time: float):
        """Handle prompt optimization (existing functionality)"""
        # This would include the existing optimization logic
        pass
    
    async def handle_intent_analysis(self, data: Dict[str, Any], start_time: float):
        """Handle intent analysis (existing functionality)"""
        # This would include the existing intent analysis logic
        pass
    
    async def handle_ping(self, data: Dict[str, Any], start_time: float):
        """Handle ping messages"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def handle_pong(self, data: Dict[str, Any], start_time: float):
        """Handle pong responses"""
        pass
    
    async def handle_slash_command(self, data: Dict[str, Any], start_time: float):
        """Handle slash commands (existing functionality)"""
        # This would include the existing slash command logic
        pass
    
    async def _send_error(self, message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        try:
            while True:
                await asyncio.sleep(20)  # 20 second intervals
                
                # Check if connection is still active
                if time.time() - self.last_activity > 300:  # 5 minutes timeout
                    logger.info(f"Connection timeout: {self.session_id}")
                    await self.close()
                    break
                
                # Send heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat(),
                    'session_id': self.session_id
                }))
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")