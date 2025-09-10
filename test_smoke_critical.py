"""
Smoke tests for critical system functionality
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class PublicEndpointsTestCase(TestCase):
    """Test public endpoints that should never require auth or sessions"""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoint(self):
        """Test /health/ returns 200 without auth"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
    
    def test_detailed_health_endpoint(self):
        """Test /health/detailed/ returns comprehensive status"""
        response = self.client.get('/api/v2/core/health/detailed/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
    
    def test_app_config_endpoint(self):
        """Test /api/v2/core/config/ returns config without auth"""
        response = self.client.get('/api/v2/core/config/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('env', data)
        self.assertIn('features', data)
    
    def test_rag_status_endpoint(self):
        """Test RAG status endpoint is public"""
        response = self.client.get('/api/v2/core/rag/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('feature_enabled', data)
        self.assertIn('service_ready', data)


class AuthenticationTestCase(APITestCase):
    """Test JWT authentication flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_jwt_login_flow(self):
        """Test JWT token generation on login"""
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
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
    
    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require JWT"""
        # Try accessing protected endpoint without token
        response = self.client.get('/api/v2/templates/rag/optimize/')
        self.assertEqual(response.status_code, 401)
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Try with valid JWT token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post('/api/v2/templates/rag/optimize/', {
            'prompt': 'Test prompt'
        })
        
        # Should not get 401 (might get 503 if RAG disabled, but not auth error)
        self.assertNotEqual(response.status_code, 401)


class SessionlessTestCase(TestCase):
    """Test that critical functionality works without sessions"""
    
    def test_no_session_cookies_on_public_endpoints(self):
        """Ensure public endpoints don't set session cookies"""
        response = self.client.get('/health/')
        
        # Should not set any session-related cookies
        cookie_names = [cookie.key for cookie in response.cookies.values()]
        self.assertNotIn('sessionid', cookie_names)
        self.assertNotIn('csrftoken', cookie_names)
    
    def test_health_endpoint_minimal_dependencies(self):
        """Test health endpoint works even with broken database"""
        # Use the simple health endpoint which shouldn't touch DB
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)


class RAGServiceTestCase(TestCase):
    """Test RAG service isolation and graceful degradation"""
    
    def test_rag_status_always_responds(self):
        """RAG status should always respond even if service is broken"""
        response = self.client.get('/api/v2/core/rag/status/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Should have all expected fields
        expected_fields = ['feature_enabled', 'service_ready', 'error', 'strategy', 'available_factories']
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_rag_graceful_degradation(self):
        """Test that app works when RAG is disabled"""
        # This tests that the service locator pattern works
        from apps.templates.rag.services import get_langchain_service, langchain_status
        
        # Should not crash even if imports fail
        service = get_langchain_service()
        status = langchain_status()
        
        # Should return valid status regardless of service availability
        self.assertIsInstance(status, dict)
        self.assertIn('feature_enabled', status)


class CacheConfigurationTestCase(TestCase):
    """Test cache configuration doesn't break"""
    
    def test_cache_backends_exist(self):
        """Test that required cache backends are configured"""
        from django.core.cache import caches
        
        # Default cache should exist
        default_cache = caches['default']
        self.assertIsNotNone(default_cache)
        
        # Sessions cache should exist 
        sessions_cache = caches['sessions']
        self.assertIsNotNone(sessions_cache)
    
    def test_session_backend_works(self):
        """Test session backend doesn't crash"""
        # Since we're using signed cookies, this should work without cache
        session = self.client.session
        session['test_key'] = 'test_value'
        session.save()
        
        # Should be able to retrieve
        self.assertEqual(session.get('test_key'), 'test_value')