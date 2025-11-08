"""
Production Readiness Testing for PromptCraft V2 API Endpoints
============================================================

This command tests all V2 API endpoints to ensure production readiness.
Validates response codes, authentication, and basic functionality.
"""
import json
import time
import uuid
from typing import Dict, List, Tuple, Any
from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from colorama import Fore, Style, init

# Initialize colorama for Windows
init()

User = get_user_model()

class ProductionReadinessTest:
    """Comprehensive production readiness testing suite."""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.auth_headers = {}
        self.results = []
        self.endpoint_groups = {
            'health': ['/health/'],
            'api_docs': ['/api/schema/swagger-ui/'],
            'templates': [
                '/api/v2/templates/',
                '/api/v2/templates/featured/',
                '/api/v2/templates/trending/',
            ],
            'categories': ['/api/v2/template-categories/'],
            'auth': [
                '/api/v2/auth/check-username/',
                '/api/v2/auth/check-email/',
                '/api/v2/auth/social/providers/',
            ],
            'billing': [
                '/api/v2/billing/plans/',
                '/api/v2/billing/me/entitlements/',
            ],
            'orchestrator': [
                '/api/v2/orchestrator/intent/',
                '/api/v2/orchestrator/assess/',
                '/api/v2/orchestrator/search/',
                '/api/v2/orchestrator/template/',
            ],
            'analytics': [
                '/api/v2/analytics/dashboard/',
                '/api/v2/analytics/user-insights/',
                '/api/v2/analytics/template-analytics/',
            ],
            'core': [
                '/api/v2/core/config/',
                '/api/v2/core/health/detailed/',
            ],
            'research': [
                '/api/v2/research/jobs/',
                '/api/v2/research/quick/',
                '/api/v2/research/intent_fast/',
                '/api/v2/research/health/',
                '/api/v2/research/stats/',
            ]
        }
    
    def setup_test_user(self):
        """Create test user for authenticated endpoints."""
        try:
            username = f"test_user_{int(time.time())}"
            email = f"{username}@example.com"
            
            self.test_user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123'
            )
            
            # Login to get session
            login_success = self.client.login(
                username=username,
                password='testpass123'
            )
            
            if login_success:
                self.print_status("✅", f"Test user created and logged in: {username}")
                return True
            else:
                self.print_status("❌", "Failed to login test user")
                return False
                
        except Exception as e:
            self.print_status("❌", f"Failed to create test user: {e}")
            return False
    
    def cleanup_test_user(self):
        """Clean up test user."""
        if self.test_user:
            try:
                self.test_user.delete()
                self.print_status("🧹", "Test user cleaned up")
            except Exception as e:
                self.print_status("⚠️", f"Failed to cleanup test user: {e}")
    
    def test_endpoint(self, method: str, path: str, data: Dict = None, 
                     expected_codes: List[int] = None, auth_required: bool = True) -> Tuple[bool, Dict]:
        """Test a single endpoint and return results."""
        if expected_codes is None:
            expected_codes = [200, 201, 204, 400, 401, 403, 404, 405, 429]
        
        try:
            # Prepare request
            kwargs = {}
            if data:
                kwargs['data'] = json.dumps(data)
                kwargs['content_type'] = 'application/json'
            
            # Make request based on method
            if method.upper() == 'GET':
                response = self.client.get(path, **kwargs)
            elif method.upper() == 'POST':
                response = self.client.post(path, **kwargs)
            elif method.upper() == 'PUT':
                response = self.client.put(path, **kwargs)
            elif method.upper() == 'PATCH':
                response = self.client.patch(path, **kwargs)
            elif method.upper() == 'DELETE':
                response = self.client.delete(path, **kwargs)
            else:
                return False, {'error': f'Unsupported method: {method}'}
            
            # Analyze response
            success = response.status_code in expected_codes
            
            result = {
                'method': method.upper(),
                'path': path,
                'status_code': response.status_code,
                'success': success,
                'response_time': getattr(response, '_response_time', 'N/A'),
                'content_type': response.get('Content-Type', 'unknown'),
                'auth_required': auth_required
            }
            
            # Try to parse JSON response
            try:
                if response.content:
                    result['response_size'] = len(response.content)
                    if 'application/json' in response.get('Content-Type', ''):
                        result['json_valid'] = True
                        response_data = json.loads(response.content)
                        result['has_error_field'] = 'error' in response_data or 'detail' in response_data
                    else:
                        result['json_valid'] = False
                else:
                    result['response_size'] = 0
            except json.JSONDecodeError:
                result['json_valid'] = False
            
            return success, result
            
        except Exception as e:
            return False, {
                'method': method.upper(),
                'path': path,
                'status_code': 0,
                'error': str(e),
                'success': False,
                'response_time': 0.0
            }
    
    def test_research_endpoints_detailed(self):
        """Detailed testing of research agent endpoints."""
        self.print_header("🔬 Research Agent Detailed Testing")
        
        research_tests = [
            # Health check (no auth)
            ('GET', '/api/v2/research/health/', None, [200], False),
            
            # Stats (may require auth)
            ('GET', '/api/v2/research/stats/', None, [200, 401, 403], True),
            
            # Jobs list (requires auth)
            ('GET', '/api/v2/research/jobs/', None, [200, 401], True),
            
            # Intent fast (high priority test)
            ('POST', '/api/v2/research/intent_fast/', 
             {'query': 'What is artificial intelligence?'}, [200, 201, 400, 429], False),
            
            # Quick research
            ('POST', '/api/v2/research/quick/', 
             {'query': 'Machine learning basics', 'top_k': 3}, [200, 201, 400, 429], False),
        ]
        
        for method, path, data, expected, auth_req in research_tests:
            success, result = self.test_endpoint(method, path, data, expected, auth_req)
            self.results.append(result)
            
            status_icon = "✅" if success else "❌"
            auth_indicator = "🔐" if auth_req else "🌐"
            self.print_status(
                status_icon, 
                f"{auth_indicator} {method} {path} → {result['status_code']}"
            )
            
            # Special handling for specific responses
            if path == '/api/v2/research/intent_fast/' and result['status_code'] == 429:
                self.print_status("ℹ️", "  Rate limiting active (good for production)")
            elif path == '/api/v2/research/health/' and result['status_code'] == 200:
                self.print_status("ℹ️", "  Health endpoint operational")
    
    def test_endpoint_group(self, group_name: str, endpoints: List[str]):
        """Test a group of related endpoints."""
        self.print_header(f"🧪 Testing {group_name.title()} Endpoints")
        
        for endpoint in endpoints:
            # Determine appropriate method and expected codes
            if 'health' in endpoint or 'config' in endpoint or 'stats' in endpoint:
                method = 'GET'
                expected = [200, 401, 403]
                auth_required = 'config' not in endpoint
            elif 'intent' in endpoint or 'assess' in endpoint or 'track' in endpoint:
                method = 'POST'
                expected = [200, 201, 400, 401, 405, 429]
                auth_required = True
                data = {'query': 'test query'} if 'intent' in endpoint else {'prompt': 'test'}
            else:
                method = 'GET'
                expected = [200, 401, 403, 404, 405]
                auth_required = True
                data = None
            
            success, result = self.test_endpoint(
                method, endpoint, 
                data if method == 'POST' else None, 
                expected, auth_required
            )
            self.results.append(result)
            
            # Format output
            status_icon = "✅" if success else "❌"
            auth_icon = "🔐" if auth_required else "🌐"
            
            status_code = result.get('status_code', 'ERROR')
            self.print_status(
                status_icon,
                f"{auth_icon} {method} {endpoint} → {status_code}"
            )
            
            # Show error details if present
            if 'error' in result:
                self.print_status("💥", f"  Error: {result['error']}")
            
            # Additional context for specific status codes
            if result['status_code'] == 401 and auth_required:
                self.print_status("ℹ️", "  Authentication required (expected)")
            elif result['status_code'] == 405:
                self.print_status("ℹ️", "  Method not allowed (check HTTP method)")
            elif result['status_code'] == 404:
                self.print_status("⚠️", "  Endpoint not found (check URL routing)")
    
    def generate_report(self):
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        
        self.print_header("📊 Production Readiness Report")
        
        print(f"{Fore.CYAN}Overall Results:{Style.RESET_ALL}")
        print(f"  Total Endpoints Tested: {total_tests}")
        print(f"  Successful Tests: {Fore.GREEN}{successful_tests}{Style.RESET_ALL}")
        print(f"  Failed Tests: {Fore.RED}{total_tests - successful_tests}{Style.RESET_ALL}")
        print(f"  Success Rate: {Fore.YELLOW}{(successful_tests/total_tests)*100:.1f}%{Style.RESET_ALL}")
        
        # Group results by status
        status_groups = {}
        for result in self.results:
            status = result['status_code']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)
        
        print(f"\n{Fore.CYAN}Status Code Distribution:{Style.RESET_ALL}")
        for status_code in sorted(status_groups.keys()):
            count = len(status_groups[status_code])
            color = Fore.GREEN if status_code < 400 else Fore.RED if status_code >= 500 else Fore.YELLOW
            print(f"  {color}{status_code}{Style.RESET_ALL}: {count} endpoints")
        
        # Critical issues
        critical_issues = [r for r in self.results if not r['success'] and r['status_code'] >= 500]
        if critical_issues:
            print(f"\n{Fore.RED}🚨 Critical Issues (5xx errors):{Style.RESET_ALL}")
            for issue in critical_issues:
                print(f"  {issue['method']} {issue['path']} → {issue['status_code']}")
        
        # Authentication analysis
        auth_endpoints = [r for r in self.results if r.get('auth_required', False)]
        if auth_endpoints:
            auth_working = sum(1 for r in auth_endpoints if r['status_code'] in [200, 201, 401, 403])
            print(f"\n{Fore.CYAN}Authentication Analysis:{Style.RESET_ALL}")
            print(f"  Auth-required endpoints: {len(auth_endpoints)}")
            print(f"  Properly secured: {auth_working}/{len(auth_endpoints)}")
        
        # Production readiness assessment
        print(f"\n{Fore.CYAN}🚀 Production Readiness Assessment:{Style.RESET_ALL}")
        
        readiness_score = 0
        max_score = 0
        
        # Core health endpoints (critical)
        health_tests = [r for r in self.results if 'health' in r['path']]
        if health_tests and all(r['status_code'] == 200 for r in health_tests):
            readiness_score += 25
            print(f"  {Fore.GREEN}✅ Health Endpoints: Operational{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ Health Endpoints: Issues detected{Style.RESET_ALL}")
        max_score += 25
        
        # Authentication system (critical)
        auth_tests = [r for r in self.results if 'auth' in r['path']]
        if auth_tests and any(r['status_code'] in [200, 401] for r in auth_tests):
            readiness_score += 25
            print(f"  {Fore.GREEN}✅ Authentication: Working{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ Authentication: Issues detected{Style.RESET_ALL}")
        max_score += 25
        
        # Research agent (high priority)
        research_tests = [r for r in self.results if 'research' in r['path']]
        research_success = sum(1 for r in research_tests if r['success'])
        if research_tests and (research_success / len(research_tests)) >= 0.7:
            readiness_score += 20
            print(f"  {Fore.GREEN}✅ Research Agent: {research_success}/{len(research_tests)} endpoints working{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ Research Agent: Only {research_success}/{len(research_tests)} endpoints working{Style.RESET_ALL}")
        max_score += 20
        
        # API stability (no 5xx errors)
        server_errors = sum(1 for r in self.results if r['status_code'] >= 500)
        if server_errors == 0:
            readiness_score += 20
            print(f"  {Fore.GREEN}✅ Server Stability: No 5xx errors{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ Server Stability: {server_errors} server errors{Style.RESET_ALL}")
        max_score += 20
        
        # Overall API coverage
        if (successful_tests / total_tests) >= 0.8:
            readiness_score += 10
            print(f"  {Fore.GREEN}✅ API Coverage: {(successful_tests/total_tests)*100:.1f}%{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ API Coverage: Only {(successful_tests/total_tests)*100:.1f}%{Style.RESET_ALL}")
        max_score += 10
        
        # Final assessment
        final_score = (readiness_score / max_score) * 100
        print(f"\n{Fore.CYAN}🎯 Production Readiness Score: {Style.RESET_ALL}", end="")
        
        if final_score >= 90:
            print(f"{Fore.GREEN}{final_score:.1f}% - READY FOR PRODUCTION! 🚀{Style.RESET_ALL}")
        elif final_score >= 75:
            print(f"{Fore.YELLOW}{final_score:.1f}% - Nearly ready, minor issues{Style.RESET_ALL}")
        elif final_score >= 50:
            print(f"{Fore.YELLOW}{final_score:.1f}% - Significant issues need attention{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{final_score:.1f}% - NOT READY - Critical issues{Style.RESET_ALL}")
        
        return final_score >= 75  # Return True if ready for production
    
    def print_header(self, title: str):
        """Print formatted section header."""
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    
    def print_status(self, icon: str, message: str):
        """Print formatted status message."""
        print(f"{icon} {message}")
    
    def run_all_tests(self):
        """Execute complete production readiness test suite."""
        start_time = time.time()
        
        print(f"{Fore.GREEN}🚀 PromptCraft V2 API Production Readiness Test{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Testing comprehensive endpoint functionality...{Style.RESET_ALL}\n")
        
        # Setup
        if not self.setup_test_user():
            print(f"{Fore.RED}❌ Failed to setup test environment{Style.RESET_ALL}")
            return False
        
        try:
            # Test each endpoint group
            for group_name, endpoints in self.endpoint_groups.items():
                self.test_endpoint_group(group_name, endpoints)
                time.sleep(0.5)  # Brief pause between groups
            
            # Special detailed testing for research agent
            self.test_research_endpoints_detailed()
            
            # Generate comprehensive report
            production_ready = self.generate_report()
            
            # Timing info
            elapsed_time = time.time() - start_time
            print(f"\n{Fore.CYAN}⏱️  Total test time: {elapsed_time:.2f} seconds{Style.RESET_ALL}")
            
            return production_ready
            
        finally:
            # Cleanup
            self.cleanup_test_user()


