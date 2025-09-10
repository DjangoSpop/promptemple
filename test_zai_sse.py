"""
Test Z.AI SSE Chat Completions Endpoint
Tests the SSE streaming proxy to Z.AI API
"""
import requests
import json
import time
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/v2/chat/completions/"
HEALTH_ENDPOINT = f"{BASE_URL}/api/v2/chat/health/"

# Test credentials (you'll need to get a real JWT token)
TEST_JWT_TOKEN = "your-jwt-token-here"  # Replace with actual JWT token

def test_health_check():
    """Test chat service health"""
    print("🏥 Testing Chat Service Health...")
    
    try:
        headers = {
            "Authorization": f"Bearer {TEST_JWT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(HEALTH_ENDPOINT, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Message: {data['message']}")
            print(f"   Config: {json.dumps(data['config'], indent=2)}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_sse_streaming():
    """Test SSE streaming with Z.AI"""
    print("\n🚀 Testing Z.AI SSE Streaming...")
    
    # Test payload
    payload = {
        "model": "glm-4-32b-0414-128k",
        "messages": [
            {
                "role": "user", 
                "content": "As a marketing expert, please create an attractive slogan for my product: AI-powered chat platform."
            }
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    headers = {
        "Authorization": f"Bearer {TEST_JWT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print(f"📤 Sending request to: {CHAT_ENDPOINT}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            CHAT_ENDPOINT, 
            json=payload, 
            headers=headers, 
            stream=True,
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📑 Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.text}")
            return False
        
        # Process SSE stream
        print("\n📺 SSE Stream Output:")
        print("-" * 50)
        
        buffer = ""
        token_count = 0
        start_time = time.time()
        
        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
            if chunk:
                buffer += chunk
                
                # Process complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Parse SSE lines
                    if line.startswith('data: '):
                        data_content = line[6:]  # Remove 'data: ' prefix
                        
                        if data_content == '[DONE]':
                            print("\n🏁 Stream completed")
                            break
                        
                        try:
                            # Try to parse as JSON
                            json_data = json.loads(data_content)
                            
                            # Handle different message types
                            if 'choices' in json_data:
                                # Standard OpenAI format
                                for choice in json_data['choices']:
                                    delta = choice.get('delta', {})
                                    if 'content' in delta:
                                        print(delta['content'], end='', flush=True)
                                        token_count += 1
                            
                            elif 'token' in json_data:
                                # Custom token format
                                print(json_data['token'], end='', flush=True)
                                token_count += 1
                            
                            elif 'request_id' in json_data:
                                # Metadata
                                print(f"\n📊 Metadata: {json_data}")
                            
                        except json.JSONDecodeError:
                            # Non-JSON data
                            print(f"📄 Raw data: {data_content}")
                    
                    elif line.startswith('event: '):
                        event_type = line[7:]  # Remove 'event: ' prefix
                        print(f"\n📻 Event: {event_type}")
                    
                    elif line.startswith('id: '):
                        message_id = line[4:]  # Remove 'id: ' prefix
                        print(f"🆔 ID: {message_id}")
        
        duration = time.time() - start_time
        print(f"\n\n📈 Stream Statistics:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Tokens: {token_count}")
        print(f"   Rate: {token_count/duration:.1f} tokens/sec" if duration > 0 else "   Rate: N/A")
        
        return True
        
    except Exception as e:
        print(f"❌ SSE Streaming Error: {e}")
        return False

def test_non_streaming():
    """Test non-streaming request (should still stream internally)"""
    print("\n📝 Testing Non-Streaming Request...")
    
    payload = {
        "model": "glm-4-32b-0414-128k",
        "messages": [
            {"role": "user", "content": "Say hello in 5 words."}
        ],
        "stream": False,  # This should be overridden to True
        "max_tokens": 50
    }
    
    headers = {
        "Authorization": f"Bearer {TEST_JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, headers=headers, timeout=30)
        
        print(f"📡 Status: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            print("✅ Non-streaming request processed (as SSE stream)")
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Non-streaming test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Z.AI SSE Chat Completions Test Suite")
    print("=" * 50)
    
    # Check if JWT token is provided
    if TEST_JWT_TOKEN == "your-jwt-token-here":
        print("⚠️  Warning: Using placeholder JWT token")
        print("   For full testing, replace TEST_JWT_TOKEN with a real JWT")
        print("   Some tests may fail due to authentication")
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("SSE Streaming", test_sse_streaming),
        ("Non-Streaming Override", test_non_streaming)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Z.AI SSE integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the configuration and try again.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)