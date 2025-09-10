"""
Tests for RAG Agent system
"""

import json
import asyncio
from unittest.mock import patch, MagicMock
from django.test import TestCase, AsyncTransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path

from apps.ai_services.rag_service import (
    DocumentIndexer, RAGRetriever, RAGAgent, 
    OptimizationRequest, get_rag_agent
)
from apps.billing.models import UserSubscription, SubscriptionPlan, UsageQuota
from apps.templates.enhanced_consumer import EnhancedChatConsumer

User = get_user_model()


class DocumentIndexerTest(TestCase):
    """Test document indexing functionality"""
    
    def setUp(self):
        self.indexer = DocumentIndexer()
    
    def test_indexer_initialization(self):
        """Test indexer initializes correctly"""
        self.assertEqual(self.indexer.chunk_size, 1000)
        self.assertEqual(self.indexer.chunk_overlap, 150)
        self.assertEqual(self.indexer.collection_name, 'prompt-knowledge')
        self.assertTrue(self.indexer.index_path.exists())
    
    @patch('apps.ai_services.rag_service.LANGCHAIN_AVAILABLE', True)
    def test_load_markdown_files(self):
        """Test loading markdown files"""
        docs = self.indexer._load_markdown_files()
        
        # Should find some markdown files in the project
        self.assertGreater(len(docs), 0)
        
        # Check document structure
        if docs:
            doc = docs[0]
            self.assertIsInstance(doc.id, str)
            self.assertIsInstance(doc.content, str)
            self.assertIn('type', doc.metadata)
            self.assertEqual(doc.metadata['type'], 'markdown')
    
    def test_load_template_database(self):
        """Test loading templates from database"""
        # Create a test template
        from apps.templates.models import PromptLibrary
        
        template = PromptLibrary.objects.create(
            title="Test Template",
            content="This is a test template for optimization",
            category="test",
            quality_score=0.8,
            is_active=True
        )
        
        docs = self.indexer._load_template_database()
        
        # Should find our test template
        template_docs = [d for d in docs if d.metadata.get('type') == 'template']
        self.assertGreater(len(template_docs), 0)
        
        # Check document structure
        if template_docs:
            doc = template_docs[0]
            self.assertEqual(doc.metadata['type'], 'template')
            self.assertIn('quality_score', doc.metadata)


class RAGAgentAPITest(APITestCase):
    """Test RAG agent REST API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        # Create subscription plan and user subscription
        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan",
            plan_type="basic",
            daily_template_limit=10,
            daily_copy_limit=5
        )
        
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_optimize_prompt_endpoint(self):
        """Test the prompt optimization endpoint"""
        url = reverse('agent-optimize')
        data = {
            'session_id': 'test-session-123',
            'original': 'Write a good email',
            'mode': 'fast',
            'context': {'intent': 'business'},
            'budget': {'tokens_in': 1000, 'tokens_out': 500, 'max_credits': 3}
        }
        
        with patch('apps.ai_services.rag_service.LANGCHAIN_AVAILABLE', False):
            response = self.client.post(url, data, format='json')
        
        # Should succeed with fallback optimization
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('optimized', response_data)
        self.assertIn('diff_summary', response_data)
        self.assertIn('usage', response_data)
        self.assertIn('citations', response_data)
    
    def test_optimize_prompt_invalid_data(self):
        """Test endpoint with invalid data"""
        url = reverse('agent-optimize')
        data = {
            'session_id': 'test-session-123',
            # Missing 'original' field
            'mode': 'fast'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimize_prompt_too_long(self):
        """Test endpoint with overly long prompt"""
        url = reverse('agent-optimize')
        data = {
            'session_id': 'test-session-123',
            'original': 'x' * 15000,  # Too long
            'mode': 'fast'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_agent_stats_endpoint(self):
        """Test the agent stats endpoint"""
        url = reverse('agent-stats')
        
        # Only staff users can access stats
        self.user.is_staff = True
        self.user.save()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('index_status', response_data)
        self.assertIn('user_usage', response_data)
        self.assertIn('system_metrics', response_data)
    
    def test_agent_stats_non_staff(self):
        """Test stats endpoint access denied for non-staff"""
        url = reverse('agent-stats')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CreditTrackingTest(TestCase):
    """Test credit tracking and budget enforcement"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='credituser',
            password='testpass'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name="Credit Test Plan",
            plan_type="basic",
            daily_template_limit=5
        )
        
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active'
        )
    
    def test_credit_check_sufficient(self):
        """Test credit checking with sufficient credits"""
        from apps.ai_services.agent_views import CreditTracker
        
        result = CreditTracker.check_user_credits(self.user, 2)
        
        self.assertTrue(result['has_credits'])
        self.assertEqual(result['requested'], 2)
        self.assertTrue(result['subscription_active'])
    
    def test_credit_consumption(self):
        """Test credit consumption tracking"""
        from apps.ai_services.agent_views import CreditTracker
        
        # Consume some credits
        success = CreditTracker.consume_credits(self.user, 3, 100, 50)
        self.assertTrue(success)
        
        # Check usage was recorded
        from django.utils import timezone
        today = timezone.now().date()
        quota = UsageQuota.objects.get(
            user=self.user,
            quota_type='daily',
            quota_date=today
        )
        
        self.assertEqual(quota.api_calls_made, 3)


class RAGAgentIntegrationTest(TestCase):
    """Integration tests for RAG agent"""
    
    def setUp(self):
        # Mock LangChain availability
        self.langchain_patch = patch('apps.ai_services.rag_service.LANGCHAIN_AVAILABLE', False)
        self.langchain_patch.start()
    
    def tearDown(self):
        self.langchain_patch.stop()
    
    def test_agent_optimization_fallback(self):
        """Test agent optimization with fallback implementation"""
        agent = get_rag_agent()
        
        request = OptimizationRequest(
            session_id="test-session",
            original="write email",
            mode="fast",
            context={"intent": "business"},
            budget={"tokens_in": 1000, "tokens_out": 500, "max_credits": 2}
        )
        
        # Run the optimization (should use fallback)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.optimize_prompt(request))
            
            self.assertIsInstance(result.optimized, str)
            self.assertIsInstance(result.diff_summary, str)
            self.assertIsInstance(result.usage, dict)
            self.assertIn('tokens_in', result.usage)
            self.assertIn('tokens_out', result.usage)
            self.assertIn('credits', result.usage)
            
        finally:
            loop.close()


class MockLangChainTest(TestCase):
    """Test RAG system behavior when LangChain is not available"""
    
    def test_indexer_without_langchain(self):
        """Test indexer gracefully handles missing LangChain"""
        with patch('apps.ai_services.rag_service.LANGCHAIN_AVAILABLE', False):
            indexer = DocumentIndexer()
            self.assertIsNone(indexer.embeddings)
            
            # Should still be able to load documents
            docs = indexer.load_documents()
            self.assertIsInstance(docs, list)
    
    def test_retriever_without_langchain(self):
        """Test retriever gracefully handles missing LangChain"""
        with patch('apps.ai_services.rag_service.LANGCHAIN_AVAILABLE', False):
            retriever = RAGRetriever()
            self.assertIsNone(retriever.vector_store)
            
            # Should return empty results gracefully
            docs = retriever.retrieve_documents("test query")
            self.assertEqual(docs, [])
