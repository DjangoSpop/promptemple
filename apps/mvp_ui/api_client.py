"""
API client utility for server-to-server API calls
Handles authentication, retries, and error parsing
"""
import httpx
import json
from typing import Optional, Dict, Any
from django.conf import settings
from urllib.parse import urljoin


class APIClient:
    """HTTP client for internal API calls with JWT auth"""
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or self._get_base_url()
        self.token = token
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
        )
    
    def _get_base_url(self):
        """Get base URL from settings or construct from request"""
        # In production, use configured API_BASE_URL
        # In development, use localhost
        if hasattr(settings, 'API_BASE_URL'):
            return settings.API_BASE_URL
        return 'http://127.0.0.1:8000'
    
    def _get_headers(self, extra_headers: Optional[Dict] = None) -> Dict[str, str]:
        """Build request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    def _make_url(self, path: str) -> str:
        """Construct full URL"""
        if path.startswith('http'):
            return path
        return urljoin(self.base_url, path.lstrip('/'))
    
    def _parse_error(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse error response"""
        try:
            error_data = response.json()
        except:
            error_data = {'detail': response.text or 'Unknown error'}
        
        return {
            'status_code': response.status_code,
            'error': error_data,
            'message': error_data.get('detail') or error_data.get('message') or 'Request failed',
        }
    
    def request(
        self, 
        method: str, 
        path: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        retry: int = 2
    ) -> Dict[str, Any]:
        """Make HTTP request with retries"""
        url = self._make_url(path)
        request_headers = self._get_headers(headers)
        
        for attempt in range(retry + 1):
            try:
                response = self.client.request(
                    method=method.upper(),
                    url=url,
                    json=data if data else None,
                    params=params,
                    headers=request_headers,
                )
                
                # Success
                if 200 <= response.status_code < 300:
                    if response.status_code == 204:  # No content
                        return {'success': True}
                    try:
                        return response.json()
                    except:
                        return {'data': response.text}
                
                # Client/Server error
                return self._parse_error(response)
            
            except httpx.TimeoutException:
                if attempt == retry:
                    return {
                        'status_code': 408,
                        'error': 'Request timeout',
                        'message': 'The request took too long to complete'
                    }
            except httpx.RequestError as e:
                if attempt == retry:
                    return {
                        'status_code': 500,
                        'error': str(e),
                        'message': 'Network error occurred'
                    }
        
        return {
            'status_code': 500,
            'error': 'Max retries exceeded',
            'message': 'Failed after multiple attempts'
        }
    
    def get(self, path: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """GET request"""
        return self.request('GET', path, params=params, **kwargs)
    
    def post(self, path: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """POST request"""
        return self.request('POST', path, data=data, **kwargs)
    
    def put(self, path: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        return self.request('PUT', path, data=data, **kwargs)
    
    def patch(self, path: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PATCH request"""
        return self.request('PATCH', path, data=data, **kwargs)
    
    def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        return self.request('DELETE', path, **kwargs)
    
    def close(self):
        """Close the client"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_api_client(request=None, token: Optional[str] = None) -> APIClient:
    """Factory function to create API client with auth from request"""
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        # Try to get JWT token from cookies or session
        token = request.COOKIES.get('jwt-auth') or token
    
    return APIClient(token=token)
