#!/usr/bin/env python
"""
Quick test to verify Django server and WebSocket routing is working
"""

import asyncio
import websockets
import json
import sys
import requests
from urllib.parse import urlparse

async def test_basic_websocket():
    """Test basic WebSocket connection to see if routing works"""
    print("🔍 Testing basic WebSocket connection...")
    
    session_id = "test123"
    url = f"ws://localhost:8000/ws/templates/{session_id}/"
    
    try:
        print(f"🔗 Connecting to: {url}")
        
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for connection message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📨 Received: {data.get('type', 'unknown')}")
                
                if 'capabilities' in data:
                    capabilities = data['capabilities']
                    print(f"📋 Capabilities: {capabilities}")
                    
                    # Check for RAG capabilities
                    rag_caps = [cap for cap in capabilities if 'rag' in cap.lower()]
                    if rag_caps:
                        print(f"✅ RAG capabilities found: {rag_caps}")
                    else:
                        print("⚠️ No RAG capabilities detected")
                
                return True
                
            except asyncio.TimeoutError:
                print("⏰ No message received within timeout")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_django_server():
    """Test if Django server is running"""
    print("🌐 Testing Django server...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Django server is running (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Django server is not running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error checking Django server: {e}")
        return False

async def main():
    """Main test function"""
    print("RAG WebSocket Quick Test")
    print("=" * 25)
    
    # First check if Django server is running
    if not test_django_server():
        print("\n💡 Please start the Django server first:")
        print("   python manage.py runserver")
        return 1
    
    print()
    
    # Test WebSocket connection
    if await test_basic_websocket():
        print("\n✅ Basic WebSocket functionality is working!")
        print("\n🧪 Now you can run the full test suite:")
        print("   python test_rag_websocket.py")
        return 0
    else:
        print("\n❌ WebSocket connection failed!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if ASGI/Daphne is configured properly")
        print("2. Verify WebSocket routing in urls.py")
        print("3. Check Django settings for CHANNEL_LAYERS")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)