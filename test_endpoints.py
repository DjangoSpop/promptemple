#!/usr/bin/env python
"""
Quick test script for the prompt optimization endpoints
Run with: python test_endpoints.py
"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000/api/templates'

def test_endpoint(endpoint, method='GET', data=None):
    """Test an endpoint and show response"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_ms:.2f}ms")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            json_data = response.json()
            print(f"Response Data:")
            print(json.dumps(json_data, indent=2)[:1000] + ('...' if len(str(json_data)) > 1000 else ''))
        else:
            print(f"Response: {response.text[:500]}")
            
        return response.status_code < 400
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("🚀 Testing Prompt Optimization Endpoints")
    print("Make sure your Django server is running on localhost:8000")
    
    tests = [
        # Check system status first
        ('/status/', 'GET', None),
        
        # Test health check
        ('/health/websocket/', 'GET', None),
        
        # Test search endpoints
        ('/search/prompts/', 'POST', {
            'query': 'professional email writing',
            'max_results': 5
        }),
        
        # Test intent processing
        ('/intent/process/', 'POST', {
            'query': 'I need help writing a business proposal',
            'session_id': 'test-session-123'
        }),
        
        # Test featured prompts
        ('/prompts/featured/', 'GET', None),
        
        # Test basic template endpoints
        ('/templates/', 'GET', None),
        ('/template-categories/', 'GET', None),
    ]
    
    results = []
    for endpoint, method, data in tests:
        success = test_endpoint(endpoint, method, data)
        results.append((endpoint, success))
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    success_count = 0
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {endpoint}")
        if success:
            success_count += 1
    
    success_rate = (success_count / len(results)) * 100 if results else 0
    print(f"\nSuccess Rate: {success_rate:.1f}% ({success_count}/{len(results)})")
    
    if success_rate >= 80:
        print("🎉 System is working well!")
    elif success_rate >= 60:
        print("⚠️  Some issues detected - check individual endpoint errors")
    else:
        print("❌ Multiple issues detected - review setup and configuration")
    
    print("\n📚 Next steps:")
    print("1. Check /api/templates/status/ for feature availability")
    print("2. Install Redis and advanced packages for full functionality")
    print("3. Run migrations: python manage.py makemigrations templates && python manage.py migrate")
    print("4. Load sample data for testing")

if __name__ == "__main__":
    main()