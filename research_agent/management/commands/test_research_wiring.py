"""
Django management command to test research agent wiring and functionality.
"""
import json
import uuid
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from django.conf import settings


class Command(BaseCommand):
    help = 'Test research agent endpoints and verify they are properly wired'

    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            type=str,
            choices=['all', 'intent_fast', 'quick', 'health', 'stats'],
            default='all',
            help='Which endpoint to test (default: all)'
        )

    def handle(self, *args, **options):
        client = Client()
        test_endpoint = options['endpoint']
        
        self.stdout.write(self.style.SUCCESS('🔍 Testing Research Agent Endpoints'))
        self.stdout.write('=' * 50)
        
        if test_endpoint in ['all', 'health']:
            self._test_health_endpoint(client)
        
        if test_endpoint in ['all', 'stats']:
            self._test_stats_endpoint(client)
            
        if test_endpoint in ['all', 'intent_fast']:
            self._test_intent_fast_endpoint(client)
            
        if test_endpoint in ['all', 'quick']:
            self._test_quick_research_endpoint(client)
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Research Agent Testing Complete'))

    def _test_health_endpoint(self, client):
        """Test the health check endpoint."""
        self.stdout.write('\n🏥 Testing Health Endpoint...')
        
        try:
            response = client.get('/api/v2/research/health/')
            self.stdout.write(f'   Status Code: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(f'   Overall Health: {data.get("overall", "Unknown")}')
                self.stdout.write(self.style.SUCCESS('   ✅ Health endpoint working'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Health endpoint failed: {response.status_code}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Health endpoint error: {str(e)}'))

    def _test_stats_endpoint(self, client):
        """Test the statistics endpoint."""
        self.stdout.write('\n📊 Testing Stats Endpoint...')
        
        try:
            response = client.get('/api/v2/research/stats/')
            self.stdout.write(f'   Status Code: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                total_jobs = data.get('total_jobs', 0)
                self.stdout.write(f'   Total Jobs: {total_jobs}')
                self.stdout.write(self.style.SUCCESS('   ✅ Stats endpoint working'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Stats endpoint failed: {response.status_code}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Stats endpoint error: {str(e)}'))

    def _test_intent_fast_endpoint(self, client):
        """Test the fast intent endpoint."""
        self.stdout.write('\n⚡ Testing Intent Fast Endpoint...')
        
        try:
            # Test v2 endpoint
            response = client.post(
                '/api/v2/research/intent_fast/',
                data=json.dumps({
                    'query': 'What is artificial intelligence?',
                    'top_k': 5
                }),
                content_type='application/json'
            )
            
            self.stdout.write(f'   V2 Status Code: {response.status_code}')
            
            if response.status_code == 201:
                data = response.json()
                intent_id = data.get('intent_id')
                self.stdout.write(f'   Intent ID: {intent_id}')
                self.stdout.write(f'   Query: {data.get("query")}')
                self.stdout.write(f'   Has Warm Card: {"warm_card" in data}')
                self.stdout.write(f'   Stream URL: {data.get("stream_url", "Missing")}')
                self.stdout.write(f'   Cards Stream URL: {data.get("cards_stream_url", "Missing")}')
                self.stdout.write(self.style.SUCCESS('   ✅ Intent Fast (V2) endpoint working'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Intent Fast (V2) failed: {response.status_code}'))
                if hasattr(response, 'json'):
                    self.stdout.write(f'   Error: {response.json()}')
            
            # Test v1 endpoint
            response_v1 = client.post(
                '/api/v1/intent_fast/',
                data=json.dumps({
                    'query': 'What is machine learning?',
                    'top_k': 5
                }),
                content_type='application/json'
            )
            
            self.stdout.write(f'   V1 Status Code: {response_v1.status_code}')
            
            if response_v1.status_code == 201:
                self.stdout.write(self.style.SUCCESS('   ✅ Intent Fast (V1) endpoint working'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Intent Fast (V1) failed: {response_v1.status_code}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Intent Fast endpoint error: {str(e)}'))

    def _test_quick_research_endpoint(self, client):
        """Test the quick research endpoint."""
        self.stdout.write('\n🔬 Testing Quick Research Endpoint...')
        
        try:
            response = client.post(
                '/api/v2/research/quick/',
                data=json.dumps({
                    'query': 'Explain quantum computing',
                    'top_k': 6
                }),
                content_type='application/json'
            )
            
            self.stdout.write(f'   Status Code: {response.status_code}')
            
            if response.status_code == 201:
                data = response.json()
                job_id = data.get('job_id')
                self.stdout.write(f'   Job ID: {job_id}')
                self.stdout.write(f'   Query: {data.get("query")}')
                self.stdout.write(self.style.SUCCESS('   ✅ Quick Research endpoint working'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Quick Research failed: {response.status_code}'))
                if hasattr(response, 'json'):
                    self.stdout.write(f'   Error: {response.json()}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Quick Research endpoint error: {str(e)}'))

    def _check_url_patterns(self):
        """Check that URL patterns are properly configured."""
        self.stdout.write('\n🔗 Checking URL Patterns...')
        
        try:
            from django.urls import reverse
            
            # Test URL reverse lookups
            urls_to_test = [
                ('research_agent:intent-fast', 'Intent Fast'),
                ('research_agent:quick-research', 'Quick Research'),
                ('research_agent:system-health', 'System Health'),
                ('research_agent:system-stats', 'System Stats'),
            ]
            
            for url_name, description in urls_to_test:
                try:
                    url = reverse(url_name)
                    self.stdout.write(f'   ✅ {description}: {url}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ {description}: {str(e)}'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ URL pattern check error: {str(e)}'))

    def _check_configuration(self):
        """Check research agent configuration."""
        self.stdout.write('\n⚙️  Checking Configuration...')
        
        # Check if research_agent is in INSTALLED_APPS
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        if 'research_agent' in installed_apps:
            self.stdout.write('   ✅ research_agent in INSTALLED_APPS')
        else:
            self.stdout.write(self.style.ERROR('   ❌ research_agent NOT in INSTALLED_APPS'))
        
        # Check RESEARCH configuration
        research_config = getattr(settings, 'RESEARCH', {})
        if research_config:
            self.stdout.write('   ✅ RESEARCH configuration found')
            self.stdout.write(f'   Search Provider: {research_config.get("SEARCH_PROVIDER", "Not set")}')
            self.stdout.write(f'   Search Top K: {research_config.get("SEARCH_TOP_K", "Not set")}')
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  RESEARCH configuration not found'))
        
        # Check Tavily API key
        tavily_key = getattr(settings, 'TAVILY_API_KEY', '')
        if tavily_key:
            self.stdout.write('   ✅ TAVILY_API_KEY configured')
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  TAVILY_API_KEY not configured'))