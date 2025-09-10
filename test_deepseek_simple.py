#!/usr/bin/env python
"""
Simple DeepSeek Integration Test - Quick verification that everything works
"""

import os
import sys
import django
import asyncio
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')

# Setup Django
django.setup()

async def test_deepseek_simple():
    """Simple test to verify DeepSeek is working"""
    print("🎯 DeepSeek Simple Test")
    print("=" * 50)
    
    try:
        # Test DeepSeek service
        from apps.templates.deepseek_service import get_deepseek_service
        
        service = get_deepseek_service()
        if not service:
            print("❌ DeepSeek service not available")
            return False
            
        if not service.enabled:
            print("❌ DeepSeek service not enabled")
            return False
            
        print("✅ DeepSeek service initialized")
        print(f"   API Key: {'*' * 20}{service.config.api_key[-10:] if service.config.api_key else 'NOT_SET'}")
        print(f"   Base URL: {service.config.base_url}")
        print(f"   Model: {service.config.model_chat}")
        
        # Test simple chat
        print("\n💬 Testing simple chat...")
        messages = [{"role": "user", "content": "Say hello in one sentence"}]
        
        response = await service._make_request(messages)
        
        if response.success:
            print(f"✅ Chat successful!")
            print(f"   Response: {response.content[:100]}...")
            print(f"   Tokens: {response.tokens_used}")
            print(f"   Time: {response.response_time_ms}ms")
            return True
        else:
            print(f"❌ Chat failed: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if 'service' in locals() and service:
            await service.close()

def main():
    """Run the simple test"""
    success = asyncio.run(test_deepseek_simple())
    
    if success:
        print("\n🎉 DeepSeek is working correctly!")
        print("✅ Ready for frontend integration")
    else:
        print("\n❌ DeepSeek test failed")
        print("⚠️  Check configuration and API key")
        
    return success

if __name__ == "__main__":
    main()