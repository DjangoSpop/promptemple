# apps/chat/enhanced_views.py
"""
Enhanced Chat SSE Streaming Views with Template Extraction
Server-side streaming proxy for DeepSeek API integration with automatic template extraction
"""
from django.http import StreamingHttpResponse, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import httpx
import json
import re
import logging
import uuid
import time
from typing import Generator, Dict, Any, Optional

# Import our models and services
try:
    from apps.chat.models import ChatSession, ChatMessage
    from chat_template_service import chat_template_service, process_chat_message_templates
    from django_models import User
except ImportError:
    # Fallback for imports
    ChatSession = None
    ChatMessage = None
    chat_template_service = None

logger = logging.getLogger(__name__)


class ChatCompletionsRateThrottle(UserRateThrottle):
    """Custom rate limit for chat completions"""
    scope = 'chat_completions'
    rate = '10/min'  # Increased for template extraction workload


class EnhancedChatCompletionsProxyView(APIView):
    """
    Enhanced Server-side SSE proxy for DeepSeek chat completions
    Now includes automatic template extraction and chat history storage
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatCompletionsRateThrottle]
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to debug authentication issues"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'None')
        logger.info(f"AuthDebug: DISPATCH {request.method} {request.path} from {request.META.get('REMOTE_ADDR')} Authorization={auth_header[:50]}...")
        
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"AuthDebug: Dispatch error - {e}")
            raise
    
    def post(self, request) -> StreamingHttpResponse:
        """
        Enhanced proxy streaming chat completions with template extraction
        
        Expected payload:
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "deepseek-chat",
            "stream": true,
            "temperature": 0.7,
            "max_tokens": 2048,
            "session_id": "optional-session-id"  // New: for chat history tracking
        }
        """
        # Debug authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'None')
        logger.info(f"AuthDebug: POST {request.path} from {request.META.get('REMOTE_ADDR')} User: {request.user}")
        
        try:
            # Get request data
            import json as json_module
            try:
                request_data = json_module.loads(request.body)
            except json_module.JSONDecodeError:
                return JsonResponse({"detail": "Invalid JSON"}, status=400)
            
            # Get or create chat session for history tracking
            chat_session = self._get_or_create_chat_session(request.user, request_data)
            
            # Store user message in chat history
            user_message = self._store_user_message(chat_session, request_data.get('messages', []))
            
            # Validate and prepare payload
            payload = self._validate_and_prepare_payload(request_data)
            if 'error' in payload:
                return JsonResponse(payload, status=400)
            
            # Get API configuration
            base_url, api_token = self._get_api_configuration()
            if not api_token or not base_url:
                logger.error("Enhanced SSE Proxy: Missing API configuration")
                return JsonResponse({
                    "detail": "Upstream service not configured"
                }, status=503)
            
            # Generate unique request ID for tracking
            request_id = str(uuid.uuid4())[:8]
            
            # Create the streaming response with template extraction
            response = StreamingHttpResponse(
                self._enhanced_event_stream_generator(
                    base_url, api_token, payload, request_id, chat_session, user_message
                ),
                content_type="text/event-stream"
            )
            
            # Set required SSE headers
            for header, value in getattr(settings, 'SSE_HEADERS', {}).items():
                response[header] = value
            
            response['Access-Control-Allow-Origin'] = '*'
            response['Connection'] = 'keep-alive'
            
            logger.info(f"Enhanced SSE Proxy: Starting stream for request {request_id}")
            return response
            
        except Exception as e:
            logger.error(f"Enhanced SSE Proxy: Unexpected error - {str(e)}")
            return JsonResponse({
                "detail": "Internal server error",
                "error": "proxy_error"
            }, status=500)
    
    def _get_or_create_chat_session(self, user, request_data):
        """Get or create chat session for history tracking"""
        if not ChatSession:
            return None
        
        session_id = request_data.get('session_id')
        model_name = request_data.get('model', 'deepseek-chat')
        
        if session_id:
            try:
                # Try to get existing session
                session = ChatSession.objects.get(id=session_id, user=user, is_active=True)
                # Update model if different
                if session.ai_model != model_name:
                    session.ai_model = model_name
                    session.save(update_fields=['ai_model', 'updated_at'])
                return session
            except ChatSession.DoesNotExist:
                pass
        
        # Create new session
        session = ChatSession.objects.create(
            user=user,
            title=self._generate_session_title(request_data.get('messages', [])),
            ai_model=model_name,
            model_provider='deepseek',
            session_metadata={
                'created_from': 'api',
                'initial_model': model_name,
                'user_agent': request_data.get('user_agent', ''),
            }
        )
        
        logger.info(f"Created new chat session {session.id} for user {user.id}")
        return session
    
    def _generate_session_title(self, messages):
        """Generate a title for the chat session based on first user message"""
        for message in messages:
            if message.get('role') == 'user':
                content = message.get('content', '')
                if content:
                    # Take first 50 characters as title
                    title = content[:50].strip()
                    if len(content) > 50:
                        title += "..."
                    return title
        return "New Chat Session"
    
    def _store_user_message(self, chat_session, messages):
        """Store the latest user message in chat history"""
        if not ChatMessage or not chat_session:
            return None
        
        # Find the latest user message
        user_message = None
        for message in reversed(messages):
            if message.get('role') == 'user':
                user_message = message
                break
        
        if not user_message:
            return None
        
        # Store in database
        stored_message = ChatMessage.objects.create(
            session=chat_session,
            role='user',
            content=user_message.get('content', ''),
            original_content=user_message.get('content', ''),
            message_metadata={
                'timestamp': timezone.now().isoformat(),
                'message_index': len(messages)
            }
        )
        
        # Update session stats
        chat_session.total_messages += 1
        chat_session.save(update_fields=['total_messages', 'updated_at'])
        
        return stored_message
    
    def _get_api_configuration(self):
        """Get API configuration with priority: DeepSeek > LangChain > ZAI"""
        # Try DeepSeek configuration first
        deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
        deepseek_token = deepseek_config.get('API_KEY', '')
        deepseek_base_url = deepseek_config.get('BASE_URL', 'https://api.deepseek.com')
        
        if deepseek_token:
            logger.info(f"Enhanced SSE Proxy: Using DeepSeek API with base_url: {deepseek_base_url}")
            return deepseek_base_url, deepseek_token
        
        # Try LANGCHAIN_SETTINGS as fallback
        langchain_settings = getattr(settings, 'LANGCHAIN_SETTINGS', {})
        deepseek_token = langchain_settings.get('DEEPSEEK_API_KEY', '')
        deepseek_base_url = langchain_settings.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        if deepseek_token:
            logger.info(f"Enhanced SSE Proxy: Using LangChain DeepSeek config")
            return deepseek_base_url, deepseek_token
        
        # Try ZAI configuration as final fallback
        zai_config = getattr(settings, 'ZAI_CONFIG', {})
        zai_token = zai_config.get('API_TOKEN', '')
        zai_base_url = zai_config.get('BASE_URL', '')
        
        if zai_token and zai_base_url:
            logger.info(f"Enhanced SSE Proxy: Using Z.AI API")
            return zai_base_url, zai_token
        
        logger.error(f"Enhanced SSE Proxy: No API configuration found")
        return None, None
    
    def _validate_and_prepare_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and prepare the request payload"""
        if not isinstance(data, dict):
            return {"error": "Invalid JSON payload"}
        
        # Required fields
        messages = data.get('messages', [])
        if not messages or not isinstance(messages, list):
            return {"error": "Messages array is required"}
        
        # Validate message format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return {"error": "Each message must have 'role' and 'content' fields"}
            
            if msg['role'] not in ['user', 'assistant', 'system']:
                return {"error": "Message role must be 'user', 'assistant', or 'system'"}
        
        # Get DeepSeek configuration
        deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
        
        # Prepare payload for DeepSeek API
        vendor_payload = {
            "messages": messages,
            "model": data.get('model', deepseek_config.get('DEFAULT_MODEL', 'deepseek-chat')),
            "stream": True,  # Force streaming
            "temperature": float(data.get('temperature', 0.7)),
            "max_tokens": int(data.get('max_tokens', deepseek_config.get('MAX_TOKENS', 4096)))
        }
        
        # Forward any additional vendor-specific parameters
        vendor_keys = [
            'top_p', 'frequency_penalty', 'presence_penalty', 
            'stop', 'user', 'logit_bias'
        ]
        for key in vendor_keys:
            if key in data:
                vendor_payload[key] = data[key]
        
        return vendor_payload
    
    def _enhanced_event_stream_generator(
        self, 
        base_url: str, 
        api_token: str, 
        payload: Dict[str, Any], 
        request_id: str,
        chat_session,
        user_message
    ) -> Generator[str, None, None]:
        """
        Enhanced generator that captures AI response and triggers template extraction
        """
        start_time = time.time()
        ai_response_content = ""  # Accumulate AI response for template extraction
        
        try:
            # Set up request headers
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "User-Agent": "PromptCraft-Enhanced-SSE-Proxy/1.0"
            }
            
            # Create timeout configuration
            timeout = httpx.Timeout(
                connect=10.0,
                read=None,
                write=30.0,
                pool=None
            )
            
            # Send initial connection event
            yield f"event: meta\n"
            yield f"data: {{\"request_id\":\"{request_id}\",\"status\":\"connected\"}}\n\n"
            
            # Start streaming request
            with httpx.stream(
                "POST",
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
                follow_redirects=True
            ) as response:
                
                trace_id = response.headers.get("x-trace-id", response.headers.get("x-request-id", "-"))
                logger.info(f"Enhanced SSE Proxy: Connected to vendor API - Request: {request_id}, Trace: {trace_id}")
                
                # Send connection metadata
                metadata = {
                    "trace_id": trace_id,
                    "model": payload.get("model", "unknown"),
                    "stream_start": True,
                    "session_id": str(chat_session.id) if chat_session else None
                }
                yield f"event: stream_start\n"
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_msg = f"Vendor API error: HTTP {response.status_code}"
                    logger.warning(f"Enhanced SSE Proxy: {error_msg} - Request: {request_id}")
                    
                    yield f"event: error\n"
                    yield f"data: {{\"error\":\"{error_msg}\",\"code\":\"upstream_error\",\"status\":{response.status_code}}}\n\n"
                    return
                
                # Stream the response line by line
                buffer = ""
                tokens_used = 0
                
                for chunk in response.iter_text():
                    if not chunk:
                        continue
                    
                    buffer += chunk
                    lines = buffer.split('\n')
                    buffer = lines[-1]  # Keep incomplete line in buffer
                    
                    for line in lines[:-1]:
                        line = line.strip()
                        if not line:
                            yield "\n"
                            continue
                        
                        # Parse and extract content from streaming chunks
                        if line.startswith('data: '):
                            data_content = line[6:]  # Remove 'data: ' prefix
                            
                            # Try to parse JSON to extract content
                            try:
                                if data_content != '[DONE]':
                                    chunk_data = json.loads(data_content)
                                    if 'choices' in chunk_data:
                                        for choice in chunk_data['choices']:
                                            if 'delta' in choice and 'content' in choice['delta']:
                                                content = choice['delta']['content']
                                                if content:
                                                    ai_response_content += content
                                                    tokens_used += 1
                            except json.JSONDecodeError:
                                pass  # Skip non-JSON data lines
                        
                        # Forward SSE lines directly
                        if line.startswith('data: ') or line.startswith('event: ') or line.startswith('id: '):
                            yield f"{line}\n"
                        elif line == "[DONE]":
                            yield f"data: [DONE]\n\n"
                            break
                        else:
                            yield f"data: {line}\n"
                
                # Process any remaining buffer content
                if buffer.strip():
                    yield f"data: {buffer.strip()}\n"
                
                # Store AI response and trigger template extraction
                if ai_response_content and chat_session:
                    self._store_ai_response_and_extract_templates(
                        chat_session, ai_response_content, tokens_used, payload.get("model", "deepseek-chat")
                    )
                
                # Send completion event with template extraction info
                processing_time = int((time.time() - start_time) * 1000)
                completion_data = {
                    "stream_complete": True,
                    "processing_time_ms": processing_time,
                    "request_id": request_id,
                    "tokens_used": tokens_used,
                    "response_length": len(ai_response_content),
                    "template_extraction": {
                        "enabled": bool(chat_template_service),
                        "content_length": len(ai_response_content),
                        "will_process": len(ai_response_content) >= 100  # Minimum length for processing
                    }
                }
                yield f"event: stream_complete\n"
                yield f"data: {json.dumps(completion_data)}\n\n"
                
                logger.info(f"Enhanced SSE Proxy: Stream completed - Request: {request_id}, Duration: {processing_time}ms, Response length: {len(ai_response_content)}")
                
        except Exception as e:
            error_msg = f"Enhanced streaming error: {str(e)}"
            logger.error(f"Enhanced SSE Proxy: Stream error - Request: {request_id} - {str(e)}")
            
            yield f"event: error\n"
            yield f"data: {{\"error\":\"{error_msg}\",\"code\":\"enhanced_stream_error\"}}\n\n"
        
        finally:
            # Always send final event to close stream properly
            yield f"event: stream_end\n"
            yield f"data: {{\"request_id\":\"{request_id}\"}}\n\n"
    
    def _store_ai_response_and_extract_templates(self, chat_session, content, tokens_used, model_name):
        """Store AI response and trigger async template extraction"""
        if not ChatMessage or not chat_session:
            return
        
        try:
            # Store AI response in database
            ai_message = ChatMessage.objects.create(
                session=chat_session,
                role='assistant',
                content=content,
                original_content=content,
                model_used=model_name,
                tokens_used=tokens_used,
                message_metadata={
                    'timestamp': timezone.now().isoformat(),
                    'content_length': len(content),
                    'response_complete': True
                }
            )
            
            # Update session stats
            with transaction.atomic():
                chat_session.total_messages += 1
                chat_session.total_tokens_used += tokens_used
                chat_session.save(update_fields=['total_messages', 'total_tokens_used', 'updated_at'])
            
            # Trigger async template extraction if service is available
            if chat_template_service and len(content) >= 100:  # Minimum content length
                try:
                    # Trigger async processing
                    process_chat_message_templates.delay(str(ai_message.id))
                    logger.info(f"Triggered template extraction for message {ai_message.id}")
                except Exception as e:
                    logger.error(f"Failed to trigger template extraction: {e}")
                    
                    # Fallback to synchronous processing
                    try:
                        result = chat_template_service.process_chat_message(ai_message)
                        logger.info(f"Synchronous template extraction result: {result}")
                    except Exception as sync_e:
                        logger.error(f"Synchronous template extraction failed: {sync_e}")
            
        except Exception as e:
            logger.error(f"Error storing AI response: {e}")


