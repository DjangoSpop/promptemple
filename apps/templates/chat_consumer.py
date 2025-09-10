"""
Chat WebSocket Consumer for Next.js Frontend Integration
Handles real-time chat with DeepSeek AI integration matching frontend protocol
"""

import json
import time
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone as django_timezone
from django.contrib.auth.models import AnonymousUser

from .deepseek_service import DeepSeekService
from .langchain_services import get_langchain_service
from .models import ChatMessage, UserIntent

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for Next.js chat frontend
    Matches the WsInbound/WsOutbound protocol from your frontend
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.user_id = None
        self.deepseek_service = DeepSeekService()
        self.langchain_service = get_langchain_service()
        self.heartbeat_task = None
        self.last_activity = time.time()
    
    async def connect(self):
        """Handle WebSocket connection with JWT auth support"""
        try:
            # Extract session_id from URL
            self.session_id = self.scope['url_route']['kwargs'].get('session_id', str(uuid.uuid4()))
            
            # Handle authentication
            await self._authenticate_user()
            
            # Accept connection
            await self.accept()
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection_ack',
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'user_id': str(self.user_id) if self.user_id else None,
                'authenticated': self.user is not None and not isinstance(self.user, AnonymousUser)
            }))
            
            logger.info(f"Chat WebSocket connected: session={self.session_id}, user={self.user_id}")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Clean up on disconnect"""
        try:
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            logger.info(f"Chat WebSocket disconnected: session={self.session_id}, code={close_code}")
        except Exception as e:
            logger.error(f"Disconnect cleanup error: {e}")
    
    async def receive(self, text_data):
        """Handle incoming messages matching frontend protocol"""
        start_time = time.time()
        self.last_activity = start_time
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route messages based on type
            handlers = {
                'chat_message': self.handle_chat_message,
                'optimize_prompt': self.handle_optimize_prompt,
                'intent_analysis': self.handle_intent_analysis,
                'ping': self.handle_ping,
                'pong': self.handle_pong,
                'slash_command': self.handle_slash_command
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data, start_time)
            else:
                await self._send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self._send_error("Internal server error")
    
    async def handle_chat_message(self, data: Dict[str, Any], start_time: float):
        """Handle regular chat messages with AI processing"""
        try:
            content = data.get('content', '').strip()
            message_id = data.get('message_id', str(uuid.uuid4()))
            
            if not content:
                await self._send_error("Message content required")
                return
            
            # Save user message
            user_message = await self._save_message(
                message_id=message_id,
                content=content,
                role='user',
                session_id=self.session_id
            )
            
            # Echo user message back
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message_id': message_id,
                'content': content,
                'role': 'user',
                'timestamp': user_message.get('timestamp'),
                'session_id': self.session_id
            }))
            
            # Process with AI
            await self._process_ai_response(content, start_time)
            
        except Exception as e:
            logger.error(f"Chat message error: {e}")
            await self._send_error("Failed to process message")
    
    async def handle_optimize_prompt(self, data: Dict[str, Any], start_time: float):
        """Handle prompt optimization requests"""
        try:
            prompt = data.get('prompt', '').strip()
            context = data.get('context', {})
            optimization_type = data.get('optimization_type', 'enhancement')
            
            if not prompt:
                await self._send_error("Prompt required for optimization")
                return
            
            # Send typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_start',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Process optimization
            if self.deepseek_service and self.deepseek_service.enabled:
                result = await self.deepseek_service.optimize_prompt(prompt, context)
            elif self.langchain_service:
                # Fallback to LangChain service
                intent_data = context if context else await self.langchain_service.process_intent(prompt)
                result = {
                    'optimized_prompt': f"Enhanced: {prompt}",
                    'improvements': ['Added clarity', 'Improved structure'],
                    'confidence': 0.8,
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
            else:
                result = {'error': 'No optimization service available'}
            
            # Stop typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_stop',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Send optimization result
            response_id = str(uuid.uuid4())
            await self.send(text_data=json.dumps({
                'type': 'optimization_result',
                'message_id': response_id,
                'original_prompt': prompt,
                'optimized_prompt': result.get('optimized_prompt', prompt),
                'improvements': result.get('improvements', []),
                'suggestions': result.get('suggestions', []),
                'confidence': result.get('confidence', 0.5),
                'processing_time_ms': result.get('processing_time_ms', 0),
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            }))
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            await self._send_error("Failed to optimize prompt")
    
    async def handle_intent_analysis(self, data: Dict[str, Any], start_time: float):
        """Handle intent analysis requests"""
        try:
            query = data.get('query', '').strip()
            
            if not query:
                await self._send_error("Query required for intent analysis")
                return
            
            # Process intent
            if self.deepseek_service and self.deepseek_service.enabled:
                result = await self.deepseek_service.process_intent(query)
            elif self.langchain_service:
                result = await self.langchain_service.process_intent(query)
            else:
                result = {
                    'category': 'general',
                    'confidence': 0.5,
                    'keywords': [],
                    'context': 'No analysis service available'
                }
            
            # Send intent analysis
            await self.send(text_data=json.dumps({
                'type': 'intent_result',
                'query': query,
                'category': result.get('category', 'general'),
                'confidence': result.get('confidence', 0.5),
                'keywords': result.get('keywords', []),
                'context': result.get('context', ''),
                'suggestions': result.get('suggestions', []),
                'processing_time_ms': result.get('processing_time_ms', 0),
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            }))
            
        except Exception as e:
            logger.error(f"Intent analysis error: {e}")
            await self._send_error("Failed to analyze intent")
    
    async def handle_slash_command(self, data: Dict[str, Any], start_time: float):
        """Handle slash commands from frontend"""
        try:
            command = data.get('command', '').strip()
            content = data.get('content', '').strip()
            
            commands = {
                'intent': self._handle_intent_command,
                'optimize': self._handle_optimize_command,
                'rewrite': self._handle_rewrite_command,
                'summarize': self._handle_summarize_command,
                'code': self._handle_code_command
            }
            
            handler = commands.get(command)
            if handler:
                await handler(content, start_time)
            else:
                await self._send_error(f"Unknown command: /{command}")
                
        except Exception as e:
            logger.error(f"Slash command error: {e}")
            await self._send_error("Failed to process command")
    
    async def handle_ping(self, data: Dict[str, Any], start_time: float):
        """Handle ping messages for latency measurement"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': datetime.now().isoformat(),
            'latency_ms': int((time.time() - start_time) * 1000)
        }))
    
    async def handle_pong(self, data: Dict[str, Any], start_time: float):
        """Handle pong responses"""
        # Update connection health metrics
        latency = int((time.time() - start_time) * 1000)
        logger.debug(f"Pong received, latency: {latency}ms")
    
    # Helper methods
    async def _authenticate_user(self):
        """Authenticate user from JWT token"""
        try:
            # Check for JWT in query params or headers
            token = None
            
            # Try query params first
            query_string = self.scope.get('query_string', b'').decode()
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            # Try headers
            if not token:
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            
            if token:
                # Decode and validate JWT (implement your JWT validation)
                # For now, use the user from scope if available
                self.user = self.scope.get('user')
                if self.user and not isinstance(self.user, AnonymousUser):
                    self.user_id = self.user.id
                else:
                    self.user = None
                    self.user_id = None
            else:
                self.user = None
                self.user_id = None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.user = None
            self.user_id = None
    
    async def _process_ai_response(self, content: str, start_time: float):
        """Process content with AI and stream response"""
        try:
            # Send typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_start',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Generate AI response
            if self.deepseek_service and self.deepseek_service.enabled:
                ai_result = await self.deepseek_service.generate_content(content)
                ai_content = ai_result.get('content', 'I apologize, but I cannot process your request right now.')
            else:
                ai_content = f"I understand you said: '{content}'. I'm currently using fallback responses as the AI service is not available."
            
            # Stop typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_stop',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Save and send AI message
            response_id = str(uuid.uuid4())
            ai_message = await self._save_message(
                message_id=response_id,
                content=ai_content,
                role='assistant',
                session_id=self.session_id
            )
            
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message_id': response_id,
                'content': ai_content,
                'role': 'assistant',
                'timestamp': ai_message.get('timestamp'),
                'session_id': self.session_id,
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }))
            
        except Exception as e:
            logger.error(f"AI response error: {e}")
            await self._send_error("Failed to generate AI response")
    
    async def _save_message(self, message_id: str, content: str, role: str, session_id: str) -> Dict[str, Any]:
        """Save message to database"""
        try:
            # This is a simplified version - adapt to your model structure
            timestamp = datetime.now().isoformat()
            
            # If you have a ChatMessage model, save here
            # For now, return a dict with timestamp
            return {
                'message_id': message_id,
                'content': content,
                'role': role,
                'session_id': session_id,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Save message error: {e}")
            return {'timestamp': datetime.now().isoformat()}
    
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
    
    # Slash command handlers
    async def _handle_intent_command(self, content: str, start_time: float):
        """Handle /intent command"""
        await self.handle_intent_analysis({'query': content}, start_time)
    
    async def _handle_optimize_command(self, content: str, start_time: float):
        """Handle /optimize command"""
        await self.handle_optimize_prompt({'prompt': content}, start_time)
    
    async def _handle_rewrite_command(self, content: str, start_time: float):
        """Handle /rewrite command"""
        prompt = f"Please rewrite the following text to make it clearer and more professional: {content}"
        await self._process_ai_response(prompt, start_time)
    
    async def _handle_summarize_command(self, content: str, start_time: float):
        """Handle /summarize command"""
        prompt = f"Please provide a clear and concise summary of the following: {content}"
        await self._process_ai_response(prompt, start_time)
    
    async def _handle_code_command(self, content: str, start_time: float):
        """Handle /code command"""
        prompt = f"Please help me with this coding request: {content}"
        await self._process_ai_response(prompt, start_time)