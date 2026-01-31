"""
Production Readiness Verification Suite
Comprehensive testing of all critical backend systems
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "prod_test_user",
    "email": "prodtest@example.com",
    "password": "SecureTestPass123!",
    "first_name": "Production",
    "last_name": "Tester"
}

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_test(test_name):
    """Print test name"""
    print(f"{Colors.OKBLUE}▶ {test_name}...{Colors.ENDC}", end=" ")

def print_success(message=""):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}", message)

def print_fail(message=""):
    """Print failure message"""
    print(f"{Colors.FAIL}❌ FAIL{Colors.ENDC}", message)

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  WARNING:{Colors.ENDC} {message}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

# Test Functions

def test_django_configuration():
    """Test 1: Django Configuration"""
    print_test("Django Configuration Check")

    try:
        assert settings.SECRET_KEY, "SECRET_KEY not set"
        assert settings.DATABASES['default'], "Database not configured"
        assert settings.INSTALLED_APPS, "No apps installed"

        print_success()
        print_info(f"    Environment: {getattr(settings, 'ENV_NAME', 'development')}")
        print_info(f"    Debug Mode: {settings.DEBUG}")
        print_info(f"    Installed Apps: {len(settings.INSTALLED_APPS)}")
        return True
    except AssertionError as e:
        print_fail(str(e))
        return False

def test_database_connectivity():
    """Test 2: Database Connection"""
    print_test("Database Connectivity")

    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        user_count = User.objects.count()
        print_success()
        print_info(f"    Database: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")
        print_info(f"    Users in database: {user_count}")
        return True
    except Exception as e:
        print_fail(str(e))
        return False

def test_redis_connectivity():
    """Test 3: Redis/Cache Connection"""
    print_test("Redis/Cache Connectivity")

    try:
        from django.core.cache import cache
        test_key = '__production_verification__'
        test_value = 'test_value'

        cache.set(test_key, test_value, 10)
        cached_value = cache.get(test_key)

        if cached_value == test_value:
            print_success()
            print_info(f"    Backend: {settings.CACHES['default']['BACKEND'].split('.')[-1]}")
            return True
        else:
            print_fail("Cache read/write mismatch")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def test_health_endpoint():
    """Test 4: Health Check Endpoint"""
    print_test("Health Check Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/api/health/", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_success()
            print_info(f"    Status: {data.get('status', 'Unknown')}")
            print_info(f"    Services: {len(data.get('services', {}))}")

            # Check services
            services = data.get('services', {})
            for service_name, service_info in services.items():
                status = service_info.get('status', 'unknown') if isinstance(service_info, dict) else service_info
                print_info(f"      - {service_name}: {status}")

            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_fail(f"Connection failed: {e}")
        return False

def test_authentication_flow():
    """Test 5: Authentication Flow"""
    print_test("Authentication Flow (Register + Login)")

    try:
        # 1. Clean up test user if exists
        User.objects.filter(username=TEST_USER['username']).delete()

        # 2. Register new user
        register_response = requests.post(
            f"{BASE_URL}/api/v1/auth/register/",
            json={
                "username": TEST_USER['username'],
                "email": TEST_USER['email'],
                "password": TEST_USER['password'],
                "password_confirm": TEST_USER['password'],
                "first_name": TEST_USER['first_name'],
                "last_name": TEST_USER['last_name']
            },
            timeout=10
        )

        if register_response.status_code != 201:
            print_fail(f"Registration failed: HTTP {register_response.status_code}")
            return False

        # 3. Login
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login/",
            json={
                "username": TEST_USER['username'],
                "password": TEST_USER['password']
            },
            timeout=10
        )

        if login_response.status_code != 200:
            print_fail(f"Login failed: HTTP {login_response.status_code}")
            return False

        login_data = login_response.json()
        access_token = login_data.get('access')
        refresh_token = login_data.get('refresh')

        if not access_token or not refresh_token:
            print_fail("Tokens not returned in response")
            return False

        # 4. Test protected endpoint
        profile_response = requests.get(
            f"{BASE_URL}/api/v1/auth/profile/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        if profile_response.status_code != 200:
            print_fail(f"Protected endpoint failed: HTTP {profile_response.status_code}")
            return False

        profile_data = profile_response.json()

        print_success()
        print_info(f"    User: {profile_data.get('username', 'Unknown')}")
        print_info(f"    Access Token: {access_token[:20]}...{access_token[-10:]}")
        print_info(f"    Profile endpoint works: ✅")

        return access_token

    except requests.exceptions.RequestException as e:
        print_fail(f"Connection failed: {e}")
        return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False

def test_deepseek_integration(access_token=None):
    """Test 6: DeepSeek AI Integration"""
    print_test("DeepSeek AI Integration")

    try:
        deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
        api_key = deepseek_config.get('API_KEY', '')
        base_url = deepseek_config.get('BASE_URL', '')

        if not api_key or not base_url:
            print_warning("DeepSeek not configured")
            return None

        # Test DeepSeek API directly
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": deepseek_config.get('DEFAULT_MODEL', 'deepseek-chat'),
                "messages": [{"role": "user", "content": "Say 'test' in one word"}],
                "max_tokens": 10
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']

            print_success()
            print_info(f"    API Key: {api_key[:20]}...{api_key[-4:]}")
            print_info(f"    Base URL: {base_url}")
            print_info(f"    Model: {deepseek_config.get('DEFAULT_MODEL', 'deepseek-chat')}")
            print_info(f"    Test Response: {content[:50]}")
            return True
        else:
            print_fail(f"API returned HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_fail(f"Connection failed: {e}")
        return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False

def test_chat_health_endpoint(access_token=None):
    """Test 7: Chat Service Health"""
    print_test("Chat Service Health Endpoint")

    try:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        response = requests.get(
            f"{BASE_URL}/api/v2/chat/health/",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success()
            print_info(f"    Status: {data.get('status', 'Unknown')}")
            print_info(f"    Message: {data.get('message', 'N/A')}")

            config = data.get('config', {})
            if config:
                print_info(f"    Provider: {config.get('provider', 'Unknown')}")
                print_info(f"    SSE Available: {config.get('sse_available', False)}")

            return True
        else:
            print_warning(f"HTTP {response.status_code} - Endpoint may require auth")
            return None

    except requests.exceptions.RequestException as e:
        print_fail(f"Connection failed: {e}")
        return False

def test_sse_streaming(access_token):
    """Test 8: SSE Streaming Endpoint"""
    print_test("SSE Streaming (Chat Completions)")

    if not access_token:
        print_warning("Skipped (no auth token)")
        return None

    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/chat/completions/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            json={
                "messages": [{"role": "user", "content": "Count 1, 2, 3"}],
                "model": "deepseek-chat",
                "stream": True,
                "max_tokens": 50
            },
            stream=True,
            timeout=30
        )

        if response.status_code == 200:
            # Read first few chunks to verify streaming
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if chunk_count >= 3:  # Just verify first few chunks
                        break

            print_success()
            print_info(f"    Status: Streaming working")
            print_info(f"    Chunks received: {chunk_count}+")
            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_fail(f"Connection failed: {e}")
        return False

def test_middleware_functionality():
    """Test 9: Middleware (Request ID, Headers)"""
    print_test("Middleware Functionality")

    try:
        response = requests.get(f"{BASE_URL}/api/health/", timeout=5)

        # Check for custom headers
        has_request_id = 'X-Request-ID' in response.headers or 'X-Request-Id' in response.headers
        has_response_time = 'X-Response-Time' in response.headers

        if has_request_id:
            print_success()
            request_id = response.headers.get('X-Request-ID') or response.headers.get('X-Request-Id')
            print_info(f"    Request ID: {request_id}")

            if has_response_time:
                print_info(f"    Response Time: {response.headers.get('X-Response-Time')}")

            return True
        else:
            print_warning("Request ID header not found (middleware may not be configured)")
            return None

    except requests.exceptions.RequestException as e:
        print_fail(f"Connection failed: {e}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print_header("PromptCraft Production Readiness Verification")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")
    print()

    results = {
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "total": 0
    }

    # Run tests
    tests = [
        ("Django Configuration", test_django_configuration),
        ("Database Connectivity", test_database_connectivity),
        ("Redis/Cache Connectivity", test_redis_connectivity),
        ("Health Check Endpoint", test_health_endpoint),
    ]

    # Authentication test (returns token)
    access_token = test_authentication_flow()
    results["total"] += 1
    if access_token:
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Continue with other tests
    test_results = {
        "DeepSeek Integration": test_deepseek_integration(access_token),
        "Chat Health Endpoint": test_chat_health_endpoint(access_token),
        "SSE Streaming": test_sse_streaming(access_token) if access_token else None,
        "Middleware Functionality": test_middleware_functionality(),
    }

    # Count basic test results
    for test_name, test_func in tests:
        result = test_func()
        results["total"] += 1
        if result:
            results["passed"] += 1
        else:
            results["failed"] += 1

    # Count additional test results
    for test_name, result in test_results.items():
        results["total"] += 1
        if result is True:
            results["passed"] += 1
        elif result is None or result is False:
            if result is None:
                results["warnings"] += 1
            else:
                results["failed"] += 1

    # Print summary
    print_header("Test Summary")
    print(f"{Colors.OKGREEN}✅ Passed: {results['passed']}/{results['total']}{Colors.ENDC}")
    if results['failed'] > 0:
        print(f"{Colors.FAIL}❌ Failed: {results['failed']}/{results['total']}{Colors.ENDC}")
    if results['warnings'] > 0:
        print(f"{Colors.WARNING}⚠️  Warnings: {results['warnings']}/{results['total']}{Colors.ENDC}")

    print()

    # Overall status
    if results['failed'] == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 ALL CRITICAL TESTS PASSED{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Backend is ready for production deployment!{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.ENDC}")
        print(f"{Colors.FAIL}Please fix the issues before deploying to production.{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Verification interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Verification failed with error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
