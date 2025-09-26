from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dataclasses import asdict
import logging
import asyncio
import json
import time
from typing import Dict, Any, Optional

from .models import AssistantThread, AssistantMessage
from .ai_assistants import AssistantRegistry
# Import DeepSeek services
try:
    from apps.templates.deepseek_service import get_deepseek_service, DeepSeekService
    from apps.templates.deepseek_integration import create_deepseek_llm, DeepSeekLangChainWrapper
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    DEEPSEEK_AVAILABLE = False
    logging.warning(f"DeepSeek services not available: {e}")

logger = logging.getLogger(__name__)


class AIProviderListView(APIView):
    """List available AI providers including DeepSeek"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        providers = [
            {
                'id': 'openai',
                'name': 'OpenAI',
                'status': 'available',
                'models': ['gpt-3.5-turbo', 'gpt-4'],
                'features': ['chat', 'completion', 'embeddings']
            },
            {
                'id': 'anthropic',
                'name': 'Anthropic',
                'status': 'available',
                'models': ['claude-3-haiku', 'claude-3-sonnet'],
                'features': ['chat', 'analysis']
            }
        ]
        
        # Add DeepSeek if available
        if DEEPSEEK_AVAILABLE:
            deepseek_service = get_deepseek_service()
            deepseek_status = 'available' if (deepseek_service and deepseek_service.enabled) else 'disabled'
            
            providers.append({
                'id': 'deepseek',
                'name': 'DeepSeek',
                'status': deepseek_status,
                'models': ['deepseek-chat', 'deepseek-coder', 'deepseek-math'],
                'features': ['chat', 'code_generation', 'optimization', 'cost_effective'],
                'cost_per_1k_tokens': 0.0014,  # Very affordable
                'max_tokens': 4000
            })
        
        return Response({
            'providers': providers,
            'total_providers': len(providers),
            'deepseek_available': DEEPSEEK_AVAILABLE
        })

class DeepSeekStreamView(APIView):
    """Server-side streaming proxy for DeepSeek (SSE-like StreamingHttpResponse)

    This view re-uses the SSE proxy pattern from apps.chat.views.ChatCompletionsProxyView
    but keeps the implementation local to ai_services so frontend can call `/api/.../deepseek/stream/`.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.http import StreamingHttpResponse
        import uuid
        import time
        import httpx

        try:
            base_url = getattr(settings, 'DEEPSEEK_BASE_URL', '').rstrip('/') or getattr(settings, 'ZAI_API_BASE', '').rstrip('/')
            api_key = getattr(settings, 'DEEPSEEK_API_KEY', '') or getattr(settings, 'ZAI_API_TOKEN', '')

            if not base_url or not api_key:
                return Response({"detail": "DeepSeek upstream not configured"}, status=503)

            # Prepare payload
            messages = request.data.get('messages') or request.data.get('prompt')
            model = request.data.get('model', getattr(settings, 'DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat'))
            temperature = float(request.data.get('temperature', 0.7))
            max_tokens = int(request.data.get('max_tokens', getattr(settings, 'DEEPSEEK_MAX_TOKENS', 2048)))

            if not messages:
                return Response({"error": "messages or prompt required"}, status=400)

            # Build vendor payload
            vendor_payload = {
                "messages": messages if isinstance(messages, list) else [{"role": "user", "content": str(messages)}],
                "model": model,
                "stream": True,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            request_id = str(uuid.uuid4())[:8]

            def generator():
                # Minimal SSE-like stream via StreamingHttpResponse
                start = time.time()
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Accept': 'text/event-stream',
                    'Content-Type': 'application/json'
                }

                timeout = httpx.Timeout(connect=10.0, read=None, write=30.0)

                yield f"event: meta\n"
                yield f"data: {{\"request_id\":\"{request_id}\", \"status\":\"connected\"}}\n\n"

                try:
                    with httpx.stream('POST', f"{base_url}/chat/completions", headers=headers, json=vendor_payload, timeout=timeout) as r:
                        trace = r.headers.get('x-trace-id', r.headers.get('x-request-id', '-'))
                        yield f"event: stream_start\n"
                        yield f"data: {{\"trace_id\":\"{trace}\", \"model\":\"{model}\"}}\n\n"

                        if r.status_code != 200:
                            yield f"event: error\n"
                            yield f"data: {{\"error\": \"upstream {r.status_code}\"}}\n\n"
                            return

                        buffer = ''
                        for chunk in r.iter_text():
                            if not chunk:
                                continue
                            buffer += chunk
                            lines = buffer.split('\n')
                            buffer = lines[-1]
                            for line in lines[:-1]:
                                line = line.strip()
                                if not line:
                                    continue
                                if line == '[DONE]':
                                    yield f"data: [DONE]\n\n"
                                    return
                                # forward as data lines
                                yield f"data: {line}\n\n"

                        if buffer.strip():
                            yield f"data: {buffer.strip()}\n\n"

                        processing_time = int((time.time() - start) * 1000)
                        yield f"event: stream_complete\n"
                        yield f"data: {{\"request_id\":\"{request_id}\", \"processing_time_ms\": {processing_time}}}\n\n"

                except Exception as e:
                    yield f"event: error\n"
                    yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                finally:
                    yield f"event: stream_end\n"
                    yield f"data: {{\"request_id\":\"{request_id}\"}}\n\n"

            response = StreamingHttpResponse(generator(), content_type='text/event-stream')
            response['Access-Control-Allow-Origin'] = '*'
            response['Connection'] = 'keep-alive'
            return response

        except Exception as e:
            logger.error(f"DeepSeekStreamView error: {e}")
            return Response({"error": "internal_error", "details": str(e)}, status=500)

