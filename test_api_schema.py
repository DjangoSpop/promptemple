"""
Test Script for API Endpoints after DRF Spectacular Fix
Verifies that the schema generation and API endpoints work correctly
"""
import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", expected_status=200):
    """Test a single endpoint"""
    try:
        print(f"\n✓ Testing {name}...")
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", timeout=5)
        else:
            response = requests.request(method, f"{BASE_URL}{url}", timeout=5)
        
        if response.status_code == expected_status:
            print(f"  ✅ SUCCESS: {response.status_code}")
            return True
        else:
            print(f"  ⚠️  UNEXPECTED STATUS: {response.status_code} (expected {expected_status})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ CONNECTION ERROR: Server not running on {BASE_URL}")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
        return False

def main():
    """Run all endpoint tests"""
    print("="*60)
    print("🚀 API Endpoint Tests - DRF Spectacular Fix Verification")
    print("="*60)
    
    tests = [
        # Core endpoints
        ("Health Check", "/health/", "GET", 200),
        ("Redis Health", "/health/redis/", "GET", 200),
        ("API Root", "/api/", "GET", 200),
        
        # Schema endpoints (main fix target)
        ("OpenAPI Schema", "/api/schema/", "GET", 200),
        ("Swagger UI", "/api/schema/swagger-ui/", "GET", 200),
        ("ReDoc", "/api/schema/redoc/", "GET", 200),
        
        # API v2 endpoints
        ("System Status", "/api/v2/core/status/", "GET", 200),
        ("App Config", "/api/v2/core/config/", "GET", 200),
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test_endpoint(*test):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All tests passed! API is working correctly.")
        print("\n📚 Next steps:")
        print("   1. Visit http://localhost:8000/api/schema/swagger-ui/")
        print("   2. Explore the interactive API documentation")
        print("   3. Test endpoints directly from Swagger UI")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the server logs.")
        print("\nTroubleshooting:")
        print("   1. Ensure the server is running:")
        print("      python manage.py runserver")
        print("      OR")
        print("      daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application")
        print("   2. Check for any error messages in the terminal")
        print("   3. Review DRF_SPECTACULAR_FIX.md for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
