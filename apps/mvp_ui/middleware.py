"""
Performance tracking middleware for API calls
Tracks request_id, duration, status codes for dashboard metrics
"""
import time
import uuid
from collections import deque
from threading import Lock
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
import statistics


class PerformanceTracker:
    """Singleton tracker for API performance metrics"""
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        self.requests = deque(maxlen=100)  # Store last 100 requests
        self.endpoint_stats = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def add_request(self, data):
        """Add a request to tracking"""
        with self._lock:
            self.requests.append(data)
            
            # Update endpoint stats
            endpoint = data['endpoint']
            if endpoint not in self.endpoint_stats:
                self.endpoint_stats[endpoint] = {
                    'count': 0,
                    'durations': deque(maxlen=50),
                    'errors': 0,
                }
            
            stats = self.endpoint_stats[endpoint]
            stats['count'] += 1
            stats['durations'].append(data['duration_ms'])
            if data['status_code'] >= 400:
                stats['errors'] += 1
    
    def get_recent_requests(self, limit=50):
        """Get recent requests"""
        with self._lock:
            return list(self.requests)[-limit:]
    
    def get_endpoint_stats(self):
        """Get aggregated endpoint statistics"""
        with self._lock:
            stats = {}
            for endpoint, data in self.endpoint_stats.items():
                durations = list(data['durations'])
                if durations:
                    stats[endpoint] = {
                        'count': data['count'],
                        'errors': data['errors'],
                        'avg_ms': round(statistics.mean(durations), 2),
                        'p95_ms': round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) > 1 else durations[0],
                        'min_ms': round(min(durations), 2),
                        'max_ms': round(max(durations), 2),
                    }
            return stats


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to track request performance"""
    
    def process_request(self, request):
        """Start timing the request"""
        request._start_time = time.time()
        request._request_id = str(uuid.uuid4())
        request.request_id = request._request_id
        return None
    
    def process_response(self, request, response):
        """Track request completion"""
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000  # Convert to milliseconds
            
            # Resolve endpoint
            try:
                resolved = resolve(request.path_info)
                endpoint = f"{request.method} {resolved.url_name or request.path_info}"
            except:
                endpoint = f"{request.method} {request.path_info}"
            
            # Track metrics
            tracker = PerformanceTracker.get_instance()
            tracker.add_request({
                'request_id': getattr(request, '_request_id', 'N/A'),
                'timestamp': time.time(),
                'method': request.method,
                'path': request.path_info,
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration_ms': round(duration, 2),
                'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            })
            
            # Add header
            response['X-Request-ID'] = getattr(request, '_request_id', 'N/A')
            response['X-Response-Time'] = f"{duration:.2f}ms"
        
        return response
