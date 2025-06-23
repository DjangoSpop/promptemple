import requests
import json
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.contrib.auth import get_user_model

BASE_URL = 'http://127.0.0.1:8000'

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.access_token = None
        
    def test_endpoints(self):
        """Test all API endpoints"""
        print("🧪 Testing PromptCraft API Endpoints")
        print("=" * 50)
        
        # Test documentation endpoints
        self.test_documentation()
        
        # Test authentication
        self.test_authentication()
        
        # Test authenticated endpoints
        if self.access_token:
            self.test_authenticated_endpoints()
        
        print("\n✅ API Testing Complete!")
    
    def test_documentation(self):
        """Test API documentation endpoints"""
        print("\n📚 Testing Documentation Endpoints:")
        
        endpoints = [
            '/api/schema/',
            '/api/docs/',
            '/api/redoc/',
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                status = "✅" if response.status_code == 200 else "❌"
                print(f"   {status} {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication:")
        
        # Test registration endpoint
        try:
            response = requests.post(f"{self.base_url}/api/v1/auth/register/", 
                                   json={
                                       "username": "testuser_api",
                                       "email": "test@api.com",
                                       "password": "testpass123",
                                       "password_confirm": "testpass123"
                                   })
            status = "✅" if response.status_code in [200, 201, 400] else "❌"
            print(f"   {status} Registration - Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Registration - Error: {e}")
        
        # Test login endpoint
        try:
            response = requests.post(f"{self.base_url}/api/v1/auth/login/", 
                                   json={
                                       "username": "testuser_api",
                                       "password": "testpass123"
                                   })
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                print(f"   ✅ Login - Status: {response.status_code}")
                print(f"   🔑 Access token obtained")
            else:
                print(f"   ❌ Login - Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Login - Error: {e}")
    
    def test_authenticated_endpoints(self):
        """Test endpoints that require authentication"""
        print("\n🔒 Testing Authenticated Endpoints:")
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        endpoints = [
            '/api/v1/auth/profile/',
            '/api/v1/templates/',
            '/api/v1/ai/providers/',
            '/api/v1/gamification/achievements/',
            '/api/v1/analytics/dashboard/',
            '/api/v1/core/health/',
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
                status = "✅" if response.status_code in [200, 404] else "❌"
                print(f"   {status} {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")

def list_all_endpoints():
    """List all available API endpoints"""
    print("\n📋 All API Endpoints:")
    print("=" * 30)
    
    endpoints = {
        "Documentation": [
            "GET /api/schema/ - OpenAPI Schema",
            "GET /api/docs/ - Swagger UI",
            "GET /api/redoc/ - ReDoc UI"
        ],
        "Authentication": [
            "POST /api/v1/auth/register/ - User Registration",
            "POST /api/v1/auth/login/ - User Login",
            "POST /api/v1/auth/logout/ - User Logout",
            "POST /api/v1/auth/refresh/ - Token Refresh",
            "GET /api/v1/auth/profile/ - User Profile",
            "PUT /api/v1/auth/profile/update/ - Update Profile",
            "POST /api/v1/auth/change-password/ - Change Password"
        ],
        "Templates": [
            "GET /api/v1/templates/ - List Templates",
            "POST /api/v1/templates/ - Create Template",
            "GET /api/v1/templates/{id}/ - Template Detail",
            "PUT /api/v1/templates/{id}/ - Update Template",
            "DELETE /api/v1/templates/{id}/ - Delete Template"
        ],
        "AI Services": [
            "GET /api/v1/ai/providers/ - AI Providers",
            "GET /api/v1/ai/models/ - AI Models",
            "POST /api/v1/ai/generate/ - Generate Content",
            "GET /api/v1/ai/usage/ - Usage Statistics",
            "GET /api/v1/ai/quotas/ - Usage Quotas"
        ],
        "Gamification": [
            "GET /api/v1/gamification/achievements/ - Achievements",
            "GET /api/v1/gamification/badges/ - Badges",
            "GET /api/v1/gamification/leaderboard/ - Leaderboard",
            "GET /api/v1/gamification/daily-challenges/ - Daily Challenges",
            "GET /api/v1/gamification/user-level/ - User Level",
            "GET /api/v1/gamification/streak/ - Streak Info"
        ],
        "Analytics": [
            "GET /api/v1/analytics/dashboard/ - Analytics Dashboard",
            "GET /api/v1/analytics/user-insights/ - User Insights",
            "GET /api/v1/analytics/template-analytics/ - Template Analytics",
            "GET /api/v1/analytics/ab-tests/ - A/B Tests",
            "GET /api/v1/analytics/recommendations/ - Recommendations"
        ],
        "Core": [
            "GET /api/v1/core/health/ - Health Check",
            "GET /api/v1/core/config/ - App Configuration",
            "GET /api/v1/core/notifications/ - Notifications"
        ]
    }
    
    for category, urls in endpoints.items():
        print(f"\n{category}:")
        for url in urls:
            print(f"   {url}")

if __name__ == "__main__":
    list_all_endpoints()
    
    # Run API tests
    tester = APITester()
    tester.test_endpoints()