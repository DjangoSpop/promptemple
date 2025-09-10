"""
Chat SSE Streaming Views
Server-side streaming proxy for DeepSeek API integration
"""
from django.http import StreamingHttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.conf import settings
import httpx
import json
import re
import logging
import uuid
import time
from typing import Generator, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChatCompletionsRateThrottle(UserRateThrottle):
    """Custom rate limit for chat completions"""
    scope = 'chat_completions'
    rate = '5/min'


from rest_framework.views import APIView
from rest_framework.response import Response


class ChatCompletionsProxyView(APIView):
    """
    Server-side SSE proxy for DeepSeek chat completions
    Provides streaming AI responses while protecting API credentials
    
    Now properly uses DRF authentication with manual streaming response
    """
    
    permission_classes = [IsAuthenticated]  # Restore JWT authentication
    throttle_classes = [ChatCompletionsRateThrottle]
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to debug authentication issues"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'None')
        logger.info(f"AuthDebug: DISPATCH {request.method} {request.path} from {request.META.get('REMOTE_ADDR')} Authorization={auth_header[:50]}...")
        
        # Let DRF handle the dispatch normally
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"AuthDebug: Dispatch error - {e}")
            raise
    
    def perform_authentication(self, request):
        """
        Explicitly perform authentication to ensure user is set
        """
        try:
            # Force authentication using the configured authentication classes
            for authenticator in self.get_authenticators():
                user_auth_tuple = authenticator.authenticate(request)
                if user_auth_tuple is not None:
                    user, auth = user_auth_tuple
                    request.user = user
                    request.auth = auth
                    logger.info(f"AuthDebug: Authenticated user {user}")
                    return user, auth
            
            # If no authentication is found, set anonymous user
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
            request.auth = None
            logger.warning("AuthDebug: No authentication found, using AnonymousUser")
            return None, None
        except Exception as e:
            logger.error(f"AuthDebug: Authentication error - {e}")
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
            request.auth = None
            return None, None
    
    def post(self, request) -> StreamingHttpResponse:
        """
        Proxy streaming chat completions to DeepSeek API
        
        Expected payload:
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "deepseek-chat",
            "stream": true,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        """
        # Debug authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'None')
        logger.info(f"AuthDebug: POST {request.path} from {request.META.get('REMOTE_ADDR')} Authorization={auth_header[:50]}...")
        logger.info(f"AuthDebug: User authenticated: {request.user}")
        
        try:
            # Use DeepSeek configuration directly
            deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
            deepseek_token = deepseek_config.get('API_KEY', '')
            deepseek_base_url = deepseek_config.get('BASE_URL', 'https://api.deepseek.com')
            
            # Also check LANGCHAIN_SETTINGS as fallback
            if not deepseek_token:
                langchain_settings = getattr(settings, 'LANGCHAIN_SETTINGS', {})
                deepseek_token = langchain_settings.get('DEEPSEEK_API_KEY', '')
                deepseek_base_url = langchain_settings.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
            
            # Try ZAI configuration as fallback
            if not deepseek_token:
                zai_config = getattr(settings, 'ZAI_CONFIG', {})
                zai_token = zai_config.get('API_TOKEN', '')
                zai_base_url = zai_config.get('BASE_URL', '')
                
                if zai_token and zai_base_url:
                    base_url = zai_base_url
                    api_token = zai_token
                    logger.info(f"SSE Proxy: Using Z.AI API")
                else:
                    base_url = None
                    api_token = None
                    logger.error(f"SSE Proxy: No API configuration found")
            else:
                base_url = deepseek_base_url
                api_token = deepseek_token
                logger.info(f"SSE Proxy: Using DeepSeek API with base_url: {base_url}")
            
            if not api_token or not base_url:
                logger.error("SSE Proxy: Missing API configuration")
                from django.http import JsonResponse
                return JsonResponse({
                    "detail": "Upstream service not configured"
                }, status=503)
            
            # Get and validate request payload
            import json as json_module
            try:
                request_data = json_module.loads(request.body)
            except json_module.JSONDecodeError:
                from django.http import JsonResponse
                return JsonResponse({"detail": "Invalid JSON"}, status=400)
            
            payload = self._validate_and_prepare_payload(request_data)
            if 'error' in payload:
                from django.http import JsonResponse
                return JsonResponse(payload, status=400)
            
            # Generate unique request ID for tracking
            request_id = str(uuid.uuid4())[:8]
            
            # Create the streaming response
            response = StreamingHttpResponse(
                self._event_stream_generator(base_url, api_token, payload, request_id),
                content_type="text/event-stream"
            )
            
            # Set required SSE headers
            for header, value in getattr(settings, 'SSE_HEADERS', {}).items():
                response[header] = value
            
            # Additional SSE headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Connection'] = 'keep-alive'
            
            logger.info(f"SSE Proxy: Starting stream for request {request_id}")
            return response
            
        except Exception as e:
            logger.error(f"SSE Proxy: Unexpected error - {str(e)}")
            from django.http import JsonResponse
            return JsonResponse({
                "detail": "Internal server error",
                "error": "proxy_error"
            }, status=500)
    
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
    
    def _event_stream_generator(
        self, 
        base_url: str, 
        api_token: str, 
        payload: Dict[str, Any], 
        request_id: str
    ) -> Generator[str, None, None]:
        """
        Generate SSE stream from DeepSeek API
        """
        start_time = time.time()
        
        try:
            # Set up request headers
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "User-Agent": "PromptCraft-SSE-Proxy/1.0"
            }
            
            # Create timeout configuration
            timeout = httpx.Timeout(
                connect=10.0,  # Connection timeout
                read=None,     # No read timeout for streaming
                write=30.0,    # Write timeout
                pool=None      # No pool timeout
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
                
                # Log response headers (but not the body/tokens)
                trace_id = response.headers.get("x-trace-id", response.headers.get("x-request-id", "-"))
                logger.info(f"SSE Proxy: Connected to vendor API - Request: {request_id}, Trace: {trace_id}")
                
                # Send connection metadata
                metadata = {
                    "trace_id": trace_id,
                    "model": payload.get("model", "unknown"),
                    "stream_start": True
                }
                yield f"event: stream_start\n"
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_msg = f"Vendor API error: HTTP {response.status_code}"
                    logger.warning(f"SSE Proxy: {error_msg} - Request: {request_id}")
                    
                    yield f"event: error\n"
                    yield f"data: {{\"error\":\"{error_msg}\",\"code\":\"upstream_error\",\"status\":{response.status_code}}}\n\n"
                    return
                
                # Stream the response line by line
                buffer = ""
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
                            
                        # Forward SSE lines directly
                        if line.startswith('data: ') or line.startswith('event: ') or line.startswith('id: '):
                            yield f"{line}\n"
                        elif line == "[DONE]":
                            yield f"data: [DONE]\n\n"
                            break
                        else:
                            # Handle any non-SSE content
                            yield f"data: {line}\n"
                
                # Process any remaining buffer content
                if buffer.strip():
                    yield f"data: {buffer.strip()}\n"
                
                # Send completion event
                processing_time = int((time.time() - start_time) * 1000)
                completion_data = {
                    "stream_complete": True,
                    "processing_time_ms": processing_time,
                    "request_id": request_id
                }
                yield f"event: stream_complete\n"
                yield f"data: {json.dumps(completion_data)}\n\n"
                
                logger.info(f"SSE Proxy: Stream completed - Request: {request_id}, Duration: {processing_time}ms")
                
        except httpx.TimeoutException as e:
            error_msg = "Request timeout - vendor API is taking too long"
            logger.warning(f"SSE Proxy: Timeout - Request: {request_id} - {str(e)}")
            
            yield f"event: error\n"
            yield f"data: {{\"error\":\"{error_msg}\",\"code\":\"timeout_error\"}}\n\n"
            
        except httpx.ConnectError as e:
            error_msg = "Cannot connect to vendor API"
            logger.error(f"SSE Proxy: Connection failed - Request: {request_id} - {str(e)}")
            
            yield f"event: error\n"
            yield f"data: {{\"error\":\"{error_msg}\",\"code\":\"connection_error\"}}\n\n"
            
        except Exception as e:
            error_msg = "Streaming error occurred"
            logger.error(f"SSE Proxy: Stream error - Request: {request_id} - {str(e)}")
            
            yield f"event: error\n"
            yield f"data: {{\"error\":\"{error_msg}\",\"code\":\"stream_error\"}}\n\n"
        
        finally:
            # Always send final event to close stream properly
            yield f"event: stream_end\n"
            yield f"data: {{\"request_id\":\"{request_id}\"}}\n\n"


class ChatHealthView(APIView):
    """Health check for chat SSE service"""
    permission_classes = []  # Allow unauthenticated health checks
    
    def get(self, request):
        """Check chat service health and configuration"""
        deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
        
        config_status = {
            "chat_transport": getattr(settings, 'CHAT_TRANSPORT', 'unknown'),
            "provider": "deepseek",
            "api_base_configured": bool(deepseek_config.get('BASE_URL', '')),
            "api_token_configured": bool(deepseek_config.get('API_KEY', '')),
            "sse_available": True,
            "deepseek_base_url": deepseek_config.get('BASE_URL', 'Not configured'),
            "available_models": ['deepseek-chat', 'deepseek-reasoner']
        }
        
        # Test basic connectivity (without making actual API call)
        if config_status["api_base_configured"] and config_status["api_token_configured"]:
            status_code = "healthy"
            message = "Chat SSE service is properly configured"
        else:
            status_code = "degraded"
            message = "Chat SSE service has configuration issues"
        
        return Response({
            "status": status_code,
            "message": message,
            "config": config_status,
            "timestamp": time.time()
        })


class AuthTestView(APIView):
    """Simple authentication test endpoint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Test authentication"""
        return Response({
            "authenticated": True,
            "user": str(request.user),
            "user_id": str(request.user.id) if hasattr(request.user, 'id') else None,
            "timestamp": time.time()
        })
    
    def post(self, request):
        """Test authentication with POST"""
        return Response({
            "authenticated": True,
            "user": str(request.user),
            "user_id": str(request.user.id) if hasattr(request.user, 'id') else None,
            "data_received": request.data,
            "timestamp": time.time()
        })