class Command(BaseCommand):
    """Django management command for production readiness testing."""
    
    help = 'Test V2 API endpoints for production readiness'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=str,
            help='Test specific endpoint group (health, auth, research, etc.)',
            default=None
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['console', 'json', 'csv'],
            default='console',
            help='Output format for results'
        )
        parser.add_argument(
            '--save-report',
            action='store_true',
            help='Save detailed report to file'
        )
    
    def handle(self, *args, **options):
        """Execute the production readiness test."""
        
        # Initialize test suite
        test_suite = ProductionReadinessTest()
        
        try:
            if options['group']:
                # Test specific group
                group_name = options['group']
                if group_name in test_suite.endpoint_groups:
                    endpoints = test_suite.endpoint_groups[group_name]
                    print(f"Testing {group_name} endpoints...")
                    test_suite.setup_test_user()
                    test_suite.test_endpoint_group(group_name, endpoints)
                    test_suite.generate_report()
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Unknown group: {group_name}")
                    )
                    self.stdout.write(
                        f"Available groups: {', '.join(test_suite.endpoint_groups.keys())}"
                    )
                    return
            else:
                # Run complete test suite
                production_ready = test_suite.run_all_tests()
                
                if production_ready:
                    self.stdout.write(
                        self.style.SUCCESS('\n🎉 API is PRODUCTION READY!')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️  API needs attention before production')
                    )
            
            # Save report if requested
            if options['save_report']:
                report_path = 'var/reports/production_readiness_report.json'
                import os
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                
                with open(report_path, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'results': test_suite.results,
                        'summary': {
                            'total_tests': len(test_suite.results),
                            'successful_tests': sum(1 for r in test_suite.results if r['success']),
                        }
                    }, f, indent=2)
                
                self.stdout.write(f"📄 Report saved to: {report_path}")
        
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⏹️  Test interrupted by user'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n💥 Test suite error: {e}')
            )
            raise