class TemplateExtractionStatusView(APIView):
    """View to check template extraction status for a user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's template extraction statistics"""
        if not chat_template_service:
            return Response({
                "error": "Template extraction service not available"
            }, status=503)
        
        try:
            stats = chat_template_service.get_user_template_stats(request.user)
            return Response({
                "status": "success",
                "stats": stats,
                "timestamp": timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting template stats for user {request.user.id}: {e}")
            return Response({
                "error": "Failed to retrieve template statistics"
            }, status=500)


class ExtractedTemplatesView(APIView):
    """View to manage extracted templates"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's extracted templates"""
        if not ChatMessage:
            return Response({"error": "Chat models not available"}, status=503)
        
        try:
            from apps.chat.models import ExtractedTemplate
            
            # Get query parameters
            status_filter = request.query_params.get('status', None)
            quality_filter = request.query_params.get('quality', None)
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
            
            # Build query
            templates = ExtractedTemplate.objects.filter(user=request.user)
            
            if status_filter:
                templates = templates.filter(status=status_filter)
            if quality_filter:
                templates = templates.filter(quality_rating=quality_filter)
            
            # Get total count
            total_count = templates.count()
            
            # Apply pagination
            templates = templates.order_by('-created_at')[offset:offset + limit]
            
            # Serialize templates
            template_data = []
            for template in templates:
                template_data.append({
                    'id': str(template.id),
                    'title': template.title,
                    'description': template.description,
                    'category': template.category_suggestion,
                    'quality_rating': template.quality_rating,
                    'confidence_score': template.confidence_score,
                    'status': template.status,
                    'auto_approved': template.auto_approved,
                    'keywords': template.keywords_extracted,
                    'use_cases': template.use_cases,
                    'created_at': template.created_at.isoformat(),
                    'published': bool(template.published_template),
                    'published_template_id': str(template.published_template.id) if template.published_template else None
                })
            
            return Response({
                'status': 'success',
                'templates': template_data,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting extracted templates for user {request.user.id}: {e}")
            return Response({
                "error": "Failed to retrieve extracted templates"
            }, status=500)
    
    def patch(self, request, template_id):
        """Update extracted template status"""
        if not ChatMessage:
            return Response({"error": "Chat models not available"}, status=503)
        
        try:
            from apps.chat.models import ExtractedTemplate
            
            template = ExtractedTemplate.objects.get(id=template_id, user=request.user)
            
            # Get update data
            new_status = request.data.get('status')
            review_notes = request.data.get('review_notes', '')
            
            if new_status and new_status in ['approved', 'rejected', 'needs_revision']:
                template.status = new_status
                template.review_notes = review_notes
                template.reviewed_by = request.user
                template.reviewed_at = timezone.now()
                template.save()
                
                # If approved, try to publish to template library
                if new_status == 'approved' and chat_template_service:
                    published_template = chat_template_service.publish_approved_template(template)
                    if published_template:
                        logger.info(f"Published template {published_template.id} from extraction {template.id}")
                
                return Response({
                    'status': 'success',
                    'message': f'Template status updated to {new_status}',
                    'template': {
                        'id': str(template.id),
                        'status': template.status,
                        'reviewed_at': template.reviewed_at.isoformat() if template.reviewed_at else None,
                        'published': bool(template.published_template)
                    }
                })
            else:
                return Response({
                    'error': 'Invalid status. Must be approved, rejected, or needs_revision'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            return Response({
                "error": "Failed to update template"
            }, status=500)


class ChatSessionsView(APIView):
    """View to manage chat sessions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's chat sessions"""
        if not ChatSession:
            return Response({"error": "Chat models not available"}, status=503)
        
        try:
            sessions = ChatSession.objects.filter(user=request.user, is_active=True)
            
            session_data = []
            for session in sessions.order_by('-updated_at')[:20]:  # Last 20 sessions
                session_data.append({
                    'id': str(session.id),
                    'title': session.title,
                    'ai_model': session.ai_model,
                    'total_messages': session.total_messages,
                    'extracted_templates_count': session.extracted_templates_count,
                    'templates_approved': session.templates_approved,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat()
                })
            
            return Response({
                'status': 'success',
                'sessions': session_data,
                'total_sessions': sessions.count(),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting chat sessions for user {request.user.id}: {e}")
            return Response({
                "error": "Failed to retrieve chat sessions"
            }, status=500)