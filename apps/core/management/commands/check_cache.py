"""
Management command to check cache and session status
"""

from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Check cache and session configuration status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking cache and session configuration...'))
        
        issues = []
        warnings = []
        
        # Check cache backends
        try:
            default_cache = caches['default']
            self.stdout.write(f'Default cache backend: {default_cache.__class__.__name__}')
            
            # Test default cache
            test_key = 'health_check_test'
            default_cache.set(test_key, 'test_value', 30)
            retrieved = default_cache.get(test_key)
            if retrieved == 'test_value':
                self.stdout.write(self.style.SUCCESS('✓ Default cache working'))
                default_cache.delete(test_key)
            else:
                issues.append('Default cache not working properly')
                
        except Exception as e:
            issues.append(f'Default cache error: {e}')
        
        # Check sessions cache
        try:
            sessions_cache = caches['sessions']
            self.stdout.write(f'Sessions cache backend: {sessions_cache.__class__.__name__}')
            
            # Test sessions cache
            test_key = 'session_test'
            sessions_cache.set(test_key, 'test_session', 30)
            retrieved = sessions_cache.get(test_key)
            if retrieved == 'test_session':
                self.stdout.write(self.style.SUCCESS('✓ Sessions cache working'))
                sessions_cache.delete(test_key)
            else:
                issues.append('Sessions cache not working properly')
                
        except Exception as e:
            issues.append(f'Sessions cache error: {e}')
        
        # Check session configuration
        session_engine = getattr(settings, 'SESSION_ENGINE', 'Not configured')
        session_cache_alias = getattr(settings, 'SESSION_CACHE_ALIAS', 'Not configured')
        
        self.stdout.write(f'Session engine: {session_engine}')
        self.stdout.write(f'Session cache alias: {session_cache_alias}')
        
        if session_engine == 'django.contrib.sessions.backends.cache':
            if session_cache_alias not in [cache_name for cache_name in caches]:
                issues.append(f'Session cache alias "{session_cache_alias}" not found in CACHES')
        
        # Check Redis status if configured
        for cache_name, cache_config in settings.CACHES.items():
            if 'redis' in cache_config.get('BACKEND', '').lower():
                try:
                    import redis
                    location = cache_config.get('LOCATION', 'redis://localhost:6379/0')
                    redis_client = redis.Redis.from_url(location)
                    redis_client.ping()
                    self.stdout.write(self.style.SUCCESS(f'✓ Redis available for {cache_name} cache'))
                except Exception as e:
                    warnings.append(f'Redis issue for {cache_name} cache: {e}')
        
        # Check WebSocket configuration
        try:
            channel_layers = getattr(settings, 'CHANNEL_LAYERS', {})
            if channel_layers:
                backend = channel_layers['default']['BACKEND']
                self.stdout.write(f'WebSocket backend: {backend}')
                if 'redis' in backend.lower():
                    try:
                        import channels_redis
                        self.stdout.write(self.style.SUCCESS('✓ Redis WebSocket backend available'))
                    except ImportError:
                        warnings.append('channels_redis not installed but Redis WebSocket backend configured')
                else:
                    self.stdout.write(self.style.WARNING('⚠ Using in-memory WebSocket backend (not suitable for production)'))
            else:
                warnings.append('CHANNEL_LAYERS not configured')
        except Exception as e:
            warnings.append(f'WebSocket configuration error: {e}')
        
        # Report results
        if issues:
            self.stdout.write(self.style.ERROR('\nIssues found:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'✗ {issue}'))
        
        if warnings:
            self.stdout.write(self.style.WARNING('\nWarnings:'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'⚠ {warning}'))
        
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS('\n✓ All cache and session checks passed'))
        elif not issues:
            self.stdout.write(self.style.SUCCESS(f'\n✓ No critical issues found ({len(warnings)} warnings)'))
        
        self.stdout.write('\nRecommendations:')
        self.stdout.write('- For production: Use Redis for all caches and WebSocket backend')
        self.stdout.write('- For development: In-memory caches are acceptable')
        self.stdout.write('- Ensure SESSION_CACHE_ALIAS matches an existing cache backend')
        self.stdout.write('- Run this check after any cache configuration changes')