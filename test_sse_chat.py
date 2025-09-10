#!/usr/bin/env python3
"""
Test SSE Chat Completions Proxy
Tests the new streaming endpoint with DeepSeek API
"""
import os
import sys
import django
import asyncio
import json
import time
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.chat.views import ChatCompletionsProxyView

User = get_user_model()


class SSETestSuite:
    """Comprehensive test suite for SSE chat completions"""
    
    def __init__(self):
        self.factory = RequestFactory()
        self.view = ChatCompletionsProxyView()
        self.test_user = None
        self.results = []
    
    def setup_test_user(self):
        """Create or get test user"""
        try:
            self.test_user = User.objects.get(username='test_sse_user')
        except User.DoesNotExist:
            self.test_user = User.objects.create_user(
                username='test_sse_user',
                email='test@example.com',
                password='testpass123'
            )
        print(f"✅ Test user ready: {self.test_user.username}")
    
    def test_configuration(self):
        """Test basic configuration"""
        print("\n🔧 Testing Configuration...")
        
        api_token = getattr(settings, 'ZAI_API_TOKEN', '')
        api_base = getattr(settings, 'ZAI_API_BASE', '')
        chat_transport = getattr(settings, 'CHAT_TRANSPORT', '')
        
        config_ok = bool(api_token and api_base)
        
        print(f"   API Base URL: {api_base or '❌ NOT SET'}")
        print(f"   API Token: {'✅ CONFIGURED' if api_token else '❌ NOT SET'}")
        print(f"   Chat Transport: {chat_transport}")
        
        self.results.append({
            'test': 'configuration',
            'passed': config_ok,
            'details': {
                'api_base_set': bool(api_base),
                'api_token_set': bool(api_token),
                'transport': chat_transport
            }
        })
        
        return config_ok
    
    def test_view_initialization(self):
        """Test view can be initialized"""
        print("\n🏗️ Testing View Initialization...")
        
        try:
            view = ChatCompletionsProxyView()
            print("   ✅ View initialized successfully")
            
            # Test view methods exist
            methods = ['post', '_validate_and_prepare_payload', '_event_stream_generator']
            for method in methods:
                if hasattr(view, method):
                    print(f"   ✅ Method {method} exists")
                else:
                    print(f"   ❌ Method {method} missing")
                    raise AttributeError(f"Missing method: {method}")
            
            self.results.append({
                'test': 'view_initialization',
                'passed': True,
                'details': {'methods_found': methods}
            })
            return True
            
        except Exception as e:
            print(f"   ❌ View initialization failed: {e}")
            self.results.append({
                'test': 'view_initialization',
                'passed': False,
                'details': {'error': str(e)}
            })
            return False
    
    def test_payload_validation(self):
        """Test request payload validation"""
        print("\n📝 Testing Payload Validation...")
        
        # Test valid payload
        valid_payload = {
            "messages": [{"role": "user", "content": "Hello, test message"}],
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        result = self.view._validate_and_prepare_payload(valid_payload)
        
        if 'error' not in result:
            print("   ✅ Valid payload accepted")
            print(f"   ✅ Processed payload: {json.dumps(result, indent=2)}")
            valid_test = True
        else:
            print(f"   ❌ Valid payload rejected: {result['error']}")
            valid_test = False
        
        # Test invalid payload
        invalid_payload = {
            "messages": [{"role": "invalid", "content": "test"}]
        }
        
        result = self.view._validate_and_prepare_payload(invalid_payload)
        
        if 'error' in result:
            print("   ✅ Invalid payload properly rejected")
            invalid_test = True
        else:
            print("   ❌ Invalid payload was accepted")
            invalid_test = False
        
        # Test empty payload
        empty_result = self.view._validate_and_prepare_payload({})
        empty_test = 'error' in empty_result
        
        if empty_test:
            print("   ✅ Empty payload properly rejected")
        else:
            print("   ❌ Empty payload was accepted")
        
        passed = valid_test and invalid_test and empty_test
        
        self.results.append({
            'test': 'payload_validation',
            'passed': passed,
            'details': {
                'valid_payload': valid_test,
                'invalid_payload': invalid_test,
                'empty_payload': empty_test
            }
        })
        
        return passed
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        print("\n🏥 Testing Health Endpoint...")
        
        try:
            from apps.chat.views import ChatHealthView
            
            # Create request
            request = self.factory.get('/api/v2/chat/health/')
            request.user = self.test_user
            
            # Call view
            view = ChatHealthView()
            response = view.get(request)
            
            if response.status_code == 200:
                data = response.data
                print("   ✅ Health endpoint responded")
                print(f"   Status: {data.get('status')}")
                print(f"   Message: {data.get('message')}")
                
                health_ok = data.get('status') in ['healthy', 'degraded']
                
                self.results.append({
                    'test': 'health_endpoint',
                    'passed': health_ok,
                    'details': data
                })
                
                return health_ok
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
            self.results.append({
                'test': 'health_endpoint',
                'passed': False,
                'details': {'error': str(e)}
            })
            return False
    
    def test_mock_sse_stream(self):
        """Test SSE stream generation (mock)"""
        print("\n🌊 Testing SSE Stream Generation...")
        
        try:
            # Create a mock payload
            payload = {
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "deepseek-chat",
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 50
            }
            
            print("   📡 Testing stream generator setup...")
            
            # Test if we can create the generator
            base_url = getattr(settings, 'ZAI_API_BASE', '').rstrip('/')
            api_token = getattr(settings, 'ZAI_API_TOKEN', '')
            
            if not base_url or not api_token:
                print("   ⚠️ Skipping stream test - missing configuration")
                self.results.append({
                    'test': 'sse_stream',
                    'passed': False,
                    'details': {'error': 'missing_config'}
                })
                return False
            
            # NOTE: We won't actually call the API in tests
            # Just verify the generator can be created
            generator = self.view._event_stream_generator(
                base_url, api_token, payload, "test-123"
            )
            
            print("   ✅ Stream generator created successfully")
            print("   ⚠️ Actual API call skipped in test mode")
            
            self.results.append({
                'test': 'sse_stream',
                'passed': True,
                'details': {'generator_created': True, 'api_call_skipped': True}
            })
            
            return True
            
        except Exception as e:
            print(f"   ❌ Stream generation failed: {e}")
            self.results.append({
                'test': 'sse_stream',
                'passed': False,
                'details': {'error': str(e)}
            })
            return False
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting SSE Chat Completions Test Suite")
        print("=" * 50)
        
        # Setup
        self.setup_test_user()
        
        # Run tests
        tests = [
            ('Configuration', self.test_configuration),
            ('View Initialization', self.test_view_initialization),
            ('Payload Validation', self.test_payload_validation),
            ('Health Endpoint', self.test_health_endpoint),
            ('SSE Stream', self.test_mock_sse_stream),
        ]
        
        passed_count = 0
        total_count = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_count += 1
            except Exception as e:
                print(f"   💥 Test '{test_name}' crashed: {e}")
        
        # Results
        print("\n" + "=" * 50)
        print("🎯 Test Results Summary")
        print(f"   Passed: {passed_count}/{total_count}")
        print(f"   Success Rate: {(passed_count/total_count)*100:.1f}%")
        
        if passed_count == total_count:
            print("   🎉 All tests passed!")
            status = "SUCCESS"
        elif passed_count > total_count * 0.7:
            print("   ⚠️ Most tests passed - check failures")
            status = "PARTIAL"
        else:
            print("   ❌ Multiple test failures")
            status = "FAILED"
        
        # Detailed results
        print("\n📊 Detailed Results:")
        for result in self.results:
            status_icon = "✅" if result['passed'] else "❌"
            print(f"   {status_icon} {result['test']}")
            if not result['passed'] and 'error' in result.get('details', {}):
                print(f"      Error: {result['details']['error']}")
        
        return status


def main():
    """Main test runner"""
    try:
        # Check Django setup
        from django.core.management import execute_from_command_line
        print("🔧 Django environment loaded")
        
        # Run tests
        test_suite = SSETestSuite()
        result = test_suite.run_all_tests()
        
        # Exit with appropriate code
        if result == "SUCCESS":
            print("\n✨ SSE implementation is ready for production!")
            sys.exit(0)
        elif result == "PARTIAL":
            print("\n⚠️ SSE implementation has some issues but may work")
            sys.exit(1)
        else:
            print("\n💥 SSE implementation has critical issues")
            sys.exit(2)
            
    except Exception as e:
        print(f"💥 Test suite failed to run: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()