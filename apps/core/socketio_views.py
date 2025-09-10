"""
Socket.IO compatibility views to handle frontend WebSocket requests
"""
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SocketIOCompatibilityView(View):
    """
    Handle Socket.IO requests and provide guidance for WebSocket connections
    """
    
    def get(self, request):
        """Handle GET requests to socket.io endpoint"""
        # Log the attempt for debugging
        logger.info(f"Socket.IO connection attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        # Return a helpful response instead of 404
        return JsonResponse({
            'error': 'Socket.IO not configured',
            'message': 'This application uses Django Channels WebSocket endpoints',
            'websocket_endpoints': {
                'chat': '/ws/chat/{session_id}/',
                'protocol': 'WebSocket (ws:// or wss://)',
                'authentication': 'JWT token in query parameters or headers'
            },
            'example_connection': 'ws://localhost:8000/ws/chat/your-session-id/',
            'documentation': '/api/schema/swagger-ui/'
        }, status=200)
    
    def post(self, request):
        """Handle POST requests to socket.io endpoint"""
        return self.get(request)
    
    def options(self, request):
        """Handle OPTIONS requests for CORS"""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


@method_decorator(csrf_exempt, name='dispatch') 
class WebSocketInfoView(View):
    """
    Provide information about available WebSocket endpoints
    """
    
    def get(self, request):
        """Return WebSocket connection information"""
        return JsonResponse({
            'websocket_info': {
                'available_endpoints': [
                    '/ws/chat/{session_id}/'
                ],
                'protocol': 'WebSocket',
                'authentication': 'JWT token in query string or headers',
                'example_urls': [
                    'ws://localhost:8000/ws/chat/test-session/',
                    'wss://yourdomain.com/ws/chat/user-123/'
                ],
                'connection_guide': {
                    'javascript': '''
                        const socket = new WebSocket('ws://localhost:8000/ws/chat/session-id/');
                        socket.onopen = function(event) { console.log('Connected'); };
                        socket.onmessage = function(event) { console.log('Message:', event.data); };
                    ''',
                    'python': '''
                        import websockets
                        import asyncio
                        
                        async def connect():
                            uri = "ws://localhost:8000/ws/chat/session-id/"
                            async with websockets.connect(uri) as websocket:
                                await websocket.send("Hello")
                                response = await websocket.recv()
                                print(response)
                    '''
                }
            }
        })