"""
Enhanced tests for research agent functionality.
"""
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json
import uuid

from .models import ResearchJob, SourceDoc, Chunk, ResearchAnswer
from .contracts import InsightCard, CitationModel
from .guards import QualityGuardRunner, validate_card_quality

User = get_user_model()


class ResearchJobModelTests(TestCase):
    """Test ResearchJob model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_research_job(self):
        """Test creating a research job."""
        job = ResearchJob.objects.create(
            query="What is artificial intelligence?",
            top_k=5,
            created_by=self.user
        )
        
        self.assertEqual(job.query, "What is artificial intelligence?")
        self.assertEqual(job.top_k, 5)
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.created_by, self.user)
        self.assertIsNotNone(job.id)
    
    def test_job_string_representation(self):
        """Test job string representation."""
        job = ResearchJob.objects.create(
            query="What is machine learning and how does it work?",
            created_by=self.user
        )
        
        expected = "Research Job: What is machine learning and how does it work?..."
        self.assertEqual(str(job), expected)


class ResearchAPITests(TestCase):
    """Test research agent API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_quick_research_endpoint(self):
        """Test quick research endpoint."""
        url = reverse('research_agent:quick-research')
        data = {
            'query': 'What is Django framework?',
            'top_k': 5
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('job_id', response.data)
        self.assertIn('query', response.data)
        self.assertIn('stream_url', response.data)
        self.assertIn('cards_stream_url', response.data)
    
    def test_intent_fast_endpoint(self):
        """Test fast intent endpoint."""
        url = reverse('research_agent:intent-fast')
        data = {
            'query': 'Explain quantum computing basics',
            'top_k': 6
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('intent_id', response.data)
        self.assertIn('query', response.data)
        # Warm card is optional
        if 'warm_card' in response.data:
            warm_card = response.data['warm_card']
            self.assertIn('id', warm_card)
            self.assertIn('title', warm_card)
            self.assertIn('content', warm_card)
    
    def test_invalid_query_validation(self):
        """Test validation of invalid queries."""
        url = reverse('research_agent:quick-research')
        data = {}  # Missing required query
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('query', response.data)
    
    def test_system_health_endpoint(self):
        """Test system health endpoint."""
        url = reverse('research_agent:system-health')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Health check might fail in test environment, but should return a response
        self.assertIn('overall', response.data)
    
    def test_system_stats_endpoint(self):
        """Test system statistics endpoint."""
        # Create some test data
        ResearchJob.objects.create(
            query="Test query 1",
            status="done"
        )
        ResearchJob.objects.create(
            query="Test query 2", 
            status="error"
        )
        
        url = reverse('research_agent:system-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_jobs', response.data)
        self.assertIn('completed_jobs', response.data)
        self.assertIn('failed_jobs', response.data)


class InsightCardTests(TestCase):
    """Test InsightCard contract and validation."""
    
    def test_valid_insight_card(self):
        """Test creating a valid insight card."""
        citations = [
            CitationModel(
                n=1,
                url="https://example.com/article1",
                title="Test Article 1",
                score=0.8
            )
        ]
        
        card = InsightCard(
            id=str(uuid.uuid4()),
            title="Test Card Title",
            content="This is a test card with sufficient content to pass validation requirements.",
            citations=citations,
            confidence=0.8,
            authority=0.7
        )
        
        self.assertTrue(card.passes_quality_guards())
        self.assertEqual(len(card.citations), 1)
        self.assertGreaterEqual(card.confidence, 0.5)
        self.assertGreaterEqual(card.authority, 0.6)
    
    def test_card_quality_guards(self):
        """Test quality guard validation."""
        # Card with no citations (should fail)
        card_no_citations = InsightCard(
            id=str(uuid.uuid4()),
            title="No Citations Card",
            content="This card has no citations and should fail validation.",
            citations=[],
            confidence=0.8,
            authority=0.7
        )
        
        self.assertFalse(validate_card_quality(card_no_citations))
        
        # Card with low authority (should fail)
        citations = [CitationModel(n=1, url="https://example.com", title="Test", score=0.5)]
        card_low_authority = InsightCard(
            id=str(uuid.uuid4()),
            title="Low Authority Card",
            content="This card has low authority and should fail validation.",
            citations=citations,
            confidence=0.8,
            authority=0.3  # Below threshold
        )
        
        self.assertFalse(validate_card_quality(card_low_authority))


class QualityGuardTests(TestCase):
    """Test quality guard functionality."""
    
    def test_quality_guard_runner(self):
        """Test quality guard runner with multiple cards."""
        # Create test cards
        good_card = InsightCard(
            id=str(uuid.uuid4()),
            title="Good Card",
            content="This is a high-quality card with sufficient content and proper citations.",
            citations=[CitationModel(n=1, url="https://example.com", title="Source", score=0.8)],
            confidence=0.8,
            authority=0.7
        )
        
        bad_card = InsightCard(
            id=str(uuid.uuid4()),
            title="Bad Card",
            content="Short",  # Too short
            citations=[],  # No citations
            confidence=0.3,  # Low confidence
            authority=0.2   # Low authority
        )
        
        runner = QualityGuardRunner("test query")
        results = runner.validate_cards([good_card, bad_card])
        
        self.assertEqual(results['total_cards'], 2)
        self.assertEqual(results['passed_cards'], 1)
        self.assertEqual(results['failed_cards'], 1)
        self.assertEqual(len(results['valid_cards']), 1)
        self.assertEqual(results['valid_cards'][0].id, good_card.id)


class SSEStreamingTests(TransactionTestCase):
    """Test SSE streaming functionality."""
    
    def setUp(self):
        self.client = APIClient()
        self.job = ResearchJob.objects.create(
            query="Test streaming query",
            status="queued"
        )
    
    def test_stream_job_progress_endpoint_exists(self):
        """Test that stream endpoint exists and returns proper headers."""
        url = reverse('research_agent:stream-job-progress', kwargs={'job_id': self.job.id})
        
        response = self.client.get(url)
        
        # Should return 200 for existing job
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')
    
    def test_stream_cards_endpoint_exists(self):
        """Test that card stream endpoint exists."""
        url = reverse('research_agent:stream-cards', kwargs={'job_id': self.job.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/event-stream')
    
    def test_stream_nonexistent_job(self):
        """Test streaming for non-existent job."""
        fake_id = uuid.uuid4()
        url = reverse('research_agent:stream-job-progress', kwargs={'job_id': fake_id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class UtilityFunctionTests(TestCase):
    """Test utility functions."""
    
    def test_clean_html_to_text(self):
        """Test HTML cleaning functionality."""
        from .utils import clean_html_to_text
        
        html = "<html><body><h1>Test Title</h1><p>Test paragraph with <a href='#'>link</a>.</p><script>alert('test');</script></body></html>"
        
        clean_text = clean_html_to_text(html)
        
        self.assertIn("Test Title", clean_text)
        self.assertIn("Test paragraph", clean_text)
        self.assertNotIn("<script>", clean_text)
        self.assertNotIn("alert", clean_text)
    
    def test_validate_url(self):
        """Test URL validation."""
        from .utils import validate_url
        
        # Valid URLs
        self.assertTrue(validate_url("https://example.com"))
        self.assertTrue(validate_url("http://test.org/path"))
        
        # Invalid URLs
        self.assertFalse(validate_url("not-a-url"))
        self.assertFalse(validate_url("ftp://example.com"))
        self.assertFalse(validate_url("https://localhost"))  # Blocked
        self.assertFalse(validate_url("http://127.0.0.1"))  # Blocked
    
    def test_extract_domain(self):
        """Test domain extraction."""
        from .utils import extract_domain
        
        self.assertEqual(extract_domain("https://example.com/path"), "example.com")
        self.assertEqual(extract_domain("http://test.org"), "test.org")
        self.assertEqual(extract_domain("invalid"), "invalid")
        self.assertEqual(extract_domain(""), "")
