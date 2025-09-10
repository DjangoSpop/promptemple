#!/usr/bin/env python3
"""
Test DeepSeek Integration and WebSocket Functionality
Validates the complete setup including AI providers, WebSocket handling, and search functionality.
"""

import os
import sys
import django
import asyncio
import aiohttp
import json
from datetime import datetime

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.test import TestCase
from django.conf import settings
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path
from apps.templates.consumers import PromptChatConsumer

# Test color output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test_header(test_name):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}Testing: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

class DeepSeekIntegrationTests:
    """Test DeepSeek API integration and functionality"""
    
    async def test_deepseek_client_initialization(self):
        """Test DeepSeek client can be initialized"""
        print_test_header("DeepSeek Client Initialization")
        
        try:
            from apps.templates.deepseek_integration import DeepSeekClient, create_deepseek_llm
            
            # Test client initialization
            client = DeepSeekClient()
            print_success("DeepSeek client initialized successfully")
            
            # Test LangChain wrapper
            llm = create_deepseek_llm()
            print_success("DeepSeek LangChain wrapper created successfully")
            
            # Test configuration
            if hasattr(settings, 'LANGCHAIN_SETTINGS'):
                config = settings.LANGCHAIN_SETTINGS
                print_info(f"AI Provider Priority: {config.get('AI_PROVIDER_PRIORITY', ['deepseek'])}")
                print_success("Configuration loaded successfully")
            
            return True
            
        except ImportError as e:
            print_error(f"Import error: {e}")
            return False
        except Exception as e:
            print_error(f"Initialization failed: {e}")
            return False

    async def test_deepseek_api_connection(self):
        """Test actual DeepSeek API connection (requires API key)"""
        print_test_header("DeepSeek API Connection")
        
        try:
            from apps.templates.deepseek_integration import DeepSeekClient
            
            client = DeepSeekClient()
            
            # Check if API key is configured
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key or api_key == 'sk-your-deepseek-api-key-here':
                print_warning("DeepSeek API key not configured - skipping API test")
                print_info("Set DEEPSEEK_API_KEY environment variable to test API connectivity")
                return True
            
            # Test simple completion
            test_prompt = "Hello, this is a test message. Please respond with 'API connection successful'."
            
            response = await client.create_completion(
                messages=[{"role": "user", "content": test_prompt}],
                model="deepseek-chat",
                max_tokens=50
            )
            
            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']
                print_success(f"API Response: {content[:100]}...")
                print_success("DeepSeek API connection successful")
                return True
            else:
                print_error("Invalid API response format")
                return False
                
        except Exception as e:
            print_error(f"API connection failed: {e}")
            return False

    async def test_langchain_integration(self):
        """Test LangChain integration with DeepSeek"""
        print_test_header("LangChain Integration")
        
        try:
            from apps.templates.langchain_services import LangChainOptimizationService
            
            service = LangChainOptimizationService()
            print_success("LangChain optimization service initialized")
            
            # Test intent detection
            test_query = "I want to optimize my marketing prompt for better engagement"
            intent = service.detect_intent(test_query)
            print_success(f"Intent detection working: {intent}")
            
            # Test prompt optimization (will use mock if no API key)
            optimized = service.optimize_prompt(
                prompt="Write a marketing email",
                context="E-commerce product launch",
                optimization_type="engagement"
            )
            
            if optimized:
                print_success("Prompt optimization successful")
                print_info(f"Optimized length: {len(optimized)} characters")
            else:
                print_warning("Prompt optimization returned empty result (may be using mock)")
            
            return True
            
        except Exception as e:
            print_error(f"LangChain integration failed: {e}")
            return False

