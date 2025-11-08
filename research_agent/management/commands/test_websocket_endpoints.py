"""
WebSocket Endpoint Testing and Diagnostics
Helps debug frontend WebSocket connection issues
"""

import asyncio
import websockets
import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Test WebSocket endpoints and provide connection diagnostics"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='WebSocket host (default: localhost)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='WebSocket port (default: 8000)'
        )
        parser.add_argument(
            '--session-id',
            type=str,
            default='test_session_123',
            help='Session ID for testing (default: test_session_123)'
        )
        parser.add_argument(
            '--endpoint',
            type=str,
            choices=['chat', 'health', 'assistant', 'all'],
            default='all',
            help='Specific endpoint to test'
        )
    
    def handle(self, *args, **options):
        """Run WebSocket diagnostics"""
        host = options['host']
        port = options['port']
        session_id = options['session_id']
        endpoint = options['endpoint']
        
        self.stdout.write(
            self.style.SUCCESS("🔌 WebSocket Endpoint Diagnostics")
        )
        self.stdout.write("=" * 60)
        self.stdout.write(f"Host: {host}")
        self.stdout.write(f"Port: {port}")
        self.stdout.write(f"Session ID: {session_id}")
        self.stdout.write("")
        
        # Available endpoints from the codebase analysis
        endpoints = {
            'chat': f'ws://{host}:{port}/ws/chat/{session_id}/',
            'health': f'ws://{host}:{port}/ws/health/',
            'assistant': f'ws://{host}:{port}/ws/assistant/deepseek_chat/{session_id}/',
            'ai_stream': f'ws://{host}:{port}/ws/ai/stream/{session_id}/',
            'root': f'ws://{host}:{port}/',
        }
        
        if endpoint == 'all':
            test_endpoints = endpoints
        else:
            test_endpoints = {endpoint: endpoints.get(endpoint)}
        
        # Run tests
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for name, url in test_endpoints.items():
                if url:
                    self.stdout.write(f"\n🧪 Testing {name.upper()} endpoint:")
                    self.stdout.write(f"URL: {url}")
                    result = loop.run_until_complete(self.test_endpoint(url, name))
                    if result:
                        self.stdout.write(self.style.SUCCESS(f"✅ {name} - Connection successful"))
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ {name} - Connection failed"))
        finally:
            loop.close()
        
        # Provide frontend guidance
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🚀 Frontend Integration Guide"))
        self.stdout.write("=" * 60)
        
        self.stdout.write("\n📋 Available WebSocket Endpoints:")
        for name, url in endpoints.items():
            self.stdout.write(f"  • {name}: {url}")
        
        self.stdout.write(f"\n💡 Frontend WebSocket Connection Code:")
        self.stdout.write(f"""
// Primary Chat Endpoint (Enhanced)
const chatWs = new WebSocket('ws://{host}:{port}/ws/chat/{session_id}/');

// Connection event handlers
chatWs.onopen = (event) => {{
    console.log('🔌 WebSocket Connected:', event);
    // Send initial message
    chatWs.send(JSON.stringify({{
        type: 'connection_ack',
        session_id: '{session_id}'
    }}));
}};

chatWs.onmessage = (event) => {{
    console.log('📨 Message received:', event.data);
    const data = JSON.parse(event.data);
    // Handle different message types
    switch(data.type) {{
        case 'connection_ack':
            console.log('✅ Connection acknowledged');
            break;
        case 'chat_response':
            console.log('💬 Chat response:', data.message);
            break;
        case 'error':
            console.error('❌ Error:', data.message);
            break;
    }}
}};

chatWs.onclose = (event) => {{
    console.log('🔌 WebSocket Closed:', event.code, event.reason);
}};

chatWs.onerror = (error) => {{
    console.error('🚨 WebSocket Error:', error);
}};

// Send chat message
function sendChatMessage(message) {{
    chatWs.send(JSON.stringify({{
        type: 'chat_message',
        message: message,
        session_id: '{session_id}',
        timestamp: new Date().toISOString()
    }}));
}}
""")
        
        self.stdout.write(f"\n🔧 Common Issues & Solutions:")
        self.stdout.write("""
1. ❌ WebSocket not initialized:
   - Ensure Daphne server is running (not Django dev server)
   - Check that port 8000 is accessible
   - Verify WebSocket URL format

2. ❌ Connection refused:
   - Make sure backend is running: daphne promptcraft.asgi:application
   - Check firewall/proxy settings
   - Verify CORS settings allow WebSocket connections

3. ❌ Authentication issues:
   - WebSocket auth is handled differently than HTTP
   - Use query parameters or connection headers for JWT
   - Anonymous connections are allowed for testing

4. ❌ Message format issues:
   - Ensure JSON format for all messages
   - Include required fields: type, session_id
   - Check message type handlers on backend
""")
        
        self.stdout.write(f"\n✨ Next Steps:")
        self.stdout.write(f"""
1. Test connection manually: wscat -c ws://{host}:{port}/ws/chat/{session_id}/
2. Update your frontend to use: ws://{host}:{port}/ws/chat/{{session_id}}/
3. Implement proper error handling and reconnection logic
4. Add authentication if needed for production
""")
    
    async def test_endpoint(self, url, endpoint_name):
        """Test a single WebSocket endpoint"""
        try:
            # Set connection timeout
            async with websockets.connect(
                url, 
                timeout=10,
                ping_interval=None  # Disable ping for testing
            ) as websocket:
                
                # Send test message based on endpoint type
                if 'chat' in endpoint_name:
                    test_message = {
                        "type": "ping",
                        "session_id": "test_session_123",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                else:
                    test_message = {
                        "type": "ping",
                        "message": "test"
                    }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    self.stdout.write(f"  📨 Response: {response[:100]}...")
                    return True
                except asyncio.TimeoutError:
                    self.stdout.write(f"  ⏰ Response timeout (connection works, no response)")
                    return True  # Connection works even if no response
                    
        except (ConnectionRefusedError, OSError, Exception) as e:
            if "Connection refused" in str(e) or "connection failed" in str(e).lower():
                self.stdout.write(f"  ❌ Connection refused - server not running?")
            else:
                self.stdout.write(f"  ❌ Error: {str(e)}")
            return False