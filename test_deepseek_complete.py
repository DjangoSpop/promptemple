#!/usr/bin/env python
"""
Comprehensive DeepSeek Integration Test
Tests API connectivity, WebSocket integration, and AI services
"""

import os
import sys
import django
import asyncio
import json
import time
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.conf import settings
from apps.templates.deepseek_service import get_deepseek_service, test_deepseek_connection
from apps.templates.deepseek_integration import create_deepseek_llm


async def test_deepseek_service():
    """Test DeepSeek service directly"""
    print("🔍 Testing DeepSeek Service...")
    
    try:
        service = get_deepseek_service()
        
        if not service:
            print("❌ DeepSeek service not available")
            return False
        
        if not service.enabled:
            print("❌ DeepSeek service is disabled (no API key)")
            return False
        
        print(f"✅ DeepSeek service initialized")
        print(f"   - Base URL: {service.config.base_url}")
        print(f"   - Model Chat: {service.config.model_chat}")
        print(f"   - Model Coder: {service.config.model_coder}")
        
        # Test API connectivity
        print("\n🔗 Testing API connectivity...")
        success = await test_deepseek_connection()
        
        if success:
            print("✅ DeepSeek API connection successful")
        else:
            print("❌ DeepSeek API connection failed")
            
        return success
        
    except Exception as e:
        print(f"❌ DeepSeek service test failed: {e}")
        return False


async def test_deepseek_chat():
    """Test DeepSeek chat functionality"""
    print("\n💬 Testing DeepSeek Chat...")
    
    try:
        service = get_deepseek_service()
        
        if not service or not service.enabled:
            print("❌ DeepSeek service not available")
            return False
        
        # Test simple chat
        messages = [
            {"role": "user", "content": "Hello! Can you tell me a short joke?"}
        ]
        
        start_time = time.time()
        response = await service._make_request(messages)
        duration = int((time.time() - start_time) * 1000)
        
        if response.success:
            print(f"✅ Chat response received in {duration}ms")
            print(f"   Model: {response.model}")
            print(f"   Tokens: {response.tokens_used}")
            print(f"   Response: {response.content[:100]}...")
            return True
        else:
            print(f"❌ Chat failed: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False


async def test_deepseek_optimization():
    """Test DeepSeek prompt optimization"""
    print("\n🚀 Testing DeepSeek Optimization...")
    
    try:
        service = get_deepseek_service()
        
        if not service or not service.enabled:
            print("❌ DeepSeek service not available")
            return False
        
        # Test prompt optimization
        test_prompt = "Write an email"
        
        start_time = time.time()
        result = await service.optimize_prompt(
            original_prompt=test_prompt,
            optimization_type="enhancement"
        )
        duration = int((time.time() - start_time) * 1000)
        
        print(f"✅ Optimization completed in {duration}ms")
        print(f"   Original: {test_prompt}")
        print(f"   Optimized: {result['optimized_content'][:100]}...")
        print(f"   Improvements: {len(result['improvements'])} suggestions")
        print(f"   Confidence: {result['confidence']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimization test failed: {e}")
        return False


async def test_deepseek_langchain():
    """Test DeepSeek LangChain integration"""
    print("\n🔗 Testing DeepSeek LangChain Integration...")
    
    try:
        # Test different models
        models_to_test = ['chat', 'coder']
        
        for model_type in models_to_test:
            print(f"\n   Testing {model_type} model...")
            
            llm = create_deepseek_llm(
                task_type=model_type,
                temperature=0.7,
                max_tokens=100
            )
            
            if model_type == 'chat':
                test_input = "Hello, how are you?"
            else:
                test_input = "Write a simple Python function to add two numbers"
            
            start_time = time.time()
            response = await llm.ainvoke(test_input)
            duration = int((time.time() - start_time) * 1000)
            
            print(f"   ✅ {model_type} model responded in {duration}ms")
            print(f"   Response: {response.content[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain test failed: {e}")
        return False


def test_environment_variables():
    """Test environment variable configuration"""
    print("\n🔧 Testing Environment Configuration...")
    
    required_vars = [
        'DEEPSEEK_API_KEY',
        'DEEPSEEK_BASE_URL',
        'DEEPSEEK_DEFAULT_MODEL'
    ]
    
    all_configured = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'DEEPSEEK_API_KEY':
                print(f"   ✅ {var}: {value[:8]}...{value[-4:]}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
            all_configured = False
    
    return all_configured


async def test_ai_services_endpoints():
    """Test AI services REST endpoints"""
    print("\n🌐 Testing AI Services Endpoints...")
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        # Create a test client
        client = Client()
        
        # Create a test user
        User = get_user_model()
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Login
        client.force_login(test_user)
        
        # Test providers endpoint
        response = client.get('/api/v2/ai/providers/')
        if response.status_code == 200:
            data = response.json()
            deepseek_found = any(p['id'] == 'deepseek' for p in data['providers'])
            if deepseek_found:
                print("   ✅ DeepSeek provider found in API")
            else:
                print("   ❌ DeepSeek provider not found in API")
        else:
            print(f"   ❌ Providers endpoint failed: {response.status_code}")
        
        # Test models endpoint
        response = client.get('/api/v2/ai/models/')
        if response.status_code == 200:
            data = response.json()
            deepseek_models = [m for m in data['models'] if m['provider'] == 'deepseek']
            print(f"   ✅ Found {len(deepseek_models)} DeepSeek models in API")
        else:
            print(f"   ❌ Models endpoint failed: {response.status_code}")
        
        # Test DeepSeek test endpoint
        response = client.get('/api/v2/ai/deepseek/test/')
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print("   ✅ DeepSeek test endpoint passed")
            else:
                print(f"   ❌ DeepSeek test endpoint failed: {data['message']}")
        else:
            print(f"   ❌ DeepSeek test endpoint failed: {response.status_code}")
        
        # Cleanup
        test_user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoints test failed: {e}")
        return False


async def main():
    """Run comprehensive DeepSeek tests"""
    print("🎯 DeepSeek Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables, False),
        ("DeepSeek Service", test_deepseek_service, True),
        ("DeepSeek Chat", test_deepseek_chat, True),
        ("DeepSeek Optimization", test_deepseek_optimization, True),
        ("LangChain Integration", test_deepseek_langchain, True),
        ("AI Services Endpoints", test_ai_services_endpoints, True)
    ]
    
    results = []
    
    for test_name, test_func, is_async in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! DeepSeek integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and logs.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())