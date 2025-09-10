#!/usr/bin/env python
"""
Test script for RAG WebSocket streaming functionality
Tests the integrated RAG optimization through WebSocket connections
"""

import asyncio
import websockets
import json
import time
import uuid
from datetime import datetime

class RAGWebSocketTester:
    """Test class for RAG WebSocket streaming functionality"""
    
    def __init__(self, websocket_url="ws://localhost:8000/ws/templates/"):
        self.websocket_url = websocket_url
        self.session_id = str(uuid.uuid4())[:8]
        self.websocket = None
        
    async def connect(self):
        """Connect to WebSocket with session ID"""
        full_url = f"{self.websocket_url}{self.session_id}/"
        print(f"🔗 Connecting to: {full_url}")
        
        try:
            self.websocket = await websockets.connect(full_url)
            print("✅ WebSocket connected successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def wait_for_message(self, timeout=10):
        """Wait for a message from the WebSocket"""
        try:
            message = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=timeout
            )
            return json.loads(message)
        except asyncio.TimeoutError:
            print(f"⏰ Timeout waiting for message ({timeout}s)")
            return None
        except Exception as e:
            print(f"❌ Error receiving message: {e}")
            return None
    
    async def send_message(self, message_data):
        """Send a message to the WebSocket"""
        try:
            await self.websocket.send(json.dumps(message_data))
            print(f"📤 Sent: {message_data['type']}")
            return True
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False
    
    async def test_connection_establishment(self):
        """Test initial connection and capability detection"""
        print("\n🧪 Testing connection establishment...")
        
        # Wait for connection established message
        msg = await self.wait_for_message(5)
        if not msg:
            return False
        
        if msg.get('type') == 'connection_established':
            capabilities = msg.get('capabilities', [])
            rag_enabled = msg.get('rag_enabled', False)
            
            print(f"✅ Connection established")
            print(f"📋 Capabilities: {', '.join(capabilities)}")
            print(f"🤖 RAG enabled: {rag_enabled}")
            
            # Check for RAG capabilities
            rag_capabilities = [
                'rag_optimization',
                'streaming_optimization',
                'context_aware_enhancement'
            ]
            
            has_rag = any(cap in capabilities for cap in rag_capabilities)
            if has_rag:
                print("✅ RAG capabilities detected")
                return True
            else:
                print("⚠️ RAG capabilities not found")
                return False
        else:
            print(f"❌ Unexpected message type: {msg.get('type')}")
            return False
    
    async def test_rag_optimization(self):
        """Test non-streaming RAG optimization"""
        print("\n🧪 Testing RAG optimization (non-streaming)...")
        
        test_prompt = "Write a professional email to request a meeting with a client about project updates"
        
        message = {
            'type': 'rag_optimize',
            'prompt': test_prompt,
            'timestamp': datetime.now().isoformat()
        }
        
        if not await self.send_message(message):
            return False
        
        # Wait for processing started message
        msg = await self.wait_for_message(5)
        if msg and msg.get('type') == 'rag_processing_started':
            print("✅ RAG processing started")
        else:
            print(f"⚠️ Unexpected response: {msg}")
        
        # Wait for optimization result
        msg = await self.wait_for_message(30)
        if not msg:
            return False
        
        if msg.get('type') == 'rag_optimized':
            print("✅ RAG optimization completed")
            print(f"⏱️ Processing time: {msg.get('processing_time_ms', 0)}ms")
            print(f"📊 Confidence: {msg.get('confidence_score', 0):.2f}")
            print(f"🔧 Improvements: {len(msg.get('improvements', []))}")
            print(f"📝 Original: {test_prompt[:50]}...")
            print(f"✨ Optimized: {msg.get('optimized_prompt', '')[:100]}...")
            return True
        elif msg.get('type') == 'error':
            print(f"❌ RAG optimization error: {msg.get('message')}")
            return False
        else:
            print(f"❌ Unexpected response: {msg.get('type')}")
            return False
    
    async def test_rag_streaming(self):
        """Test streaming RAG optimization"""
        print("\n🧪 Testing RAG streaming optimization...")
        
        test_prompt = "Create a compelling marketing copy for a new AI-powered productivity app that helps remote teams collaborate better"
        
        message = {
            'type': 'rag_stream_optimize',
            'prompt': test_prompt,
            'timestamp': datetime.now().isoformat()
        }
        
        if not await self.send_message(message):
            return False
        
        # Wait for streaming started message
        msg = await self.wait_for_message(5)
        if msg and msg.get('type') == 'rag_stream_started':
            print("✅ RAG streaming started")
        else:
            print(f"⚠️ Unexpected response: {msg}")
        
        # Collect streaming chunks
        chunks = []
        chunk_count = 0
        start_time = time.time()
        
        while True:
            msg = await self.wait_for_message(10)
            if not msg:
                break
            
            msg_type = msg.get('type')
            
            if msg_type == 'rag_stream_chunk':
                chunk_count += 1
                chunk = {
                    'index': msg.get('chunk_index'),
                    'type': msg.get('chunk_type'),
                    'content': msg.get('content', ''),
                    'is_final': msg.get('is_final', False)
                }
                chunks.append(chunk)
                
                print(f"📦 Chunk {chunk_count}: {chunk['type']} - {chunk['content'][:50]}...")
                
                if chunk['is_final']:
                    print("🏁 Final chunk received")
                    break
                    
            elif msg_type == 'rag_stream_completed':
                total_chunks = msg.get('total_chunks', 0)
                processing_time = msg.get('processing_time_ms', 0)
                elapsed = int((time.time() - start_time) * 1000)
                
                print("✅ RAG streaming completed")
                print(f"📦 Total chunks: {total_chunks}")
                print(f"⏱️ Processing time: {processing_time}ms")
                print(f"🕐 Elapsed time: {elapsed}ms")
                return True
                
            elif msg_type == 'error':
                print(f"❌ RAG streaming error: {msg.get('message')}")
                return False
            
        if chunks:
            print(f"✅ Received {len(chunks)} streaming chunks")
            return True
        else:
            print("❌ No streaming chunks received")
            return False
    
    async def test_enhanced_optimize_prompt(self):
        """Test enhanced optimize_prompt with RAG options"""
        print("\n🧪 Testing enhanced optimize_prompt with RAG...")
        
        test_prompt = "Help me write a technical documentation for REST API endpoints"
        
        message = {
            'type': 'optimize_prompt',
            'prompt': test_prompt,
            'use_rag': True,
            'stream': True,
            'context': {
                'domain': 'technical_writing',
                'audience': 'developers'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if not await self.send_message(message):
            return False
        
        # Since this routes to RAG streaming, expect streaming messages
        msg = await self.wait_for_message(5)
        if msg and msg.get('type') == 'rag_stream_started':
            print("✅ Enhanced optimization routed to RAG streaming")
            
            # Wait for at least one chunk
            msg = await self.wait_for_message(10)
            if msg and msg.get('type') == 'rag_stream_chunk':
                print("✅ Streaming chunks received")
                return True
            else:
                print(f"❌ Expected chunk, got: {msg}")
                return False
        else:
            print(f"❌ Expected stream start, got: {msg}")
            return False
    
    async def test_ping_pong(self):
        """Test basic ping/pong functionality"""
        print("\n🧪 Testing ping/pong...")
        
        message = {
            'type': 'ping',
            'timestamp': datetime.now().isoformat()
        }
        
        if not await self.send_message(message):
            return False
        
        msg = await self.wait_for_message(5)
        if msg and msg.get('type') == 'pong':
            print("✅ Ping/pong working")
            return True
        else:
            print(f"❌ Expected pong, got: {msg}")
            return False
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 WebSocket connection closed")
    
    async def run_all_tests(self):
        """Run all RAG WebSocket tests"""
        print("🚀 Starting RAG WebSocket Integration Tests")
        print("=" * 50)
        
        # Connect to WebSocket
        if not await self.connect():
            return False
        
        try:
            # Test connection and capabilities
            if not await self.test_connection_establishment():
                print("❌ Connection test failed")
                return False
            
            # Test ping/pong
            if not await self.test_ping_pong():
                print("❌ Ping/pong test failed")
                return False
            
            # Test RAG optimization
            if not await self.test_rag_optimization():
                print("❌ RAG optimization test failed")
                return False
            
            # Test RAG streaming
            if not await self.test_rag_streaming():
                print("❌ RAG streaming test failed")
                return False
            
            # Test enhanced optimize_prompt
            if not await self.test_enhanced_optimize_prompt():
                print("❌ Enhanced optimize_prompt test failed")
                return False
            
            print("\n🎉 All tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            return False
        finally:
            await self.close()


async def main():
    """Main test function"""
    tester = RAGWebSocketTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ RAG WebSocket integration is working correctly!")
        return 0
    else:
        print("\n❌ RAG WebSocket integration has issues!")
        return 1


if __name__ == "__main__":
    import sys
    
    print("RAG WebSocket Integration Tester")
    print("=" * 40)
    print("This script tests the integrated RAG streaming functionality")
    print("Make sure the Django server is running on localhost:8000")
    print()
    
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)