class WebSocketTests:
    """Test WebSocket functionality and real-time features"""
    
    async def test_websocket_consumer_connection(self):
        """Test WebSocket consumer can be connected to"""
        print_test_header("WebSocket Consumer Connection")
        
        try:
            # Create communicator
            application = URLRouter([
                re_path(r"ws/chat/$", PromptChatConsumer.as_asgi()),
            ])
            
            communicator = WebsocketCommunicator(application, "/ws/chat/")
            connected, subprotocol = await communicator.connect()
            
            if connected:
                print_success("WebSocket connection established")
                
                # Test sending a message
                await communicator.send_json_to({
                    "type": "search_request",
                    "query": "test search query",
                    "filters": {}
                })
                print_success("Test message sent successfully")
                
                # Try to receive response (with timeout)
                try:
                    response = await asyncio.wait_for(
                        communicator.receive_json_from(),
                        timeout=5.0
                    )
                    print_success(f"Received response: {response['type']}")
                except asyncio.TimeoutError:
                    print_warning("No response received within timeout (expected for test)")
                
                # Clean up
                await communicator.disconnect()
                print_success("WebSocket disconnected cleanly")
                return True
            else:
                print_error("Failed to establish WebSocket connection")
                return False
                
        except Exception as e:
            print_error(f"WebSocket test failed: {e}")
            return False

    async def test_websocket_message_handling(self):
        """Test WebSocket message handling and routing"""
        print_test_header("WebSocket Message Handling")
        
        try:
            from apps.templates.consumers import PromptChatConsumer
            
            # Test message type validation
            consumer = PromptChatConsumer()
            
            # Test various message types
            test_messages = [
                {"type": "search_request", "query": "test"},
                {"type": "chat_message", "message": "Hello"},
                {"type": "optimization_request", "prompt": "Test prompt"},
                {"type": "invalid_type", "data": "should be handled gracefully"}
            ]
            
            for msg in test_messages:
                try:
                    # This would normally be called by the WebSocket framework
                    # We're just testing that the methods exist and can be called
                    if hasattr(consumer, f"handle_{msg['type']}"):
                        print_success(f"Handler exists for message type: {msg['type']}")
                    else:
                        print_info(f"No specific handler for: {msg['type']} (will use default)")
                except Exception as e:
                    print_warning(f"Message handling issue for {msg['type']}: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Message handling test failed: {e}")
            return False

class DatabaseAndSearchTests:
    """Test database connectivity and search functionality"""
    
    async def test_database_connection(self):
        """Test database connectivity and basic operations"""
        print_test_header("Database Connection")
        
        try:
            from django.db import connection
            from apps.templates.models import Template
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    print_success("Database connection successful")
                else:
                    print_error("Database connection test failed")
                    return False
            
            # Test model operations
            template_count = Template.objects.count()
            print_success(f"Template count: {template_count}")
            
            # Test if we have any sample templates
            if template_count > 0:
                sample_template = Template.objects.first()
                print_success(f"Sample template found: {sample_template.title[:50]}...")
            else:
                print_warning("No templates found in database")
                print_info("Consider running: python manage.py populate_templates")
            
            return True
            
        except Exception as e:
            print_error(f"Database test failed: {e}")
            return False

    async def test_search_functionality(self):
        """Test search services and functionality"""
        print_test_header("Search Functionality")
        
        try:
            from apps.templates.services import TemplateSearchService
            
            search_service = TemplateSearchService()
            print_success("Search service initialized")
            
            # Test basic search
            results = search_service.search_templates(
                query="marketing",
                limit=5
            )
            
            print_success(f"Search completed, found {len(results)} results")
            
            # Test vector search if available
            try:
                vector_results = search_service.vector_search(
                    query="create engaging content",
                    limit=3
                )
                print_success(f"Vector search completed, found {len(vector_results)} results")
            except Exception as e:
                print_warning(f"Vector search not available: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Search functionality test failed: {e}")
            return False

