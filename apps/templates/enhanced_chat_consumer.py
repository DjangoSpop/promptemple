"""
Enhanced Chat Consumer with Template Integration
Automatically converts successful chat interactions into reusable templates
"""

import json
import time
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Union
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
from ..templates.models import Template, TemplateField, TemplateCategory

logger = logging.getLogger(__name__)
User = get_user_model()

class EnhancedChatConsumer(AsyncWebsocketConsumer):
    """
    Enhanced WebSocket consumer with template creation capabilities
    Automatically suggests and creates templates from successful interactions
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
        self.conversation_history = []  # Track conversation for template creation
        self.template_suggestions = []  # Track potential templates
    
    async def connect(self):
        """Handle WebSocket connection with JWT auth support"""
        try:
            # Extract session_id from URL
            self.session_id = self.scope['url_route']['kwargs'].get('session_id', str(uuid.uuid4()))
            
            # Handle authentication
            await self._handle_authentication()
            
            # Accept connection
            await self.accept()
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Send welcome message with template integration info
            await self.send(text_data=json.dumps({
                'type': 'connection_ack',
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'user_id': str(self.user_id) if self.user_id else None,
                'authenticated': self.user is not None and not isinstance(self.user, AnonymousUser),
                'features': {
                    'template_creation': True,
                    'ai_optimization': self.deepseek_service.enabled if self.deepseek_service else False,
                    'langchain_fallback': self.langchain_service is not None
                }
            }))
            
            logger.info(f"Enhanced Chat WebSocket connected: session={self.session_id}, user={self.user_id}")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Clean up on disconnect and offer template creation"""
        try:
            # Before disconnecting, check if we should suggest template creation
            if len(self.conversation_history) >= 3 and self.user_id:
                await self._suggest_template_creation()
            
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            logger.info(f"Enhanced Chat WebSocket disconnected: session={self.session_id}, code={close_code}")
        except Exception as e:
            logger.error(f"Disconnect cleanup error: {e}")
    
    async def receive(self, text_data):
        """Handle incoming messages with template awareness"""
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
                'create_template': self.handle_create_template,
                'save_conversation_as_template': self.handle_save_conversation_as_template,
                'get_template_suggestions': self.handle_get_template_suggestions,
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
        """Handle chat messages with conversation tracking for template creation"""
        try:
            content = data.get('content', '').strip()
            message_id = data.get('message_id', str(uuid.uuid4()))
            
            if not content:
                await self._send_error("Message content required")
                return
            
            # Add to conversation history
            user_message = {
                'id': message_id,
                'content': content,
                'role': 'user',
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            }
            self.conversation_history.append(user_message)
            
            # Save user message
            await self._save_message(**user_message)
            
            # Echo user message back
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message_id': message_id,
                'content': content,
                'role': 'user',
                'timestamp': user_message['timestamp'],
                'session_id': self.session_id
            }))
            
            # Process with AI and get enhanced response
            ai_response = await self._process_ai_response_enhanced(content, start_time)
            
            # Add AI response to conversation history
            if ai_response:
                self.conversation_history.append(ai_response)
            
            # Check if we should suggest template creation
            await self._check_template_opportunity()
            
        except Exception as e:
            logger.error(f"Enhanced chat message error: {e}")
            await self._send_error("Failed to process message")
    
    async def handle_create_template(self, data: Dict[str, Any], start_time: float):
        """Handle direct template creation requests"""
        try:
            if not self.user_id:
                await self._send_error("Authentication required for template creation")
                return
            
            template_data = data.get('template_data', {})
            title = template_data.get('title', '').strip()
            description = template_data.get('description', '').strip()
            content = template_data.get('content', '').strip()
            category_name = template_data.get('category', 'General')
            
            if not all([title, content]):
                await self._send_error("Title and content are required for template creation")
                return
            
            # Create template using AI assistance
            template = await self._create_template_from_data({
                'title': title,
                'description': description,
                'content': content,
                'category': category_name,
                'source': 'manual_creation'
            })
            
            if template:
                await self.send(text_data=json.dumps({
                    'type': 'template_created',
                    'template': {
                        'id': str(template['id']),
                        'title': template['title'],
                        'description': template['description'],
                        'category': template['category'],
                        'fields_count': template.get('fields_count', 0)
                    },
                    'message': 'Template created successfully!',
                    'timestamp': datetime.now().isoformat()
                }))
            else:
                await self._send_error("Failed to create template")
                
        except Exception as e:
            logger.error(f"Template creation error: {e}")
            await self._send_error("Failed to create template")
    
    async def handle_save_conversation_as_template(self, data: Dict[str, Any], start_time: float):
        """Convert current conversation into a reusable template"""
        try:
            if not self.user_id:
                await self._send_error("Authentication required for template creation")
                return
            
            if len(self.conversation_history) < 2:
                await self._send_error("Need more conversation history to create template")
                return
            
            template_title = data.get('title', '').strip()
            template_category = data.get('category', 'General')
            include_ai_responses = data.get('include_ai_responses', True)
            
            # Generate template from conversation
            template_data = await self._generate_template_from_conversation(
                title=template_title,
                category=template_category,
                include_ai_responses=include_ai_responses
            )
            
            if template_data:
                template = await self._create_template_from_data(template_data)
                
                if template:
                    await self.send(text_data=json.dumps({
                        'type': 'conversation_template_created',
                        'template': {
                            'id': str(template['id']),
                            'title': template['title'],
                            'description': template['description'],
                            'category': template['category'],
                            'source': 'conversation',
                            'message_count': len(self.conversation_history)
                        },
                        'message': 'Conversation saved as template!',
                        'timestamp': datetime.now().isoformat()
                    }))
                else:
                    await self._send_error("Failed to save conversation as template")
            else:
                await self._send_error("Could not generate template from conversation")
                
        except Exception as e:
            logger.error(f"Conversation template creation error: {e}")
            await self._send_error("Failed to save conversation as template")
    
    async def handle_get_template_suggestions(self, data: Dict[str, Any], start_time: float):
        """Get AI-powered template suggestions based on conversation"""
        try:
            suggestions = await self._get_intelligent_template_suggestions()
            
            await self.send(text_data=json.dumps({
                'type': 'template_suggestions',
                'suggestions': suggestions,
                'conversation_length': len(self.conversation_history),
                'timestamp': datetime.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Template suggestions error: {e}")
            await self._send_error("Failed to get template suggestions")
    
    async def _process_ai_response_enhanced(self, content: str, start_time: float) -> Optional[Dict[str, Any]]:
        """Enhanced AI response processing with template awareness"""
        try:
            # Send typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_start',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Get conversation context for better AI responses
            context = self._build_conversation_context()
            
            # Generate AI response with context
            if self.deepseek_service and self.deepseek_service.enabled:
                ai_result = await self.deepseek_service.generate_content_with_context(content, context)
                ai_content = ai_result.get('content', 'I apologize, but I cannot process your request right now.')
                
                # Check if AI suggests template creation
                if ai_result.get('suggests_template', False):
                    self.template_suggestions.append({
                        'trigger': content,
                        'ai_response': ai_content,
                        'confidence': ai_result.get('template_confidence', 0.5),
                        'suggested_title': ai_result.get('suggested_template_title', ''),
                        'timestamp': datetime.now().isoformat()
                    })
            else:
                # Use LangChain fallback with template awareness
                ai_content = await self._generate_fallback_response(content, context)
            
            # Stop typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing_stop',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Create AI message object
            response_id = str(uuid.uuid4())
            ai_message = {
                'id': response_id,
                'content': ai_content,
                'role': 'assistant',
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            }
            
            # Save AI message
            await self._save_message(**ai_message)
            
            # Send AI response with template suggestions if any
            response_data = {
                'type': 'message',
                'message_id': response_id,
                'content': ai_content,
                'role': 'assistant',
                'timestamp': ai_message['timestamp'],
                'session_id': self.session_id,
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
            
            # Add template suggestions if available
            if len(self.template_suggestions) > 0:
                response_data['template_suggestions'] = self.template_suggestions[-3:]  # Last 3 suggestions
            
            await self.send(text_data=json.dumps(response_data))
            
            return ai_message
            
        except Exception as e:
            logger.error(f"Enhanced AI response error: {e}")
            await self._send_error("Failed to generate AI response")
            return None
    
    async def _check_template_opportunity(self):
        """Check if current conversation presents a good template opportunity"""
        try:
            if len(self.conversation_history) < 4:  # Need reasonable conversation length
                return
            
            # Analyze conversation for template potential
            analysis = await self._analyze_conversation_for_templates()
            
            if analysis['should_suggest_template']:
                await self.send(text_data=json.dumps({
                    'type': 'template_opportunity',
                    'suggestion': {
                        'title': analysis['suggested_title'],
                        'description': analysis['suggested_description'],
                        'category': analysis['suggested_category'],
                        'confidence': analysis['confidence'],
                        'reasoning': analysis['reasoning']
                    },
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Template opportunity check error: {e}")
    
    async def _analyze_conversation_for_templates(self) -> Dict[str, Any]:
        """Analyze conversation to determine if it would make a good template"""
        try:
            if not self.conversation_history:
                return {'should_suggest_template': False}
            
            # Extract user messages and AI responses
            user_messages = [msg for msg in self.conversation_history if msg['role'] == 'user']
            ai_messages = [msg for msg in self.conversation_history if msg['role'] == 'assistant']
            
            # Simple heuristic analysis (can be enhanced with AI)
            conversation_text = ' '.join([msg['content'] for msg in self.conversation_history])
            
            # Check for template indicators
            template_indicators = [
                'help me write', 'create a', 'generate', 'template', 'format',
                'structure', 'outline', 'framework', 'process', 'steps'
            ]
            
            indicator_count = sum(1 for indicator in template_indicators if indicator in conversation_text.lower())
            
            # Determine if this looks like a good template candidate
            should_suggest = (
                len(user_messages) >= 2 and
                len(ai_messages) >= 2 and
                indicator_count >= 1 and
                len(conversation_text) > 100
            )
            
            if should_suggest:
                # Generate suggestions
                first_user_message = user_messages[0]['content']
                suggested_title = self._extract_title_from_content(first_user_message)
                suggested_category = self._extract_category_from_content(conversation_text)
                
                return {
                    'should_suggest_template': True,
                    'suggested_title': suggested_title,
                    'suggested_description': f"Template based on conversation about {suggested_title.lower()}",
                    'suggested_category': suggested_category,
                    'confidence': min(0.8, 0.3 + (indicator_count * 0.1) + (len(user_messages) * 0.05)),
                    'reasoning': f"Found {indicator_count} template indicators in {len(user_messages)} user messages"
                }
            
            return {'should_suggest_template': False}
            
        except Exception as e:
            logger.error(f"Conversation analysis error: {e}")
            return {'should_suggest_template': False}
    
    async def _generate_template_from_conversation(self, title: str, category: str, include_ai_responses: bool) -> Optional[Dict[str, Any]]:
        """Generate a template structure from the current conversation"""
        try:
            if not title:
                title = self._extract_title_from_content(self.conversation_history[0]['content'])
            
            # Build template content from conversation
            template_content = []
            template_fields = []
            
            for i, message in enumerate(self.conversation_history):
                if message['role'] == 'user':
                    # Convert user messages to fields or examples
                    content = message['content']
                    field_name = f"user_input_{i//2 + 1}"
                    template_content.append(f"**User Input {i//2 + 1}:** {content}")
                    template_fields.append({
                        'name': field_name,
                        'label': f"User Input {i//2 + 1}",
                        'type': 'textarea',
                        'placeholder': content[:100] + '...' if len(content) > 100 else content,
                        'required': True
                    })
                elif message['role'] == 'assistant' and include_ai_responses:
                    # Include AI responses as examples
                    template_content.append(f"**AI Response:** {message['content']}")
            
            description = f"Template created from conversation with {len([m for m in self.conversation_history if m['role'] == 'user'])} user inputs"
            
            return {
                'title': title,
                'description': description,
                'content': '\n\n'.join(template_content),
                'category': category,
                'fields': template_fields,
                'source': 'conversation',
                'conversation_id': self.session_id
            }
            
        except Exception as e:
            logger.error(f"Template generation error: {e}")
            return None
    
    @database_sync_to_async
    def _create_template_from_data(self, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a template in the database from template data"""
        try:
            if not self.user_id:
                return None
            
            # Get or create category
            category, _ = TemplateCategory.objects.get_or_create(
                name=template_data['category'],
                defaults={'description': f"Templates for {template_data['category']}"}
            )
            
            # Create template
            template = Template.objects.create(
                title=template_data['title'],
                description=template_data['description'],
                content=template_data['content'],
                category=category,
                created_by_id=self.user_id,
                is_public=False  # Private by default
            )
            
            # Create fields if provided
            fields_count = 0
            if 'fields' in template_data:
                for field_data in template_data['fields']:
                    TemplateField.objects.create(
                        template=template,
                        name=field_data['name'],
                        label=field_data['label'],
                        field_type=field_data.get('type', 'text'),
                        placeholder=field_data.get('placeholder', ''),
                        is_required=field_data.get('required', False)
                    )
                    fields_count += 1
            
            return {
                'id': template.id,
                'title': template.title,
                'description': template.description,
                'category': template.category.name,
                'fields_count': fields_count,
                'created_at': template.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database template creation error: {e}")
            return None
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract a meaningful title from content"""
        # Simple title extraction logic
        content = content.strip()
        if len(content) <= 50:
            return content
        
        # Take first sentence or 50 characters
        sentences = content.split('. ')
        if len(sentences) > 0 and len(sentences[0]) <= 50:
            return sentences[0]
        
        return content[:47] + "..."
    
    def _extract_category_from_content(self, content: str) -> str:
        """Extract a likely category from conversation content"""
        content_lower = content.lower()
        
        # Category mappings
        category_keywords = {
            'Writing': ['write', 'essay', 'article', 'blog', 'story', 'content'],
            'Business': ['business', 'proposal', 'meeting', 'strategy', 'plan'],
            'Marketing': ['marketing', 'campaign', 'social media', 'brand', 'promotion'],
            'Education': ['learn', 'study', 'teach', 'course', 'lesson', 'tutorial'],
            'Technology': ['code', 'programming', 'software', 'tech', 'development'],
            'Creative': ['creative', 'design', 'art', 'inspiration', 'brainstorm']
        }
        
        # Find best matching category
        best_category = 'General'
        best_score = 0
        
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category
    
    def _build_conversation_context(self) -> Dict[str, Any]:
        """Build context from conversation history for better AI responses"""
        return {
            'conversation_length': len(self.conversation_history),
            'user_messages': [msg for msg in self.conversation_history if msg['role'] == 'user'],
            'last_messages': self.conversation_history[-3:] if self.conversation_history else [],
            'session_id': self.session_id,
            'template_suggestions_count': len(self.template_suggestions)
        }
    
    async def _generate_fallback_response(self, content: str, context: Dict[str, Any]) -> str:
        """Generate fallback response when AI service is not available"""
        try:
            if self.langchain_service:
                # Use LangChain for processing
                result = await self.langchain_service.process_intent(content)
                return f"I understand you're interested in {result.get('category', 'general')} topics. Let me help you with that: {content}"
            else:
                # Simple fallback
                return f"I understand you said: '{content[:100]}...' I'm currently using fallback responses. Would you like me to help you create a template from our conversation?"
        except Exception as e:
            logger.error(f"Fallback response error: {e}")
            return "I'm here to help! Could you please rephrase your request?"
    
    async def _handle_authentication(self):
        """Handle user authentication from JWT token or headers"""
        try:
            # Check for token in query parameters (URL)
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            token = None
            
            # Handle token=undefined case
            if 'token=undefined' in query_string or 'token=' in query_string:
                # Extract token from query parameters
                for param in query_string.split('&'):
                    if param.startswith('token='):
                        token_value = param.split('=', 1)[1]
                        # Skip undefined or empty tokens
                        if token_value and token_value != 'undefined' and token_value != 'null':
                            token = token_value
                        break
            
            # Check for token in headers
            if not token:
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode('utf-8')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            if token and token != 'undefined':
                # Validate JWT token
                user = await self._validate_jwt_token(token)
                if user:
                    self.user = user
                    self.user_id = user.id
                    logger.info(f"User authenticated: {user.id}")
                    return
            
            # If no valid token, set as anonymous user
            self.user = AnonymousUser()
            self.user_id = None
            logger.info("Anonymous user connection (no valid token)")
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.user = AnonymousUser()
            self.user_id = None
    
    @database_sync_to_async
    def _validate_jwt_token(self, token: str):
        """Validate JWT token and return user"""
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            from django.contrib.auth import get_user_model
            import jwt
            from django.conf import settings
            
            # Validate the token
            try:
                # Decode the token
                decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = decoded_token.get('user_id')
                
                if user_id:
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                    return user
                    
            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, User.DoesNotExist):
                logger.warning("Invalid or expired JWT token")
                return None
                
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None
    
    async def _save_message(self, **message_data):
        """Save message to database"""
        try:
            # Only save if we have a user
            if self.user_id:
                await self._save_message_to_db(message_data)
        except Exception as e:
            logger.error(f"Message save error: {e}")
    
    @database_sync_to_async
    def _save_message_to_db(self, message_data: Dict[str, Any]):
        """Save message to database (sync operation)"""
        try:
            # This is a placeholder - implement based on your ChatMessage model
            logger.info(f"Would save message: {message_data['content'][:50]}...")
        except Exception as e:
            logger.error(f"Database save error: {e}")
    
    async def _send_error(self, message: str, error_code: str = "GENERAL_ERROR"):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error_code,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def _heartbeat_loop(self):
        """Maintain connection with periodic heartbeat"""
        try:
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                if time.time() - self.last_activity > 300:  # 5 minutes idle
                    await self.close(code=4001)  # Close idle connection
                    break
                    
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat()
                }))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
    
    async def _suggest_template_creation(self):
        """Suggest template creation when conversation ends"""
        try:
            if len(self.conversation_history) >= 3:
                await self.send(text_data=json.dumps({
                    'type': 'template_opportunity',
                    'suggestion': {
                        'title': 'Save This Conversation',
                        'description': 'This conversation could be useful as a template',
                        'category': 'General',
                        'confidence': 0.7,
                        'reasoning': 'Long conversation with valuable content'
                    },
                    'timestamp': datetime.now().isoformat()
                }))
        except Exception as e:
            logger.error(f"Template suggestion error: {e}")
    
    async def _get_intelligent_template_suggestions(self) -> List[Dict[str, Any]]:
        """Get AI-powered template suggestions"""
        try:
            # This is a placeholder for more sophisticated template suggestion logic
            suggestions = []
            
            if len(self.conversation_history) >= 2:
                suggestions.append({
                    'title': 'Current Conversation Template',
                    'description': 'Convert this conversation into a reusable template',
                    'category': self._extract_category_from_content(' '.join([msg['content'] for msg in self.conversation_history])),
                    'confidence': 0.8
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Template suggestions error: {e}")
            return []
    
    # Include all the other methods from the original ChatConsumer...
    async def handle_optimize_prompt(self, data: Dict[str, Any], start_time: float):
        """Handle prompt optimization with template suggestions"""
        # Similar to original but with template awareness
        pass
    
    async def handle_ping(self, data: Dict[str, Any], start_time: float):
        """Handle ping messages"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': datetime.now().isoformat(),
            'latency_ms': int((time.time() - start_time) * 1000)
        }))
    
    # ... (include other necessary methods from original consumer)