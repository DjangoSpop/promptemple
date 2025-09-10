"""
Smoke tests for critical system functionality
Tests public endpoints, auth flow, and RAG service status
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

User = get_user_model()


class PublicEndpointsSmokeTest(TestCase):
    """Test public endpoints that should never require auth or sessions"""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoint(self):
        """Test /health/ endpoint - should always return 200"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
    
    def test_health_detailed_endpoint(self):
        """Test /health/detailed/ endpoint"""
        response = self.client.get('/api/v2/core/health/detailed/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
    
    def test_config_endpoint(self):
        """Test /api/v2/core/config/ endpoint"""
        response = self.client.get('/api/v2/core/config/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('env', data)
        self.assertIn('features', data)
        self.assertIn('rag', data['features'])
    
    def test_rag_status_endpoint(self):
        """Test RAG status endpoint"""
        response = self.client.get('/api/v2/core/rag/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('feature_enabled', data)
        self.assertIn('service_ready', data)


class AuthenticationSmokeTest(TestCase):
    """Test JWT authentication flow"""
    
    def setUp(self):
        self.client = Client()
        self.username = 'testuser'
        self.password = 'testpass123'
        
        # Create test user
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email='test@example.com'
        )
    
    def test_login_returns_jwt(self):
        """Test that login returns JWT tokens without session dependency"""
        login_data = {
            'username': self.username,
            'password': self.password
        }
        
        response = self.client.post(
            '/api/v2/auth/login/',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        # Should return 200 with JWT tokens
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
    
    def test_protected_endpoint_without_token(self):
        """Test that protected endpoints properly reject requests without tokens"""
        response = self.client.get('/api/v2/core/notifications/')
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
    
    def test_protected_endpoint_with_token(self):
        """Test that protected endpoints work with valid JWT"""
        # Login to get token
        login_response = self.client.post(
            '/api/v2/auth/login/',
            data=json.dumps({
                'username': self.username,
                'password': self.password
            }),
            content_type='application/json'
        )
        
        token = login_response.json()['access']
        
        # Use token for protected endpoint
        response = self.client.get(
            '/api/v2/core/notifications/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should return 200
        self.assertEqual(response.status_code, 200)


class RAGServiceSmokeTest(TestCase):
    """Test RAG service functionality"""
    
    def test_rag_service_import(self):
        """Test that RAG service can be imported without crashing"""
        try:
            from apps.templates.rag.services import get_langchain_service, langchain_status
            
            # Get service status
            status = langchain_status()
            self.assertIsInstance(status, dict)
            self.assertIn('feature_enabled', status)
            
            # Try to get service (may return None if disabled)
            service = get_langchain_service()
            # This is OK - service can be None if FEATURE_RAG=0
            
        except Exception as e:
            self.fail(f"RAG service import failed: {e}")
    
    def test_rag_service_graceful_degradation(self):
        """Test that RAG service degrades gracefully when unavailable"""
        from apps.ai_services.rag_service import get_rag_agent
        
        try:
            agent = get_rag_agent()
            self.assertIsNotNone(agent)
            
            # Agent should handle missing service gracefully
            self.assertTrue(hasattr(agent, 'service_available'))
            
        except Exception as e:
            self.fail(f"RAG agent creation failed: {e}")


def run_smoke_tests():
    """Run all smoke tests and return results"""
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(PublicEndpointsSmokeTest))
    suite.addTests(loader.loadTestsFromTestCase(AuthenticationSmokeTest))
    suite.addTests(loader.loadTestsFromTestCase(RAGServiceSmokeTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 Running smoke tests...")
    success = run_smoke_tests()
    
    if success:
        print("✅ All smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some smoke tests failed!")
        sys.exit(1)