class AIModelListView(APIView):
    """List available AI models including DeepSeek models"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        models = [
            {
                'id': 'gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'provider': 'openai',
                'cost_per_token': 0.002,
                'max_tokens': 4096,
                'features': ['chat', 'completion']
            },
            {
                'id': 'gpt-4',
                'name': 'GPT-4',
                'provider': 'openai',
                'cost_per_token': 0.03,
                'max_tokens': 8192,
                'features': ['chat', 'completion', 'analysis']
            }
        ]
        
        # Add DeepSeek models if available
        if DEEPSEEK_AVAILABLE:
            deepseek_service = get_deepseek_service()
            if deepseek_service and deepseek_service.enabled:
                deepseek_models = [
                    {
                        'id': 'deepseek-chat',
                        'name': 'DeepSeek Chat',
                        'provider': 'deepseek',
                        'cost_per_token': 0.0014,
                        'max_tokens': 4000,
                        'features': ['chat', 'general_purpose'],
                        'description': 'General conversation and reasoning'
                    },
                    {
                        'id': 'deepseek-coder',
                        'name': 'DeepSeek Coder',
                        'provider': 'deepseek',
                        'cost_per_token': 0.0014,
                        'max_tokens': 4000,
                        'features': ['code_generation', 'programming'],
                        'description': 'Specialized for code generation and programming tasks'
                    },
                    {
                        'id': 'deepseek-math',
                        'name': 'DeepSeek Math',
                        'provider': 'deepseek',
                        'cost_per_token': 0.0014,
                        'max_tokens': 4000,
                        'features': ['mathematical_reasoning'],
                        'description': 'Mathematical reasoning and problem solving'
                    }
                ]
                models.extend(deepseek_models)
        
        return Response({
            'models': models,
            'total_models': len(models),
            'deepseek_available': DEEPSEEK_AVAILABLE
        })


class AIGenerateView(APIView):
    """AI generation endpoint with DeepSeek integration"""
    permission_classes = [permissions.IsAuthenticated]
    
    async def _generate_with_deepseek(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Generate content using DeepSeek"""
        try:
            deepseek_service = get_deepseek_service()
            if not deepseek_service or not deepseek_service.enabled:
                raise Exception("DeepSeek service not available")
            
            start_time = time.time()
            
            # Map model to specific DeepSeek model
            model_mapping = {
                'deepseek-chat': deepseek_service.config.model_chat,
                'deepseek-coder': deepseek_service.config.model_coder,
                'deepseek-math': deepseek_service.config.model_math
            }
            
            deepseek_model = model_mapping.get(model, deepseek_service.config.model_chat)
            
            # Create messages format
            messages = [{"role": "user", "content": prompt}]
            
            # Generate response
            response = await deepseek_service._make_request(
                messages=messages,
                model=deepseek_model,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000)
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if response.success:
                return {
                    'content': response.content,
                    'model': response.model,
                    'tokens_used': response.tokens_used,
                    'processing_time_ms': processing_time,
                    'cost_estimate': response.tokens_used * 0.0014 / 1000,  # DeepSeek pricing
                    'success': True,
                    'provider': 'deepseek'
                }
            else:
                return {
                    'content': '',
                    'error': response.error,
                    'success': False,
                    'processing_time_ms': processing_time,
                    'provider': 'deepseek'
                }
                
        except Exception as e:
            logger.error(f"DeepSeek generation error: {e}")
            return {
                'content': '',
                'error': str(e),
                'success': False,
                'provider': 'deepseek'
            }
    
    def post(self, request):
        prompt = request.data.get('prompt', '').strip()
        model = request.data.get('model', 'deepseek-chat')
        temperature = request.data.get('temperature', 0.7)
        max_tokens = request.data.get('max_tokens', 1000)
        
        if not prompt:
            return Response({
                'error': 'Prompt is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if it's a DeepSeek model
        if model.startswith('deepseek-') and DEEPSEEK_AVAILABLE:
            try:
                # Run async function in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self._generate_with_deepseek(
                        prompt=prompt,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                )
                
                loop.close()
                
                if result['success']:
                    return Response({
                        'result': result['content'],
                        'model': result['model'],
                        'tokens_used': result['tokens_used'],
                        'processing_time_ms': result['processing_time_ms'],
                        'cost_estimate': result['cost_estimate'],
                        'provider': 'deepseek',
                        'success': True
                    })
                else:
                    return Response({
                        'error': result['error'],
                        'provider': 'deepseek',
                        'success': False
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                logger.error(f"DeepSeek generation error: {e}")
                return Response({
                    'error': f'DeepSeek generation failed: {str(e)}',
                    'provider': 'deepseek',
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Fallback for other models
        return Response({
            'message': f'Generated content for prompt: "{prompt[:50]}..." using model: {model}',
            'result': f'[Placeholder] This would be generated content using {model}',
            'tokens_used': 150,
            'cost_estimate': 0.30,
            'provider': 'placeholder',
            'success': True
        })


class AIUsageView(APIView):
    """Placeholder AI usage view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': 'AI Usage endpoint - Coming soon!',
            'usage': {
                'tokens_used_today': 1250,
                'tokens_remaining': 8750,
                'cost_today': 2.50,
                'monthly_limit': 10000
            }
        })


class AIQuotaView(APIView):
    """Placeholder AI quota view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': 'AI Quota endpoint - Coming soon!',
            'quotas': {
                'daily_limit': 1000,
                'monthly_limit': 10000,
                'used_today': 125,
                'used_monthly': 3450,
                'reset_time': '2025-06-21T00:00:00Z'
            }
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_suggestions(request):
    """
    AI-powered suggestions endpoint for autocomplete functionality
    """
    try:
        partial = request.GET.get('partial', '')
        limit = int(request.GET.get('limit', 10))
        
        # Get suggestions from prompt library
        suggestions = []
        
        if partial and len(partial) >= 2:
            try:
                # Try to import PromptLibrary model from templates app
                from apps.templates.models import PromptLibrary
                
                # Search for prompts that match the partial input
                matching_prompts = PromptLibrary.objects.filter(
                    Q(title__icontains=partial) | 
                    Q(content__icontains=partial) |
                    Q(tags__icontains=partial)
                ).distinct()[:limit]
                
                suggestions = [
                    {
                        'id': str(prompt.id),
                        'text': prompt.title,
                        'description': prompt.description[:100] if prompt.description else '',
                        'category': prompt.category.name if prompt.category else 'General',
                        'type': 'prompt'
                    }
                    for prompt in matching_prompts
                ]
                
            except Exception as e:
                logger.warning(f"Could not search prompts: {e}")
                
        # Add some common AI suggestions if no prompts found
        if not suggestions:
            common_suggestions = [
                {'id': 'write_email', 'text': 'Write a professional email', 'description': 'Generate professional email content', 'category': 'Communication', 'type': 'template'},
                {'id': 'summarize', 'text': 'Summarize this text', 'description': 'Create a concise summary', 'category': 'Analysis', 'type': 'template'},
                {'id': 'explain', 'text': 'Explain this concept', 'description': 'Break down complex topics', 'category': 'Education', 'type': 'template'},
                {'id': 'brainstorm', 'text': 'Brainstorm ideas', 'description': 'Generate creative ideas', 'category': 'Creative', 'type': 'template'},
                {'id': 'translate', 'text': 'Translate text', 'description': 'Translate between languages', 'category': 'Language', 'type': 'template'},
            ]
            
            # Filter common suggestions based on partial input
            if partial:
                suggestions = [
                    s for s in common_suggestions 
                    if partial.lower() in s['text'].lower() or partial.lower() in s['description'].lower()
                ][:limit]
            else:
                suggestions = common_suggestions[:limit]
        
        return Response({
            'suggestions': suggestions,
            'total': len(suggestions),
            'partial': partial,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error in ai_suggestions: {e}")
        return Response({
            'suggestions': [],
            'total': 0,
            'error': 'Failed to get suggestions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def deepseek_chat(request):
    """
    DeepSeek-specific chat endpoint for real-time AI conversations
    """
    try:
        if not DEEPSEEK_AVAILABLE:
            return Response({
                'error': 'DeepSeek service not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        messages = request.data.get('messages', [])
        model = request.data.get('model', 'deepseek-chat')
        temperature = request.data.get('temperature', 0.7)
        max_tokens = request.data.get('max_tokens', 1000)
        stream = request.data.get('stream', False)
        
        if not messages:
            return Response({
                'error': 'Messages are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate message format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return Response({
                    'error': 'Invalid message format. Each message must have "role" and "content"'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        async def generate_response():
            deepseek_service = get_deepseek_service()
            if not deepseek_service or not deepseek_service.enabled:
                raise Exception("DeepSeek service not properly configured")
            
            start_time = time.time()
            
            response = await deepseek_service._make_request(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                'response': response,
                'processing_time': processing_time
            }
        
        # Execute async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(generate_response())
            response_data = result['response']
            
            if response_data.success:
                return Response({
                    'message': {
                        'role': 'assistant',
                        'content': response_data.content
                    },
                    'model': response_data.model,
                    'tokens_used': response_data.tokens_used,
                    'processing_time_ms': result['processing_time'],
                    'cost_estimate': response_data.tokens_used * 0.0014 / 1000,
                    'provider': 'deepseek',
                    'success': True
                })
            else:
                return Response({
                    'error': response_data.error,
                    'processing_time_ms': result['processing_time'],
                    'provider': 'deepseek',
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"DeepSeek chat error: {e}")
        return Response({
            'error': f'DeepSeek chat failed: {str(e)}',
            'provider': 'deepseek',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def deepseek_test(request):
    """
    Test DeepSeek connectivity and configuration
    """
    try:
        if not DEEPSEEK_AVAILABLE:
            return Response({
                'status': 'error',
                'message': 'DeepSeek service not available - import failed',
                'available': False
            })
        
        deepseek_service = get_deepseek_service()
        
        if not deepseek_service:
            return Response({
                'status': 'error',
                'message': 'DeepSeek service could not be initialized',
                'available': False
            })
        
        if not deepseek_service.enabled:
            return Response({
                'status': 'error',
                'message': 'DeepSeek service disabled - API key not configured',
                'available': False,
                'api_key_configured': False
            })
        
        async def test_connection():
            # Test with a simple message
            test_messages = [{"role": "user", "content": "Say 'Hello from DeepSeek!' if you can hear me."}]
            
            start_time = time.time()
            response = await deepseek_service._make_request(test_messages)
            test_time = int((time.time() - start_time) * 1000)
            
            return {
                'response': response,
                'test_time': test_time
            }
        
        # Execute test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(test_connection())
            response_data = result['response']
            
            if response_data.success:
                return Response({
                    'status': 'success',
                    'message': 'DeepSeek is working correctly',
                    'available': True,
                    'api_key_configured': True,
                    'test_response': response_data.content,
                    'model': response_data.model,
                    'tokens_used': response_data.tokens_used,
                    'response_time_ms': result['test_time'],
                    'config': {
                        'base_url': deepseek_service.config.base_url,
                        'model_chat': deepseek_service.config.model_chat,
                        'model_coder': deepseek_service.config.model_coder,
                        'max_tokens': deepseek_service.config.max_tokens,
                        'temperature': deepseek_service.config.temperature
                    }
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'DeepSeek API error: {response_data.error}',
                    'available': True,
                    'api_key_configured': True,
                    'response_time_ms': result['test_time'],
                    'error_details': response_data.error
                })
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"DeepSeek test error: {e}")
        return Response({
            'status': 'error',
            'message': f'DeepSeek test failed: {str(e)}',
            'available': False,
            'error_details': str(e)
        })

class AssistantListView(APIView):
    """Expose registered assistants to the frontend."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        descriptions = [asdict(desc) for desc in AssistantRegistry.list_descriptions()]
        default_assistant = getattr(
            settings,
            "AI_ASSISTANT_SETTINGS",
            {},
        ).get("DEFAULT_ASSISTANT", "deepseek_chat")
        return Response(
            {
                "assistants": descriptions,
                "default_assistant": default_assistant,
                "total": len(descriptions),
            }
        )


class AssistantRunView(APIView):
    """Run an assistant synchronously via standard Django view."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payload = request.data or {}
        assistant_id = payload.get("assistant_id") or getattr(
            settings,
            "AI_ASSISTANT_SETTINGS",
            {},
        ).get("DEFAULT_ASSISTANT", "deepseek_chat")
        message = payload.get("message")
        thread_id = payload.get("thread_id")
        metadata = payload.get("metadata") or {}

        if not message:
            return Response(
                {"detail": "Request must include a non-empty 'message'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            assistant = AssistantRegistry.create(
                assistant_id,
                user=request.user,
                request=request,
                view=self,
            )
        except KeyError:
            return Response(
                {"detail": f"Assistant '{assistant_id}' is not available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = assistant.run(message, thread_id=thread_id, metadata=metadata)
        return Response(result, status=status.HTTP_200_OK)


class AssistantThreadListView(APIView):
    """Return threads created by the current user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        threads = AssistantThread.objects.filter(user=request.user).order_by("-last_interaction_at")
        serialized = [
            {
                "id": str(thread.id),
                "assistant_id": thread.assistant_id,
                "title": thread.title,
                "metadata": thread.metadata,
                "last_interaction_at": thread.last_interaction_at,
                "created_at": thread.created_at,
            }
            for thread in threads
        ]
        return Response({"threads": serialized, "total": len(serialized)})


class AssistantThreadDetailView(APIView):
    """Return a thread with its messages."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, thread_id: str):
        thread = get_object_or_404(AssistantThread, id=thread_id)
        if thread.user and thread.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        messages = thread.messages.order_by("created_at")
        serialized_messages = [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
                "tool_name": message.tool_name or None,
                "tool_result": message.tool_result or None,
            }
            for message in messages
        ]

        return Response(
            {
                "thread": {
                    "id": str(thread.id),
                    "assistant_id": thread.assistant_id,
                    "title": thread.title,
                    "metadata": thread.metadata,
                    "created_at": thread.created_at,
                    "last_interaction_at": thread.last_interaction_at,
                },
                "messages": serialized_messages,
            }
        )