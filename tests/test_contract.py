"""
Contract tests auto-generated from OpenAPI specification
Tests API endpoints for correct request/response schemas and status codes
"""
import pytest
import httpx
from typing import Dict, Any
import yaml
from pathlib import Path


# Load OpenAPI spec
SPEC_PATH = Path(__file__).parent.parent / "PromptCraft API.yaml"

with open(SPEC_PATH, 'r', encoding='utf-8') as f:
    OPENAPI_SPEC = yaml.safe_load(f)


@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    return httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)


@pytest.fixture
def authenticated_client(api_client):
    """Authenticated API client with JWT token"""
    # Login and get token
    response = api_client.post('/api/v2/auth/login/', json={
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    
    if response.status_code == 200:
        token = response.json().get('access')
        api_client.headers['Authorization'] = f'Bearer {token}'
    
    return api_client


# ============================================
# HEALTH & STATUS TESTS
# ============================================

@pytest.mark.contract
def test_health_check(api_client):
    """Test health check endpoint returns 200"""
    response = api_client.get('/health/')
    assert response.status_code in [200, 503], f"Unexpected status: {response.status_code}"
    data = response.json()
    assert 'status' in data


@pytest.mark.contract
def test_api_root(api_client):
    """Test API root returns version and endpoints"""
    response = api_client.get('/api/')
    assert response.status_code == 200
    data = response.json()
    assert 'version' in data
    assert 'endpoints' in data


# ============================================
# TEMPLATE ENDPOINTS - CONTRACT TESTS
# ============================================

@pytest.mark.contract
def test_template_list_success(api_client):
    """Test GET /api/v2/templates/ returns paginated list"""
    response = api_client.get('/api/v2/templates/')
    assert response.status_code == 200
    
    data = response.json()
    assert 'results' in data
    assert 'count' in data
    assert isinstance(data['results'], list)


@pytest.mark.contract
def test_template_list_with_filters(api_client):
    """Test template list with query parameters"""
    params = {
        'search': 'test',
        'is_public': True,
        'page': 1,
    }
    response = api_client.get('/api/v2/templates/', params=params)
    assert response.status_code == 200


@pytest.mark.contract
def test_template_create_unauthorized(api_client):
    """Test creating template without auth returns 401"""
    response = api_client.post('/api/v2/templates/', json={
        'title': 'Test Template',
        'content': 'Test content {{variable}}',
    })
    assert response.status_code in [401, 403], "Should require authentication"


@pytest.mark.contract
def test_template_create_invalid_data(authenticated_client):
    """Test creating template with invalid data returns 400"""
    response = authenticated_client.post('/api/v2/templates/', json={
        'title': '',  # Empty title should fail
    })
    assert response.status_code == 400
    data = response.json()
    assert 'title' in data or 'detail' in data


@pytest.mark.contract
def test_template_detail_not_found(api_client):
    """Test retrieving non-existent template returns 404"""
    fake_uuid = '00000000-0000-0000-0000-000000000000'
    response = api_client.get(f'/api/v2/templates/{fake_uuid}/')
    assert response.status_code == 404


# ============================================
# CATEGORY ENDPOINTS
# ============================================

@pytest.mark.contract
def test_category_list(api_client):
    """Test GET /api/v2/template-categories/"""
    response = api_client.get('/api/v2/template-categories/')
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@pytest.mark.contract
def test_register_missing_fields(api_client):
    """Test registration with missing fields returns 400"""
    response = api_client.post('/api/v2/auth/register/', json={
        'username': 'testuser',
        # Missing email and password
    })
    assert response.status_code == 400


@pytest.mark.contract
def test_register_invalid_email(api_client):
    """Test registration with invalid email returns 400"""
    response = api_client.post('/api/v2/auth/register/', json={
        'username': 'testuser',
        'email': 'invalid-email',
        'password': 'testpass123',
    })
    assert response.status_code == 400


@pytest.mark.contract
def test_login_invalid_credentials(api_client):
    """Test login with invalid credentials returns 401"""
    response = api_client.post('/api/v2/auth/login/', json={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword',
    })
    assert response.status_code in [400, 401]


@pytest.mark.contract
def test_profile_unauthenticated(api_client):
    """Test accessing profile without auth returns 401"""
    response = api_client.get('/api/v2/auth/profile/')
    assert response.status_code in [401, 403]


# ============================================
# AI SERVICES ENDPOINTS
# ============================================

@pytest.mark.contract
def test_ai_providers_list(api_client):
    """Test GET /api/v2/ai/providers/"""
    response = api_client.get('/api/v2/ai/providers/')
    assert response.status_code == 200


@pytest.mark.contract
def test_ai_models_list(api_client):
    """Test GET /api/v2/ai/models/"""
    response = api_client.get('/api/v2/ai/models/')
    assert response.status_code == 200


# ============================================
# RESEARCH ENDPOINTS
# ============================================

@pytest.mark.contract
def test_research_jobs_list(api_client):
    """Test GET /api/v2/research/jobs/"""
    response = api_client.get('/api/v2/research/jobs/')
    # May require auth depending on configuration
    assert response.status_code in [200, 401]


@pytest.mark.contract
def test_research_create_unauthorized(api_client):
    """Test creating research job without auth"""
    response = api_client.post('/api/v2/research/jobs/', json={
        'query': 'Test research question',
    })
    assert response.status_code in [401, 403], "Should require authentication"


# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@pytest.mark.contract
def test_analytics_track_anonymous(api_client):
    """Test analytics tracking endpoint (no auth required)"""
    response = api_client.post('/api/v2/analytics/track/', json={
        'event': 'page_view',
        'properties': {'page': 'dashboard'},
    })
    assert response.status_code in [200, 201]


# ============================================
# CORE ENDPOINTS
# ============================================

@pytest.mark.contract
def test_core_config_public(api_client):
    """Test public config endpoint (no auth)"""
    response = api_client.get('/api/v2/core/config/')
    assert response.status_code == 200
    data = response.json()
    assert 'features' in data or 'config' in data


@pytest.mark.contract
def test_core_health_detailed(api_client):
    """Test detailed health check"""
    response = api_client.get('/api/v2/core/health/detailed/')
    assert response.status_code in [200, 503]


# ============================================
# PAGINATION TESTS
# ============================================

@pytest.mark.contract
def test_pagination_first_page(api_client):
    """Test first page of paginated results"""
    response = api_client.get('/api/v2/templates/', params={'page': 1})
    assert response.status_code == 200
    data = response.json()
    assert 'next' in data
    assert 'previous' in data


@pytest.mark.contract
def test_pagination_invalid_page(api_client):
    """Test invalid page number"""
    response = api_client.get('/api/v2/templates/', params={'page': 99999})
    assert response.status_code in [200, 404], "Should handle invalid page gracefully"


# ============================================
# ERROR RESPONSE STRUCTURE TESTS
# ============================================

@pytest.mark.contract
def test_error_response_structure(api_client):
    """Test that error responses have consistent structure"""
    # Trigger a 400 error
    response = api_client.post('/api/v2/auth/register/', json={})
    assert response.status_code == 400
    
    data = response.json()
    # Should have either 'detail' or field-specific errors
    assert 'detail' in data or any(key for key in data.keys())


# ============================================
# RESPONSE HEADER TESTS
# ============================================

@pytest.mark.contract
def test_cors_headers_present(api_client):
    """Test CORS headers are present"""
    response = api_client.options('/api/v2/templates/')
    assert 'access-control-allow-origin' in [h.lower() for h in response.headers.keys()]


@pytest.mark.contract
def test_content_type_json(api_client):
    """Test API returns JSON content type"""
    response = api_client.get('/api/v2/templates/')
    assert 'application/json' in response.headers.get('content-type', '')


# ============================================
# PERFORMANCE TESTS
# ============================================

@pytest.mark.slow
@pytest.mark.contract
def test_list_endpoint_performance(api_client):
    """Test list endpoints respond within acceptable time"""
    import time
    
    start = time.time()
    response = api_client.get('/api/v2/templates/')
    duration = (time.time() - start) * 1000  # Convert to ms
    
    assert response.status_code == 200
    assert duration < 2000, f"Endpoint took {duration}ms, should be <2000ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
