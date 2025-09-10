#!/usr/bin/env python3
"""
Manual HTTP Test for SSE Chat Completions
Tests the SSE endpoint with actual HTTP requests
"""
import requests
import json
import time
import os
from typing import Dict, Any

def get_auth_token() -> str:
    """Get or create an auth token for testing"""
    # This would normally come from your frontend login
    # For testing, you'd need to either:
    # 1. Create a test user and get their JWT token
    # 2. Use an existing token
    # For now, return a placeholder
    return "your-jwt-token-here"

def test_health_endpoint():
    """Test the health endpoint"""
    print("🏥 Testing Chat Health Endpoint...")
    
    try:
        headers = {
            'Authorization': f'Bearer {get_auth_token()}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'http://localhost:8000/api/v2/chat/health/',
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"   ❌ Health check failed")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Health check error: {e}")
        return False

def test_sse_stream():
    """Test the SSE streaming endpoint"""
    print("\n🌊 Testing SSE Chat Completions...")
    
    try:
        headers = {
            'Authorization': f'Bearer {get_auth_token()}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": "Say 'Hello from SSE test!' if you can hear me."}
            ],
            "model": "deepseek-chat",
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        print(f"   📤 Sending request to /api/v2/chat/completions/")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        
        with requests.post(
            'http://localhost:8000/api/v2/chat/completions/',
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        ) as response:
            
            print(f"   📥 Response status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            
            if response.status_code != 200:
                print(f"   ❌ Request failed")
                print(f"   Response: {response.text}")
                return False
            
            print(f"   ✅ Starting to read SSE stream...")
            
            # Read SSE stream
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"   📨 {line}")
                    event_count += 1
                    
                    # Stop after reasonable number of events
                    if event_count > 20:
                        print("   ⏹️ Stopping after 20 events")
                        break
            
            duration = time.time() - start_time
            print(f"   ⏱️ Stream duration: {duration:.2f}s")
            print(f"   📊 Events received: {event_count}")
            
            return event_count > 0
            
    except Exception as e:
        print(f"   💥 SSE test error: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Manual HTTP Test for SSE Chat Completions")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:8000/health/', timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running")
        else:
            print("❌ Django server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Django server: {e}")
        print("   Make sure to run: python manage.py runserver")
        return
    
    # Get auth token
    token = get_auth_token()
    if token == "your-jwt-token-here":
        print("⚠️ Using placeholder token - you'll need a real JWT token to test")
        print("   To get a token:")
        print("   1. Create a test user via Django admin or shell")
        print("   2. Use the /api/v2/auth/login/ endpoint")
        print("   3. Copy the access token")
        print("\n   For now, testing configuration only...")
    
    # Run tests
    results = []
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    results.append(('Health Check', health_ok))
    
    # Test SSE endpoint (if token available)
    if token != "your-jwt-token-here":
        sse_ok = test_sse_stream()
        results.append(('SSE Stream', sse_ok))
    else:
        print("\n⚠️ Skipping SSE stream test - need real auth token")
        results.append(('SSE Stream', None))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 HTTP Test Results:")
    
    for test_name, result in results:
        if result is True:
            print(f"   ✅ {test_name}")
        elif result is False:
            print(f"   ❌ {test_name}")
        else:
            print(f"   ⚠️ {test_name} (skipped)")
    
    print("\n📋 Next Steps:")
    print("   1. Get a valid JWT token")
    print("   2. Test with real API requests")
    print("   3. Check server logs for any errors")
    print("   4. Test from frontend application")

if __name__ == "__main__":
    main()