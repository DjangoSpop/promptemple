#!/usr/bin/env python
"""
Deployment Validation Script for PromptCraft Railway Deployment

This script validates that all critical components are working correctly
before and after deployment to Railway.
"""

import os
import sys
import json
import requests
import time
from urllib.parse import urljoin

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.production')

try:
    import django
    django.setup()
    from django.conf import settings
    from django.test.utils import get_runner
    from django.core.management import call_command
    from apps.core.health_checks import api_health_check
except ImportError as e:
    print(f"❌ Failed to import Django: {e}")
    sys.exit(1)

class DeploymentValidator:
    """Validates deployment readiness and functionality"""

    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get('RAILWAY_STATIC_URL', 'http://localhost:8000')
        self.errors = []
        self.warnings = []

    def log_error(self, message):
        """Log an error"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message):
        """Log a warning"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_success(self, message):
        """Log a success"""
        print(f"✅ SUCCESS: {message}")

    def validate_settings(self):
        """Validate Django settings for production"""
        print("\n🔧 Validating Django settings...")

        # Check DEBUG setting
        if settings.DEBUG:
            self.log_warning("DEBUG is True in production settings")
        else:
            self.log_success("DEBUG is False")

        # Check SECRET_KEY
        if settings.SECRET_KEY == "django-insecure-=$&0cpo9(=xihchk^!6p&#um-7icn@#u4ut)04sqcxs6__i+gd":
            self.log_error("SECRET_KEY is using default insecure value")
        else:
            self.log_success("SECRET_KEY is configured")

        # Check ALLOWED_HOSTS
        if '*' in settings.ALLOWED_HOSTS:
            self.log_warning("ALLOWED_HOSTS contains '*' (not recommended for production)")
        elif settings.ALLOWED_HOSTS:
            self.log_success(f"ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}")
        else:
            self.log_error("ALLOWED_HOSTS is empty")

        # Check database configuration
        db_config = settings.DATABASES['default']
        if db_config['ENGINE'] == 'django.db.backends.sqlite3':
            self.log_warning("Using SQLite database (OK for Railway deployment)")
        else:
            self.log_success(f"Database engine: {db_config['ENGINE']}")

    def validate_dependencies(self):
        """Validate that required dependencies are available"""
        print("\n📦 Validating dependencies...")

        required_modules = [
            'django',
            'rest_framework',
            'channels',
            'daphne',
            'celery',
            'redis',
            'openai',
            'anthropic',
            'sentry_sdk',
        ]

        for module in required_modules:
            try:
                __import__(module)
                self.log_success(f"{module} is available")
            except ImportError:
                self.log_error(f"{module} is not available")

    def validate_health_checks(self):
        """Validate internal health checks"""
        print("\n🏥 Running internal health checks...")

        try:
            health_result = api_health_check()

            if health_result['status'] == 'healthy':
                self.log_success("Internal health check passed")
            else:
                self.log_error(f"Internal health check failed: {health_result.get('message', 'Unknown error')}")

            # Check individual components
            for component, result in health_result.get('checks', {}).items():
                if result['status'] == 'healthy':
                    self.log_success(f"{component} check passed")
                else:
                    self.log_warning(f"{component} check failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            self.log_error(f"Failed to run internal health checks: {e}")

    def validate_api_endpoints(self):
        """Validate API endpoints are accessible"""
        print(f"\n🌐 Validating API endpoints at {self.base_url}...")

        endpoints = [
            '/health/',
            '/api/v1/core/health/',
            '/api/v2/core/health/',
            '/api/',
        ]

        for endpoint in endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    self.log_success(f"{endpoint} responded with 200")
                else:
                    self.log_warning(f"{endpoint} responded with {response.status_code}")

            except requests.exceptions.RequestException as e:
                self.log_warning(f"Could not reach {endpoint}: {e}")

    def validate_static_files(self):
        """Validate static files configuration"""
        print("\n📁 Validating static files...")

        # Check static files settings
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            self.log_success(f"STATIC_ROOT configured: {settings.STATIC_ROOT}")
        else:
            self.log_error("STATIC_ROOT not configured")

        if hasattr(settings, 'STATICFILES_STORAGE'):
            self.log_success(f"Static files storage: {settings.STATICFILES_STORAGE}")
        else:
            self.log_warning("STATICFILES_STORAGE not configured")

    def validate_environment_variables(self):
        """Validate required environment variables"""
        print("\n🔐 Validating environment variables...")

        required_vars = ['DJANGO_SETTINGS_MODULE']
        optional_vars = ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL', 'SENTRY_DSN']

        for var in required_vars:
            if os.environ.get(var):
                self.log_success(f"{var} is set")
            else:
                self.log_error(f"{var} is not set")

        for var in optional_vars:
            if os.environ.get(var):
                self.log_success(f"{var} is configured")
            else:
                self.log_warning(f"{var} is not configured")

    def run_django_checks(self):
        """Run Django system checks"""
        print("\n🔍 Running Django system checks...")

        try:
            from django.core.management import call_command
            from io import StringIO

            # Capture output
            output = StringIO()
            call_command('check', stdout=output, stderr=output)

            result = output.getvalue()
            if "System check identified no issues" in result:
                self.log_success("Django system checks passed")
            else:
                self.log_warning(f"Django system checks output: {result}")

        except Exception as e:
            self.log_error(f"Failed to run Django system checks: {e}")

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "="*60)
        print("DEPLOYMENT VALIDATION REPORT")
        print("="*60)

        total_errors = len(self.errors)
        total_warnings = len(self.warnings)

        if total_errors == 0 and total_warnings == 0:
            print("🎉 ALL CHECKS PASSED! Deployment is ready.")
            return True
        else:
            print(f"📊 Summary: {total_errors} errors, {total_warnings} warnings")

            if total_errors > 0:
                print("\n❌ ERRORS THAT MUST BE FIXED:")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")

            if total_warnings > 0:
                print("\n⚠️  WARNINGS TO CONSIDER:")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")

            return total_errors == 0

    def run_all_validations(self):
        """Run all validations"""
        print("🚀 Starting PromptCraft deployment validation...")

        self.validate_settings()
        self.validate_dependencies()
        self.validate_environment_variables()
        self.validate_static_files()
        self.run_django_checks()
        self.validate_health_checks()

        # Only run API endpoint validation if base_url is provided
        if self.base_url and self.base_url != 'http://localhost:8000':
            self.validate_api_endpoints()
        else:
            print("\n🌐 Skipping API endpoint validation (no remote URL provided)")

        return self.generate_report()

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Validate PromptCraft deployment')
    parser.add_argument('--url', help='Base URL of deployed application')
    parser.add_argument('--local', action='store_true', help='Run local validation only')

    args = parser.parse_args()

    # Determine base URL
    base_url = None
    if not args.local:
        base_url = args.url or os.environ.get('RAILWAY_STATIC_URL')

    validator = DeploymentValidator(base_url)

    try:
        success = validator.run_all_validations()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()