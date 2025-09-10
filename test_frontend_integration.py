#!/usr/bin/env python
"""
Frontend Integration Test - WebSocket Chat Protocol
Tests the chat WebSocket connection that matches your Next.js frontend protocol
"""

import asyncio
import websockets
import json
import time
import uuid
from datetime import datetime

class ChatWebSocketTester:
    def __init__(self, url="ws://localhost:8000"):
        self.url = url
        self.session_id = str(uuid.uuid4())
        
    async def test_chat_integration(self):
        """Test the complete chat integration"""
        print("🚀 Testing Next.js Chat WebSocket Integration")
        print("=" * 50)
        
        try:
            # Connect to WebSocket
            uri = f"{self.url}/ws/chat/{self.session_id}/"
            print(f"Connecting to: {uri}")
            
            async with websockets.connect(uri) as websocket:
                print("✅ WebSocket connected successfully!")
                
                # Test 1: Connection acknowledgment
                print("\n1. Testing connection acknowledgment...")
                response = await websocket.recv()
                ack_data = json.loads(response)
                
                if ack_data.get('type') == 'connection_ack':
                    print(f"✅ Connection acknowledged")
                    print(f"   Session ID: {ack_data.get('session_id')}")
                    print(f"   Authenticated: {ack_data.get('authenticated')}")
                else:
                    print(f"⚠️ Unexpected first message: {ack_data}")
                
                # Test 2: Ping/Pong latency
                print("\n2. Testing ping/pong latency...")
                ping_start = time.time()
                await websocket.send(json.dumps({
                    'type': 'ping',
                    'timestamp': datetime.now().isoformat()
                }))
                
                pong_response = await websocket.recv()
                pong_data = json.loads(pong_response)
                latency = int((time.time() - ping_start) * 1000)
                
                if pong_data.get('type') == 'pong':
                    print(f"✅ Ping/Pong successful")
                    print(f"   Round-trip latency: {latency}ms")
                    print(f"   Server latency: {pong_data.get('latency_ms', 'N/A')}ms")
                
                # Test 3: Chat message
                print("\n3. Testing chat message...")
                test_message = "Hello! Can you help me write a professional email?"
                message_id = str(uuid.uuid4())
                
                await websocket.send(json.dumps({
                    'type': 'chat_message',
                    'message_id': message_id,
                    'content': test_message,
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Collect responses (user echo + AI response)
                responses = []
                timeout_count = 0
                max_timeout = 10  # 10 seconds max wait
                
                while len(responses) < 4 and timeout_count < max_timeout:  # Echo + typing + AI response + typing stop
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response_data = json.loads(response)
                        responses.append(response_data)
                        
                        if response_data.get('type') == 'message' and response_data.get('role') == 'user':
                            print(f"✅ User message echoed back")
                        elif response_data.get('type') == 'typing_start':
                            print(f"✅ AI typing indicator received")
                        elif response_data.get('type') == 'typing_stop':
                            print(f"✅ AI stopped typing")
                        elif response_data.get('type') == 'message' and response_data.get('role') == 'assistant':
                            print(f"✅ AI response received")
                            print(f"   Content preview: {response_data.get('content', '')[:100]}...")
                            print(f"   Processing time: {response_data.get('processing_time_ms', 'N/A')}ms")
                            break
                        elif response_data.get('type') == 'heartbeat':
                            print(f"💓 Heartbeat received")
                        
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        continue
                
                # Test 4: Intent analysis
                print("\n4. Testing intent analysis...")
                await websocket.send(json.dumps({
                    'type': 'intent_analysis',
                    'query': 'I need help creating marketing content for social media',
                    'timestamp': datetime.now().isoformat()
                }))
                
                intent_response = await websocket.recv()
                intent_data = json.loads(intent_response)
                
                if intent_data.get('type') == 'intent_result':
                    print(f"✅ Intent analysis successful")
                    print(f"   Category: {intent_data.get('category')}")
                    print(f"   Confidence: {intent_data.get('confidence')}")
                    print(f"   Keywords: {intent_data.get('keywords', [])}")
                
                # Test 5: Prompt optimization
                print("\n5. Testing prompt optimization...")
                await websocket.send(json.dumps({
                    'type': 'optimize_prompt',
                    'prompt': 'Write something good',
                    'context': {'category': 'marketing'},
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Wait for optimization result
                optimization_timeout = 0
                while optimization_timeout < 10:
                    try:
                        opt_response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        opt_data = json.loads(opt_response)
                        
                        if opt_data.get('type') == 'optimization_result':
                            print(f"✅ Prompt optimization successful")
                            print(f"   Original: {opt_data.get('original_prompt')}")
                            print(f"   Optimized: {opt_data.get('optimized_prompt', '')[:100]}...")
                            print(f"   Improvements: {len(opt_data.get('improvements', []))} suggestions")
                            break
                        elif opt_data.get('type') in ['typing_start', 'typing_stop']:
                            print(f"   {opt_data.get('type').replace('_', ' ').title()}")
                        
                    except asyncio.TimeoutError:
                        optimization_timeout += 1
                        continue
                
                # Test 6: Slash command
                print("\n6. Testing slash command...")
                await websocket.send(json.dumps({
                    'type': 'slash_command',
                    'command': 'summarize',
                    'content': 'This is a very long piece of text that needs to be summarized into key points.',
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Wait for response
                slash_timeout = 0
                while slash_timeout < 5:
                    try:
                        slash_response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        slash_data = json.loads(slash_response)
                        
                        if slash_data.get('type') == 'message' and slash_data.get('role') == 'assistant':
                            print(f"✅ Slash command processed")
                            print(f"   Response preview: {slash_data.get('content', '')[:100]}...")
                            break
                        
                    except asyncio.TimeoutError:
                        slash_timeout += 1
                        continue
                
                print(f"\n🎉 Integration test completed successfully!")
                print(f"WebSocket URL: {uri}")
                print(f"Session ID: {self.session_id}")
                
                return True
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False
    
    async def test_multiple_connections(self):
        """Test multiple simultaneous connections"""
        print("\n🔄 Testing multiple connections...")
        
        async def single_connection_test(conn_id):
            try:
                uri = f"{self.url}/ws/chat/test-{conn_id}/"
                async with websockets.connect(uri) as websocket:
                    # Send ping
                    await websocket.send(json.dumps({
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    }))
                    
                    # Wait for pong
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    await asyncio.wait_for(websocket.recv(), timeout=5.0)  # Get pong
                    
                    return True
            except Exception as e:
                print(f"Connection {conn_id} failed: {e}")
                return False
        
        # Test 3 simultaneous connections
        tasks = [single_connection_test(i) for i in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        print(f"✅ {successful}/3 simultaneous connections successful")

async def main():
    """Main test runner"""
    print("🧪 Django WebSocket Integration Test for Next.js Frontend")
    print("=" * 60)
    
    # Test with different URLs in case of port differences
    test_urls = [
        "ws://localhost:8000",  # Standard Django dev server
        "ws://localhost:8001",  # Alternative port
        "ws://127.0.0.1:8000"   # IP instead of localhost
    ]
    
    for url in test_urls:
        print(f"\n🔍 Testing connection to {url}")
        tester = ChatWebSocketTester(url)
        
        try:
            success = await tester.test_chat_integration()
            if success:
                print(f"\n✅ SUCCESS: Frontend integration working with {url}")
                
                # Test multiple connections
                await tester.test_multiple_connections()
                
                print(f"\n🎯 READY FOR PRODUCTION!")
                print(f"Your Next.js frontend should connect to: {url}/ws/chat/{{session_id}}/")
                print(f"\nUpdate your .env.local:")
                print(f"NEXT_PUBLIC_WS_URL={url}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {e}")
            continue
    
    print(f"\n❌ No WebSocket servers found. Please ensure Django is running with Daphne:")
    print(f"daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application")
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)