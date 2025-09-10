#!/usr/bin/env python3
"""
SSE Chat Testing Script
======================

This script tests the SSE chat implementation with real HTTP requests
to verify the complete flow works as expected.

Usage:
    python test_sse_production.py

Requirements:
    - Django server running on localhost:8000
    - Valid JWT token for authentication
    - Z.AI API properly configured
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime

class SSEChatTester:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authentication headers."""
        if not self.token:
            print("❌ No JWT token provided. Please set TOKEN environment variable.")
            sys.exit(1)
            
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'User-Agent': 'SSE-Chat-Tester/1.0'
        }
    
    async def test_health_check(self):
        """Test the health check endpoint."""
        print("🔍 Testing health check endpoint...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v2/chat/health/",
                headers={'Authorization': f'Bearer {self.token}'}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                    
                    # Print configuration details
                    if 'checks' in data:
                        for check_name, check_data in data['checks'].items():
                            status = check_data.get('status', 'unknown')
                            emoji = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"
                            print(f"  {emoji} {check_name}: {status}")
                    
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_sse_stream(self, messages, model="glm-4-32b-0414-128k"):
        """Test SSE streaming with a chat completion request."""
        print(f"🚀 Testing SSE stream with model: {model}")
        print(f"📝 Messages: {len(messages)} message(s)")
        
        payload = {
            "messages": messages,
            "model": model,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        events_received = []
        tokens_received = []
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v2/chat/completions/",
                headers=self.get_auth_headers(),
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Request failed: HTTP {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                
                print(f"✅ SSE connection established (HTTP {response.status})")
                print("📡 Streaming response...")
                
                # Read SSE stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line:
                        continue
                        
                    if line.startswith('event: '):
                        event_type = line[7:]
                        print(f"📤 Event: {event_type}")
                        continue
                        
                    if line.startswith('data: '):
                        data_str = line[6:]
                        
                        if data_str == '[DONE]':
                            print("🏁 Stream completed: [DONE] received")
                            break
                            
                        try:
                            data = json.loads(data_str)
                            events_received.append(data)
                            
                            # Handle different event types
                            if data.get('stream_start'):
                                print(f"🎬 Stream started: {data.get('trace_id', 'N/A')}")
                                
                            elif data.get('stream_complete'):
                                processing_time = data.get('processing_time_ms', 0)
                                print(f"✅ Stream completed in {processing_time}ms")
                                
                            elif data.get('choices'):
                                # OpenAI-compatible token streaming
                                choice = data['choices'][0]
                                delta = choice.get('delta', {})
                                content = delta.get('content', '')
                                
                                if content:
                                    tokens_received.append(content)
                                    print(f"🔤 Token: '{content}'", end='', flush=True)
                                    
                                finish_reason = choice.get('finish_reason')
                                if finish_reason:
                                    print(f"\n🏁 Finish reason: {finish_reason}")
                                    
                            elif data.get('error'):
                                print(f"❌ Stream error: {data['error']}")
                                return False
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Failed to parse JSON: {data_str[:100]}...")
                            continue
                
                # Calculate metrics
                total_time = time.time() - start_time
                total_tokens = len(tokens_received)
                tokens_per_second = total_tokens / total_time if total_time > 0 else 0
                
                print(f"\n📊 Stream Metrics:")
                print(f"   ⏱️  Total time: {total_time:.2f}s")
                print(f"   🔤 Tokens received: {total_tokens}")
                print(f"   🚀 Tokens/second: {tokens_per_second:.1f}")
                print(f"   📦 Events received: {len(events_received)}")
                
                # Reconstruct full response
                full_response = ''.join(tokens_received)
                if full_response:
                    print(f"\n💬 Complete Response:")
                    print(f"   {full_response}")
                
                return True
                
        except Exception as e:
            print(f"❌ SSE stream error: {e}")
            return False
    
    async def test_rate_limiting(self):
        """Test rate limiting by making multiple rapid requests."""
        print("🚦 Testing rate limiting (5 requests/minute)...")
        
        test_payload = {
            "messages": [{"role": "user", "content": "Quick test"}],
            "model": "glm-4-32b-0414-128k",
            "stream": True,
            "max_tokens": 10
        }
        
        rate_limit_hit = False
        
        for i in range(7):  # Try 7 requests (limit is 5)
            print(f"📤 Request {i+1}/7...")
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/v2/chat/completions/",
                    headers=self.get_auth_headers(),
                    json=test_payload
                ) as response:
                    
                    if response.status == 429:
                        print(f"✅ Rate limit triggered at request {i+1} (expected)")
                        rate_limit_hit = True
                        break
                    elif response.status == 200:
                        print(f"   ✅ Request {i+1} successful")
                        # Consume the stream to avoid connection issues
                        async for _ in response.content:
                            pass
                    else:
                        print(f"   ⚠️  Request {i+1} returned HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Request {i+1} error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        if rate_limit_hit:
            print("✅ Rate limiting working correctly")
            return True
        else:
            print("⚠️  Rate limiting not triggered (might need longer test)")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive test suite."""
        print("=" * 60)
        print("🧪 SSE Chat Comprehensive Test Suite")
        print("=" * 60)
        print(f"🌐 Testing endpoint: {self.base_url}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        test_results = []
        
        # 1. Health Check
        health_ok = await self.test_health_check()
        test_results.append(("Health Check", health_ok))
        print()
        
        # 2. Basic SSE Stream
        if health_ok:
            basic_stream_ok = await self.test_sse_stream([
                {"role": "user", "content": "Hello! Can you tell me a short joke?"}
            ])
            test_results.append(("Basic SSE Stream", basic_stream_ok))
            print()
            
            # 3. Conversation Stream
            if basic_stream_ok:
                conversation_ok = await self.test_sse_stream([
                    {"role": "user", "content": "What is Python?"},
                    {"role": "assistant", "content": "Python is a programming language."},
                    {"role": "user", "content": "What are its main features?"}
                ])
                test_results.append(("Conversation Stream", conversation_ok))
                print()
                
                # 4. Rate Limiting
                rate_limit_ok = await self.test_rate_limiting()
                test_results.append(("Rate Limiting", rate_limit_ok))
        
        # Summary
        print("=" * 60)
        print("📋 Test Results Summary")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            emoji = "✅" if result else "❌"
            print(f"{emoji} {test_name}")
            if result:
                passed += 1
        
        print()
        print(f"📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! SSE implementation is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
            return False

async def main():
    """Main test runner."""
    import os
    
    # Get configuration from environment
    base_url = os.getenv('BASE_URL', 'http://localhost:8000')
    token = os.getenv('JWT_TOKEN')
    
    if not token:
        print("❌ JWT_TOKEN environment variable not set.")
        print("   Please set it with: export JWT_TOKEN='your-jwt-token-here'")
        print("   You can get a token by logging into your app and checking localStorage.")
        sys.exit(1)
    
    # Run tests
    async with SSEChatTester(base_url, token) as tester:
        success = await tester.run_comprehensive_test()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)