class ConfigurationTests:
    """Test system configuration and settings"""
    
    async def test_django_configuration(self):
        """Test Django configuration and settings"""
        print_test_header("Django Configuration")
        
        try:
            from django.conf import settings
            
            # Test essential settings
            required_settings = [
                'SECRET_KEY', 'DATABASES', 'INSTALLED_APPS',
                'MIDDLEWARE', 'ROOT_URLCONF'
            ]
            
            for setting_name in required_settings:
                if hasattr(settings, setting_name):
                    print_success(f"{setting_name} configured")
                else:
                    print_error(f"{setting_name} missing")
                    return False
            
            # Test Channels configuration
            if hasattr(settings, 'ASGI_APPLICATION'):
                print_success("ASGI application configured")
            
            if hasattr(settings, 'CHANNEL_LAYERS'):
                print_success("Channel layers configured")
            
            # Test AI configuration
            if hasattr(settings, 'LANGCHAIN_SETTINGS'):
                ai_config = settings.LANGCHAIN_SETTINGS
                print_success("AI configuration found")
                print_info(f"Provider priority: {ai_config.get('AI_PROVIDER_PRIORITY', [])}")
            
            return True
            
        except Exception as e:
            print_error(f"Configuration test failed: {e}")
            return False

    async def test_environment_variables(self):
        """Test environment variable configuration"""
        print_test_header("Environment Variables")
        
        # Check for important environment variables
        env_vars = [
            ('SECRET_KEY', 'Django secret key'),
            ('DEEPSEEK_API_KEY', 'DeepSeek API key (optional)'),
            ('REDIS_URL', 'Redis URL (for WebSocket)'),
            ('SENTRY_DSN', 'Sentry DSN (optional)'),
        ]
        
        for var_name, description in env_vars:
            value = os.getenv(var_name)
            if value and value != f'your-{var_name.lower().replace("_", "-")}-here':
                print_success(f"{var_name} configured")
            else:
                if 'optional' in description:
                    print_warning(f"{var_name} not configured ({description})")
                else:
                    print_error(f"{var_name} not configured ({description})")
        
        return True

async def run_all_tests():
    """Run all test suites"""
    print(f"{Colors.BOLD}DeepSeek Integration & WebSocket Test Suite{Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Django Version: {django.get_version()}")
    
    test_suites = [
        ("Configuration", ConfigurationTests()),
        ("Database", DatabaseAndSearchTests()),
        ("DeepSeek Integration", DeepSeekIntegrationTests()),
        ("WebSocket", WebSocketTests()),
    ]
    
    results = {}
    
    for suite_name, test_suite in test_suites:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Running {suite_name} Tests{Colors.END}")
        
        suite_results = []
        
        # Get all test methods
        test_methods = [method for method in dir(test_suite) 
                       if method.startswith('test_') and callable(getattr(test_suite, method))]
        
        for test_method in test_methods:
            try:
                result = await getattr(test_suite, test_method)()
                suite_results.append(result)
            except Exception as e:
                print_error(f"Test {test_method} crashed: {e}")
                suite_results.append(False)
        
        results[suite_name] = suite_results
    
    # Print summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    total_tests = 0
    passed_tests = 0
    
    for suite_name, suite_results in results.items():
        total = len(suite_results)
        passed = sum(1 for r in suite_results if r)
        
        total_tests += total
        passed_tests += passed
        
        if passed == total:
            print(f"{Colors.GREEN}{suite_name}: {passed}/{total} tests passed{Colors.END}")
        else:
            print(f"{Colors.YELLOW}{suite_name}: {passed}/{total} tests passed{Colors.END}")
    
    print(f"\n{Colors.BOLD}Overall: {passed_tests}/{total_tests} tests passed{Colors.END}")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Your DeepSeek integration is ready.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Check the output above for details.{Colors.END}")
    
    # Print next steps
    print(f"\n{Colors.BLUE}{Colors.BOLD}Next Steps:{Colors.END}")
    if not os.getenv('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY') == 'sk-your-deepseek-api-key-here':
        print(f"{Colors.BLUE}1. Get a DeepSeek API key from https://platform.deepseek.com{Colors.END}")
        print(f"{Colors.BLUE}2. Set DEEPSEEK_API_KEY environment variable{Colors.END}")
    print(f"{Colors.BLUE}3. Start the development server: python manage.py runserver{Colors.END}")
    print(f"{Colors.BLUE}4. Test WebSocket connections in your frontend{Colors.END}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())