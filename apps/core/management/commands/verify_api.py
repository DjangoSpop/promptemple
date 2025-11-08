"""
Management command to verify API endpoints and CORS configuration
"""
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import get_resolver
from django.urls.exceptions import Resolver404


class Command(BaseCommand):
    help = 'Verify API endpoints and CORS headers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-cors',
            action='store_true',
            help='Check CORS headers on endpoints',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        base_url = 'http://127.0.0.1:8000'
        
        self.stdout.write(self.style.SUCCESS('\n=== API Endpoint Verification ===\n'))
        self.stdout.write(f'Base URL: {base_url}')
        self.stdout.write(f'DEBUG: {settings.DEBUG}\n')

        # Key endpoints to verify
        endpoints = [
            ('GET', '/health/', 'Health check'),
            ('GET', '/api/', 'API root'),
            ('GET', '/api/v2/core/config/', 'Core config'),
            ('GET', '/api/v2/template-categories/', 'Template categories'),
            ('GET', '/api/v2/templates/', 'Templates list'),
            ('GET', '/api/v2/templates/featured/', 'Featured templates'),
            ('GET', '/api/v2/templates/trending/', 'Trending templates'),
            ('GET', '/api/v2/ai/assistant/', 'AI Assistant'),
            ('GET', '/api/v2/analytics/dashboard/', 'Analytics dashboard'),
        ]

        results = []
        
        for method, path, description in endpoints:
            result = self._check_endpoint(base_url, method, path, description, options)
            results.append(result)

        # Print results
        self.stdout.write('\n=== Results ===\n')
        for result in results:
            self._print_result(result, options)

        # Summary
        successful = sum(1 for r in results if r['accessible'])
        self.stdout.write(f'\nSummary: {successful}/{len(results)} endpoints accessible\n')

        # Check CORS if requested
        if options['check_cors']:
            self.stdout.write('\n=== CORS Header Verification ===\n')
            self._check_cors_headers(base_url, endpoints)

    def _check_endpoint(self, base_url, method, path, description, options):
        """Check if endpoint is accessible"""
        url = f'{base_url}{path}'
        
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    timeout=5,
                    headers={'Accept': 'application/json'},
                    allow_redirects=False
                )
            else:
                response = requests.request(
                    method,
                    url,
                    timeout=5,
                    headers={'Accept': 'application/json'},
                    allow_redirects=False
                )
            
            return {
                'path': path,
                'description': description,
                'method': method,
                'status': response.status_code,
                'accessible': response.status_code < 500,
                'cors_header': response.headers.get('Access-Control-Allow-Origin'),
                'error': None,
            }
        except requests.ConnectionError as e:
            return {
                'path': path,
                'description': description,
                'method': method,
                'status': None,
                'accessible': False,
                'cors_header': None,
                'error': f'Connection error: {str(e)}',
            }
        except requests.Timeout:
            return {
                'path': path,
                'description': description,
                'method': method,
                'status': None,
                'accessible': False,
                'cors_header': None,
                'error': 'Request timeout',
            }
        except Exception as e:
            return {
                'path': path,
                'description': description,
                'method': method,
                'status': None,
                'accessible': False,
                'cors_header': None,
                'error': str(e),
            }

    def _print_result(self, result, options):
        """Print endpoint check result"""
        if result['error']:
            self.stdout.write(
                self.style.ERROR(f"✗ {result['description']}: {result['error']}")
            )
        elif result['accessible']:
            status_color = self.style.SUCCESS if result['status'] < 400 else self.style.WARNING
            status_text = f"HTTP {result['status']}"
            
            line = f"✓ {result['description']}: {status_text}"
            
            if result['cors_header']:
                line += f" (CORS: {result['cors_header']})"
            elif options['verbose']:
                line += " (No CORS header)"
            
            self.stdout.write(status_color(line))
        else:
            self.stdout.write(
                self.style.ERROR(f"✗ {result['description']}: HTTP {result['status']}")
            )

    def _check_cors_headers(self, base_url, endpoints):
        """Check CORS headers by making preflight requests"""
        frontend_origin = 'http://localhost:3001'
        
        self.stdout.write(f'Checking preflight requests from: {frontend_origin}\n')
        
        for method, path, description in endpoints:
            if method != 'GET':
                continue
            
            url = f'{base_url}{path}'
            
            try:
                response = requests.options(
                    url,
                    headers={
                        'Origin': frontend_origin,
                        'Access-Control-Request-Method': 'GET',
                    },
                    timeout=5,
                    allow_redirects=False
                )
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
                cors_methods = response.headers.get('Access-Control-Allow-Methods', 'NOT SET')
                cors_headers = response.headers.get('Access-Control-Allow-Headers', 'NOT SET')
                
                if response.headers.get('Access-Control-Allow-Origin'):
                    status = self.style.SUCCESS('✓ CORS enabled')
                else:
                    status = self.style.ERROR('✗ CORS not configured')
                
                self.stdout.write(f'\n{description} ({path}):')
                self.stdout.write(f'  Status: HTTP {response.status_code} {status}')
                self.stdout.write(f'  Allow-Origin: {cors_origin}')
                self.stdout.write(f'  Allow-Methods: {cors_methods}')
                if len(cors_headers) < 100:
                    self.stdout.write(f'  Allow-Headers: {cors_headers}')
                else:
                    self.stdout.write(f'  Allow-Headers: {cors_headers[:100]}...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'{description}: Error - {str(e)}')
                )
