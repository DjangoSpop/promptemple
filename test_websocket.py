#!/usr/bin/env python3
"""
WebSocket connectivity test for PromptCraft backend
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    try:
        uri = 'ws://localhost:8000/ws/chat/test-session/'
        print(f'Testing WebSocket connection to: {uri}')
        
        async with websockets.connect(uri) as websocket:
            print('✓ WebSocket connection established')
            
            # Send a test message
            test_message = {
                'type': 'ping',
                'message': 'test connection'
            }
            await websocket.send(json.dumps(test_message))
            print('✓ Test message sent')
            
            # Try to receive response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f'✓ Response received: {response}')
                return True
            except asyncio.TimeoutError:
                print('⚠ No response received (timeout), but connection works')
                return True
                
    except Exception as e:
        print(f'✗ WebSocket connection failed: {e}')
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    print(f'WebSocket test result: {"PASSED" if result else "FAILED"}')
    sys.exit(0 if result else 1)