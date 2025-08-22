"""
Health Check Utilities for PromptCraft API

This module provides health check utilities for monitoring the application status.

Author: GitHub Copilot
Date: August 9, 2025
"""

from django.db import connections
from django.core.cache import cache
from django.conf import settings
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

def database_check() -> Dict[str, Any]:
    """
    Check database connectivity and basic functionality.
    
    Returns:
        Dict containing check results and timing
    """
    start_time = time.time()
    
    try:
        # Test database connection
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        # Test basic query
        from apps.templates.models import Template
        template_count = Template.objects.count()
        
        elapsed_time = time.time() - start_time
        
        return {
            'status': 'healthy',
            'message': f'Database connection successful. {template_count} templates available.',
            'response_time_ms': round(elapsed_time * 1000, 2),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'template_count': template_count
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Database health check failed: {e}")
        
        return {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}',
            'response_time_ms': round(elapsed_time * 1000, 2),
            'error': str(e)
        }

def cache_check() -> Dict[str, Any]:
    """
    Check cache functionality.
    
    Returns:
        Dict containing check results and timing
    """
    start_time = time.time()
    
    try:
        # Test cache write and read
        test_key = 'health_check_test'
        test_value = f'test_value_{int(time.time())}'
        
        cache.set(test_key, test_value, timeout=60)
        cached_value = cache.get(test_key)
        
        if cached_value == test_value:
            cache.delete(test_key)  # Cleanup
            elapsed_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'message': 'Cache is working correctly',
                'response_time_ms': round(elapsed_time * 1000, 2)
            }
        else:
            elapsed_time = time.time() - start_time
            return {
                'status': 'unhealthy',
                'message': 'Cache read/write mismatch',
                'response_time_ms': round(elapsed_time * 1000, 2),
                'error': 'Cache value mismatch'
            }
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Cache health check failed: {e}")
        
        return {
            'status': 'unhealthy',
            'message': f'Cache error: {str(e)}',
            'response_time_ms': round(elapsed_time * 1000, 2),
            'error': str(e)
        }

def storage_check() -> Dict[str, Any]:
    """
    Check file storage functionality.
    
    Returns:
        Dict containing check results and timing
    """
    start_time = time.time()
    
    try:
        import os
        import tempfile
        import uuid
        from django.conf import settings
        
        # Check if media directory is writable
        media_root = getattr(settings, 'MEDIA_ROOT', tempfile.gettempdir())
        
        # Use a unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        test_file_path = os.path.join(media_root, f'health_check_test_{unique_id}.txt')
        
        # Ensure directory exists
        os.makedirs(media_root, exist_ok=True)
        
        # Test write and read in one operation to minimize file lock time
        test_content = f'health check test {unique_id}'
        
        # Test write
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Test read
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        # Verify content
        if content != test_content:
            raise Exception("File content verification failed")
        
        # Cleanup - handle file lock gracefully
        try:
            os.remove(test_file_path)
        except (OSError, PermissionError) as cleanup_error:
            logger.warning(f"Could not cleanup test file {test_file_path}: {cleanup_error}")
            # Don't fail the health check if cleanup fails
        
        elapsed_time = time.time() - start_time
        
        return {
            'status': 'healthy',
            'message': 'Storage is working correctly',
            'response_time_ms': round(elapsed_time * 1000, 2),
            'media_root': str(media_root)  # Convert to string to avoid JSON serialization issues
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Storage health check failed: {e}")
        
        return {
            'status': 'unhealthy',
            'message': f'Storage error: {str(e)}',
            'response_time_ms': round(elapsed_time * 1000, 2),
            'error': str(e)
        }

def api_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for the entire API.
    
    Returns:
        Dict containing overall health status and individual check results
    """
    start_time = time.time()
    
    checks = {
        'database': database_check(),
        'cache': cache_check(),
        'storage': storage_check()
    }
    
    # Determine overall health
    overall_status = 'healthy'
    unhealthy_services = []
    
    for service, result in checks.items():
        if result['status'] != 'healthy':
            overall_status = 'unhealthy'
            unhealthy_services.append(service)
    
    elapsed_time = time.time() - start_time
    
    # Use timezone-aware timestamp for JSON serialization
    from django.utils import timezone
    
    return {
        'status': overall_status,
        'message': f'API health check completed. Status: {overall_status}',
        'timestamp': timezone.now().isoformat(),
        'response_time_ms': round(elapsed_time * 1000, 2),
        'checks': checks,
        'unhealthy_services': unhealthy_services,
        'version': getattr(settings, 'API_VERSION', '1.0.0'),
        'debug_mode': settings.DEBUG
    }
