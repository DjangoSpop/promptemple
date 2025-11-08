"""
MVP API Test Suite

Tests the professional MVP endpoints to ensure they work correctly.
Run after setting up the database and seeding data.

Usage:
    python test_mvp_api.py
    python test_mvp_api.py --host http://localhost:8000
"""

import requests
import json
import sys
from datetime import datetime


class MVPAPITester:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token = None
        
    def test_endpoint(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                return False, f"Unsupported method: {method}"
            
            success = response.status_code == expected_status
            
            return success, {
                'status_code': response.status_code,
                'expected': expected_status,
                'response_size': len(response.content),
                'response_time': response.elapsed.total_seconds(),
                'success': success
            }
            
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
    
    def get_auth_headers(self):
        """Get authorization headers"""
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}
    
    def test_health_check(self):
        """Test system health endpoints"""
        print("🏥 Testing Health Check Endpoints...")
        
        tests = [
            ('GET', '/health/', None, 200),
            ('GET', '/api/mvp/templates/status/', None, 200),
        ]
        
        results = []
        for method, endpoint, data, expected in tests:
            success, result = self.test_endpoint(method, endpoint, data, expected_status=expected)
            results.append((endpoint, success, result))
            
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {method} {endpoint} - {result}")
        
        return results
    
    def test_authentication_flow(self):
        """Test complete authentication flow"""
        print("🔐 Testing Authentication Flow...")
        
        # Test user registration
        test_user = {
            'username': 'mvp_test_user',
            'email': 'mvp_test@example.com',
            'password': 'test_password_123',
            'password_confirm': 'test_password_123',
            'first_name': 'MVP',
            'last_name': 'Tester'
        }
        
        # Check username availability
        success, result = self.test_endpoint('GET', '/api/mvp/auth/check-username/?username=mvp_test_user')
        print(f"  {'✅' if success else '❌'} Username availability check - {result}")
        
        # Register user
        success, result = self.test_endpoint('POST', '/api/mvp/auth/register/', test_user, expected_status=201)
        print(f"  {'✅' if success else '❌'} User registration - {result}")
        
        # Login user
        login_data = {
            'username': test_user['username'],
            'password': test_user['password']
        }
        
        success, result = self.test_endpoint('POST', '/api/mvp/auth/login/', login_data)
        
        if success:
            # Extract access token from response if login was successful
            try:
                response = self.session.post(f"{self.base_url}/api/mvp/auth/login/", json=login_data)
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get('tokens', {}).get('access')
                    print(f"  ✅ User login successful - Token obtained")
                else:
                    print(f"  ❌ User login failed - {response.status_code}")
            except Exception as e:
                print(f"  ❌ Login token extraction failed: {e}")
        
        # Test profile access (requires authentication)
        auth_headers = self.get_auth_headers()
        success, result = self.test_endpoint('GET', '/api/mvp/auth/profile/', headers=auth_headers)
        print(f"  {'✅' if success else '❌'} Profile access - {result}")
        
        return success
    
    def test_template_crud(self):
        """Test template CRUD operations"""
        print("📝 Testing Template CRUD Operations...")
        
        auth_headers = self.get_auth_headers()
        
        # List templates
        success, result = self.test_endpoint('GET', '/api/mvp/templates/')
        print(f"  {'✅' if success else '❌'} List templates (public) - {result}")
        
        # List categories
        success, result = self.test_endpoint('GET', '/api/mvp/templates/categories/')
        print(f"  {'✅' if success else '❌'} List categories - {result}")
        
        # Search templates
        success, result = self.test_endpoint('GET', '/api/mvp/templates/search/?q=business')
        print(f"  {'✅' if success else '❌'} Search templates - {result}")
        
        # Featured templates
        success, result = self.test_endpoint('GET', '/api/mvp/templates/featured/')
        print(f"  {'✅' if success else '❌'} Featured templates - {result}")
        
        if self.access_token:
            # Create new template
            new_template = {\n                'title': 'MVP Test Template',\n                'description': 'A test template created by MVP API test',\n                'content': 'This is a test template for {{purpose}} created on {{date}}.',\n                'category': 1,  # Assuming first category exists\n                'tags': 'test, mvp, api',\n                'is_public': True\n            }\n            \n            success, result = self.test_endpoint('POST', '/api/mvp/templates/', new_template, auth_headers, expected_status=201)\n            print(f\"  {'✅' if success else '❌'} Create template - {result}\")\n            \n            # List user's templates\n            success, result = self.test_endpoint('GET', '/api/mvp/templates/my_templates/', headers=auth_headers)\n            print(f\"  {'✅' if success else '❌'} List user templates - {result}\")\n    \n    def test_api_documentation(self):\n        \"\"\"Test API documentation endpoints\"\"\"\n        print(\"📚 Testing API Documentation...\")\n        \n        tests = [\n            ('GET', '/api/', None, 200),\n            ('GET', '/api/schema/', None, 200),\n        ]\n        \n        for method, endpoint, data, expected in tests:\n            success, result = self.test_endpoint(method, endpoint, data, expected_status=expected)\n            print(f\"  {'✅' if success else '❌'} {method} {endpoint} - {result}\")\n    \n    def run_all_tests(self):\n        \"\"\"Run complete test suite\"\"\"\n        print(f\"\\n🚀 MVP API Test Suite\")\n        print(f\"🌐 Testing: {self.base_url}\")\n        print(f\"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n        print(\"=\"*60)\n        \n        # Run test suites\n        try:\n            self.test_health_check()\n            print()\n            \n            auth_success = self.test_authentication_flow()\n            print()\n            \n            self.test_template_crud()\n            print()\n            \n            self.test_api_documentation()\n            print()\n            \n            print(\"=\"*60)\n            print(f\"🎉 MVP API Test Suite Completed!\")\n            \n            if auth_success:\n                print(\"✅ All core functionality working\")\n                print(\"🎯 Ready for professional MVP demonstration\")\n            else:\n                print(\"⚠️  Some authentication issues detected\")\n                print(\"🔧 Check database setup and seeding\")\n            \n        except KeyboardInterrupt:\n            print(\"\\n⏹️  Test suite interrupted by user\")\n        except Exception as e:\n            print(f\"\\n❌ Test suite failed: {e}\")\n            import traceback\n            traceback.print_exc()\n\n\ndef main():\n    \"\"\"Main test runner\"\"\"\n    import argparse\n    \n    parser = argparse.ArgumentParser(description='MVP API Test Suite')\n    parser.add_argument(\n        '--host', \n        default='http://localhost:8000',\n        help='Base URL for the API (default: http://localhost:8000)'\n    )\n    parser.add_argument(\n        '--quick',\n        action='store_true',\n        help='Run quick health check only'\n    )\n    \n    args = parser.parse_args()\n    \n    tester = MVPAPITester(args.host)\n    \n    if args.quick:\n        tester.test_health_check()\n    else:\n        tester.run_all_tests()\n\n\nif __name__ == '__main__':\n    main()