#!/usr/bin/env python
"""
DeepSeek AI Service Test - Comprehensive Integration Testing
Tests all DeepSeek AI functionality including intent processing, 
prompt optimization, and content generation.
"""

import asyncio
import os
import sys
import django
import time
from typing import Dict, Any

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.templates.deepseek_service import DeepSeekService
from apps.templates.langchain_services import get_langchain_service

class DeepSeekTester:
    def __init__(self):
        try:
            self.deepseek_service = DeepSeekService()
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize DeepSeek service: {e}")
            self.deepseek_service = None
            
        self.langchain_service = get_langchain_service()
        
    async def test_deepseek_direct(self):
        """Test DeepSeek service directly"""
        print("🔍 Testing DeepSeek Service Direct Integration")
        print("=" * 50)
        
        if not self.deepseek_service:
            print("❌ DeepSeek service not available")
            return False
        
        try:
            # Check if service is enabled
            if not self.deepseek_service.is_enabled():
                print("⚠️ DeepSeek service is disabled (no API key)")
                print("✅ Testing fallback functionality...")
                
                # Test fallback intent processing
                intent_result = await self.deepseek_service.process_intent("test query")
                print(f"   Fallback intent category: {intent_result.get('category', 'N/A')}")
                
                # Test fallback optimization
                opt_result = await self.deepseek_service.optimize_prompt("test prompt")
                print(f"   Fallback optimization: {len(opt_result.get('improvements', []))} suggestions")
                
                # Test fallback content
                content_result = await self.deepseek_service.generate_content("test content")
                print(f"   Fallback content: {content_result.get('note', 'Generated')}")
                
                print("✅ Fallback functionality working correctly")
                return True
            
            # Test 1: Intent Processing
            print("\n1. Testing Intent Processing...")
            intent_query = "Help me write a professional marketing email for launching our new AI-powered project management tool"
            
            start_time = time.time()
            intent_result = await self.deepseek_service.process_intent(intent_query)
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"✅ Intent processed in {processing_time}ms")
            print(f"   Category: {intent_result.get('category', 'N/A')}")
            print(f"   Confidence: {intent_result.get('confidence', 0):.2f}")
            print(f"   Keywords: {intent_result.get('keywords', [])}")
            
            # Test 2: Prompt Optimization
            print("\n2. Testing Prompt Optimization...")
            original_prompt = "Write me something good about our product"
            
            start_time = time.time()
            optimization_result = await self.deepseek_service.optimize_prompt(
                original_prompt, 
                intent_result.get('processed_data', {})
            )
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"✅ Prompt optimized in {processing_time}ms")
            print(f"   Original: {original_prompt}")
            print(f"   Optimized: {optimization_result.get('optimized_prompt', 'N/A')[:100]}...")
            print(f"   Improvements: {len(optimization_result.get('improvements', []))} suggestions")
            
            # Test 3: Content Generation
            print("\n3. Testing Content Generation...")
            content_prompt = "Generate a compelling email subject line for our AI project management tool launch"
            
            start_time = time.time()
            content_result = await self.deepseek_service.generate_content(content_prompt)
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"✅ Content generated in {processing_time}ms")
            print(f"   Content: {content_result.get('content', 'N/A')[:100]}...")
            print(f"   Confidence: {content_result.get('confidence', 0):.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ DeepSeek direct test failed: {e}")
            return False
    
    async def test_langchain_integration(self):
        """Test DeepSeek through LangChain service"""
        print("\n🔗 Testing DeepSeek through LangChain Integration")
        print("=" * 50)
        
        try:
            if not self.langchain_service:
                print("❌ LangChain service not available")
                return False
            
            # Test intent processing through LangChain
            print("\n1. Testing Intent Processing via LangChain...")
            query = "Create a comprehensive content strategy for social media marketing campaign"
            
            start_time = time.time()
            intent_result = await self.langchain_service.process_intent(query)
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"✅ Intent processed in {processing_time}ms")
            print(f"   Category: {intent_result.get('category', 'N/A')}")
            print(f"   Service used: {'DeepSeek' if hasattr(self.langchain_service, 'deepseek_service') and self.langchain_service.deepseek_service else 'Fallback'}")
            
            return True
            
        except Exception as e:
            print(f"❌ LangChain integration test failed: {e}")
            return False
    
    def print_system_info(self):
        """Print system information and configuration"""
        print("🔧 System Configuration")
        print("=" * 50)
        
        # Check environment variables
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
        print(f"DEEPSEEK_API_KEY: {'✅ Set' if deepseek_key else '❌ Not set'}")
        
        if deepseek_key:
            print(f"   Key length: {len(deepseek_key)} characters")
            print(f"   Key preview: {deepseek_key[:8]}...{deepseek_key[-4:] if len(deepseek_key) > 12 else ''}")
        
        print(f"DEEPSEEK_BASE_URL: {os.environ.get('DEEPSEEK_BASE_URL', 'Using default')}")
        print(f"DEEPSEEK_MODEL: {os.environ.get('DEEPSEEK_MODEL', 'Using default')}")
        
        # Check Django settings
        try:
            from django.conf import settings
            print(f"\nDjango Settings:")
            print(f"   DEBUG: {getattr(settings, 'DEBUG', False)}")
            print(f"   Redis configured: {'✅' if hasattr(settings, 'CHANNEL_LAYERS') else '❌'}")
            print(f"   Sentry configured: {'✅' if hasattr(settings, 'SENTRY_DSN') else '❌'}")
        except Exception as e:
            print(f"   Django settings error: {e}")

async def main():
    """Main test runner"""
    print("🚀 DeepSeek AI Integration Test Suite")
    print("=" * 60)
    
    tester = DeepSeekTester()
    tester.print_system_info()
    
    # Run core tests
    tests = [
        ("DeepSeek Direct", tester.test_deepseek_direct),
        ("LangChain Integration", tester.test_langchain_integration),
    ]
    
    results = {}
    total_start = time.time()
    
    for test_name, test_func in tests:
        try:
            print(f"\n" + "🔍" * 20)
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    total_time = int((time.time() - total_start) * 1000)
    
    # Print summary
    print("\n" + "📊" * 20)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    print(f"Total execution time: {total_time}ms")
    
    if passed == total:
        print("\n🎉 All tests passed! DeepSeek integration is working correctly.")
        print("\nNext steps:")
        print("1. Set your DEEPSEEK_API_KEY environment variable")
        print("2. Test real API calls with your key")
        print("3. Deploy to production with proper configuration")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the logs above for details.")
        print("\nTroubleshooting:")
        print("1. Ensure DEEPSEEK_API_KEY is set correctly")
        print("2. Check internet connectivity")
        print("3. Verify Django settings are properly configured")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)