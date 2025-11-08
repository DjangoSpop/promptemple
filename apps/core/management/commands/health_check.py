"""
Health check management command for production monitoring
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger('promptcraft.health')


class Command(BaseCommand):
    help = 'Check application health and dependencies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        health_checks = {
            'database': self.check_database,
            'cache': self.check_cache,
            'redis': self.check_redis,
            'celery': self.check_celery,
            'storage': self.check_storage,
        }
        
        results = {}
        failed_checks = []
        
        self.stdout.write('Running health checks...\n')
        
        for check_name, check_func in health_checks.items():
            try:
                status, message = check_func()
                results[check_name] = {
                    'status': 'OK' if status else 'FAILED',
                    'message': message
                }
                
                if status:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {check_name.upper()}: {message}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ {check_name.upper()}: {message}')
                    )
                    failed_checks.append(check_name)
                    
            except Exception as e:
                results[check_name] = {
                    'status': 'ERROR',
                    'message': str(e)
                }
                self.stdout.write(
                    self.style.ERROR(f'✗ {check_name.upper()}: {str(e)}')
                )
                failed_checks.append(check_name)
        
        # Summary
        self.stdout.write('\n' + '='*50)
        passed = len([r for r in results.values() if r['status'] == 'OK'])
        total = len(results)
        
        if failed_checks:
            self.stdout.write(
                self.style.ERROR(
                    f'Health check FAILED ({passed}/{total} passed)'
                )
            )
            return 1
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Health check PASSED ({passed}/{total} passed)'
                )
            )
            return 0

    def check_database(self):
        """Check database connection"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            return True, 'Database connection OK'
        except Exception as e:
            return False, f'Database error: {str(e)}'

    def check_cache(self):
        """Check cache backend"""
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'ok', 10)
            value = cache.get(test_key)
            
            if value == 'ok':
                cache.delete(test_key)
                return True, 'Cache OK'
            else:
                return False, 'Cache read/write failed'
        except Exception as e:
            return False, f'Cache error: {str(e)}'

    def check_redis(self):
        """Check Redis connection"""
        try:
            import redis
            redis_url = getattr(settings, 'REDIS_URL', None)
            
            if not redis_url:
                return True, 'Redis not configured'
            
            r = redis.Redis.from_url(redis_url)
            r.ping()
            return True, 'Redis connection OK'
        except ImportError:
            return True, 'Redis library not available'
        except Exception as e:
            return False, f'Redis error: {str(e)}'

    def check_celery(self):
        """Check Celery worker status"""
        try:
            from celery import current_app
            
            stats = current_app.control.inspect().stats()
            if stats:
                worker_count = len(stats)
                return True, f'Celery OK ({worker_count} workers)'
            else:
                return False, 'No active Celery workers'
        except Exception as e:
            return False, f'Celery error: {str(e)}'

    def check_storage(self):
        """Check file storage"""
        try:
            import os
            from django.conf import settings
            
            media_root = settings.MEDIA_ROOT
            static_root = settings.STATIC_ROOT
            
            if os.path.exists(media_root) and os.path.exists(static_root):
                return True, 'Storage paths accessible'
            else:
                return False, 'Storage paths not accessible'
        except Exception as e:
            return False, f'Storage error: {str(e)}'