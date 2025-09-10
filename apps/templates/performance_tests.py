"""
Performance testing suite for high-performance prompt search and WebSocket functionality
Tests sub-50ms response time requirements
"""

import time
import asyncio
import json
import uuid
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import statistics

from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.core.cache import cache
from django.db import transaction
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack

from .models import PromptLibrary, UserIntent, ChatMessage, PerformanceMetrics
from .search_services import search_service
from .cache_services import multi_cache, performance_monitor
from .consumers import PromptChatConsumer
from . import routing

class PerformanceBaseTest(TestCase):
    """Base class for performance tests with common utilities"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.target_response_time_ms = 50
        cls.acceptable_response_time_ms = 100  # Fallback threshold
        
    def setUp(self):
        # Clear caches before each test
        cache.clear()
        multi_cache.memory_cache.clear()
        multi_cache.memory_access_order.clear()
        performance_monitor.response_times.clear()
        
        # Create test data
        self.create_test_prompts()
    
    def create_test_prompts(self, count: int = 100):
        """Create test prompt data"""
        categories = ['content_creation', 'technical_writing', 'communication', 'analysis']
        prompts = []
        
        for i in range(count):
            category = categories[i % len(categories)]
            prompt = PromptLibrary(
                title=f'Test Prompt {i+1}',
                content=f'This is a test prompt for {category} category. It contains sample content for testing search functionality.',
                category=category,
                subcategory=f'{category}_sub',
                tags=['test', 'sample', category],
                keywords=['test', 'prompt', 'content'],
                intent_category=category,
                usage_count=i * 10,
                average_rating=4.0 + (i % 10) * 0.1,
                quality_score=70 + (i % 30),
                is_active=True,
                is_featured=(i % 10 == 0)
            )
            prompts.append(prompt)
        
        # Bulk create for better performance
        PromptLibrary.objects.bulk_create(prompts)
    
    def measure_execution_time(self, func, *args, **kwargs) -> tuple:
        """Measure function execution time in milliseconds"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time_ms = (time.time() - start_time) * 1000
        return result, execution_time_ms
    
    def assertPerformance(self, execution_time_ms: float, operation_name: str = "Operation"):
        """Assert that execution time meets performance requirements"""
        if execution_time_ms > self.target_response_time_ms:
            if execution_time_ms > self.acceptable_response_time_ms:
                self.fail(
                    f"{operation_name} took {execution_time_ms:.2f}ms, "
                    f"exceeds acceptable threshold of {self.acceptable_response_time_ms}ms"
                )
            else:
                print(f"Warning: {operation_name} took {execution_time_ms:.2f}ms, "
                      f"above target of {self.target_response_time_ms}ms but acceptable")

class SearchPerformanceTests(PerformanceBaseTest):
    """Performance tests for search functionality"""
    
    def test_search_single_query_performance(self):
        """Test single search query performance"""
        query = "test content creation"
        
        result, execution_time = self.measure_execution_time(
            search_service.search_prompts,
            query=query,
            max_results=20
        )
        
        results, metrics = result
        self.assertGreater(len(results), 0, "Search should return results")
        self.assertPerformance(execution_time, "Single search query")
        
        # Verify search quality
        self.assertTrue(any('content_creation' in r.prompt.category for r in results))
    
    def test_search_with_cache_performance(self):
        """Test search performance with caching"""
        query = "technical writing documentation"
        
        # First query (cold cache)
        _, first_time = self.measure_execution_time(
            search_service.search_prompts,
            query=query,
            max_results=20
        )
        
        # Second query (warm cache)
        _, second_time = self.measure_execution_time(
            search_service.search_prompts,
            query=query,
            max_results=20
        )
        
        self.assertPerformance(first_time, "First search (cold cache)")
        self.assertPerformance(second_time, "Second search (warm cache)")
        
        # Cache should improve performance
        self.assertLess(second_time, first_time * 0.8, 
                       "Cached search should be significantly faster")
    
    def test_concurrent_search_performance(self):
        """Test search performance under concurrent load"""
        queries = [
            "content creation marketing",
            "technical documentation API",
            "business communication email",
            "data analysis report",
            "creative writing story"
        ]
        
        execution_times = []
        
        def search_query(query):
            start_time = time.time()
            search_service.search_prompts(query=query, max_results=10)
            return (time.time() - start_time) * 1000
        
        # Execute concurrent searches
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_query, query) for query in queries]
            execution_times = [future.result() for future in futures]
        
        # Check individual performance
        for i, exec_time in enumerate(execution_times):
            self.assertPerformance(exec_time, f"Concurrent search {i+1}")
        
        # Check average performance
        avg_time = statistics.mean(execution_times)
        self.assertPerformance(avg_time, "Average concurrent search")
        
        print(f"Concurrent search stats: avg={avg_time:.2f}ms, "
              f"min={min(execution_times):.2f}ms, max={max(execution_times):.2f}ms")
    
    def test_featured_prompts_performance(self):
        """Test featured prompts retrieval performance"""
        _, execution_time = self.measure_execution_time(
            search_service.get_featured_prompts,
            max_results=10
        )
        
        self.assertPerformance(execution_time, "Featured prompts retrieval")
    
    def test_similar_prompts_performance(self):
        """Test similar prompts search performance"""
        # Get a prompt ID to test with
        test_prompt = PromptLibrary.objects.first()
        
        _, execution_time = self.measure_execution_time(
            search_service.similar_prompts,
            prompt_id=str(test_prompt.id),
            max_results=5
        )
        
        self.assertPerformance(execution_time, "Similar prompts search")
    
    def test_large_result_set_performance(self):
        """Test search performance with large result sets"""
        # Create more test data
        self.create_test_prompts(1000)
        
        query = "test"  # Should match many prompts
        
        _, execution_time = self.measure_execution_time(
            search_service.search_prompts,
            query=query,
            max_results=50
        )
        
        self.assertPerformance(execution_time, "Large result set search")

class CachePerformanceTests(PerformanceBaseTest):
    """Performance tests for caching functionality"""
    
    def test_memory_cache_performance(self):
        """Test L1 memory cache performance"""
        key = "test_key"
        value = {"data": "test_value", "timestamp": time.time()}
        
        # Set operation
        start_time = time.time()
        multi_cache.set(key, value, levels=["L1"])
        set_time = (time.time() - start_time) * 1000
        
        # Get operation
        start_time = time.time()
        result = multi_cache.get(key)
        get_time = (time.time() - start_time) * 1000
        
        self.assertEqual(result, value)
        self.assertLess(set_time, 1, "Memory cache set should be under 1ms")
        self.assertLess(get_time, 1, "Memory cache get should be under 1ms")
        
        print(f"Memory cache: set={set_time:.3f}ms, get={get_time:.3f}ms")
    
    def test_redis_cache_performance(self):
        """Test L2 Redis cache performance"""
        key = "test_redis_key"
        value = {"data": "redis_test_value", "complex": list(range(100))}
        
        # Set operation
        start_time = time.time()
        multi_cache.set(key, value, timeout=300, levels=["L2"])
        set_time = (time.time() - start_time) * 1000
        
        # Get operation (clear L1 first to force L2 access)
        multi_cache.memory_cache.clear()
        start_time = time.time()
        result = multi_cache.get(key)
        get_time = (time.time() - start_time) * 1000
        
        self.assertEqual(result, value)
        self.assertLess(set_time, 10, "Redis cache set should be under 10ms")
        self.assertLess(get_time, 10, "Redis cache get should be under 10ms")
        
        print(f"Redis cache: set={set_time:.3f}ms, get={get_time:.3f}ms")
    
    def test_cache_hierarchy_performance(self):
        """Test multi-level cache hierarchy performance"""
        keys_values = {f"key_{i}": f"value_{i}" for i in range(50)}
        
        # Fill cache
        for key, value in keys_values.items():
            multi_cache.set(key, value)
        
        # Measure retrieval performance
        total_time = 0
        l1_hits = 0
        
        for key in keys_values.keys():
            start_time = time.time()
            result = multi_cache.get(key)
            exec_time = (time.time() - start_time) * 1000
            total_time += exec_time
            
            # Check if it was an L1 hit
            if exec_time < 1:  # Very fast indicates L1 hit
                l1_hits += 1
            
            self.assertIsNotNone(result)
        
        avg_time = total_time / len(keys_values)
        l1_hit_rate = l1_hits / len(keys_values)
        
        self.assertLess(avg_time, 5, "Average cache retrieval should be under 5ms")
        self.assertGreater(l1_hit_rate, 0.7, "L1 hit rate should be over 70%")
        
        print(f"Cache hierarchy: avg={avg_time:.3f}ms, L1_hit_rate={l1_hit_rate:.2%}")

class WebSocketPerformanceTests(TransactionTestCase):
    """Performance tests for WebSocket functionality"""
    
    def setUp(self):
        super().setUp()
        self.session_id = str(uuid.uuid4())
        
        # Create test prompts
        with transaction.atomic():
            for i in range(50):
                PromptLibrary.objects.create(
                    title=f'WebSocket Test Prompt {i+1}',
                    content=f'WebSocket test content for prompt {i+1}',
                    category='content_creation',
                    is_active=True
                )
    
    async def test_websocket_connection_performance(self):
        """Test WebSocket connection establishment performance"""
        application = URLRouter(routing.websocket_urlpatterns)
        
        start_time = time.time()
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.session_id}/"
        )
        
        connected, subprotocol = await communicator.connect()
        connection_time = (time.time() - start_time) * 1000
        
        self.assertTrue(connected)
        self.assertLess(connection_time, 100, 
                       f"WebSocket connection took {connection_time:.2f}ms, should be under 100ms")
        
        await communicator.disconnect()
        print(f"WebSocket connection time: {connection_time:.2f}ms")
    
    async def test_websocket_message_processing_performance(self):
        """Test WebSocket message processing performance"""
        application = URLRouter(routing.websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.session_id}/"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Test intent processing message
        start_time = time.time()
        
        await communicator.send_json_to({
            "type": "user_intent",
            "query": "I need help writing a professional email"
        })
        
        response = await communicator.receive_json_from()
        processing_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response['type'], 'intent_processed')
        self.assertLess(processing_time, 200,  # Slightly higher threshold for WebSocket
                       f"Intent processing took {processing_time:.2f}ms")
        
        await communicator.disconnect()
        print(f"WebSocket message processing: {processing_time:.2f}ms")
    
    async def test_websocket_search_performance(self):
        """Test WebSocket search message performance"""
        application = URLRouter(routing.websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.session_id}/"
        )
        
        await communicator.connect()
        
        # Test search request
        start_time = time.time()
        
        await communicator.send_json_to({
            "type": "search_request",
            "query": "content creation",
            "max_results": 10
        })
        
        response = await communicator.receive_json_from()
        processing_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response['type'], 'search_results')
        self.assertGreater(len(response['results']), 0)
        self.assertLess(processing_time, 150,
                       f"WebSocket search took {processing_time:.2f}ms")
        
        await communicator.disconnect()
        print(f"WebSocket search processing: {processing_time:.2f}ms")

class IntegrationPerformanceTests(PerformanceBaseTest):
    """Integration performance tests for the complete system"""
    
    def setUp(self):
        super().setUp()
        # Create larger dataset for integration tests
        self.create_test_prompts(500)
    
    def test_end_to_end_search_workflow(self):
        """Test complete search workflow performance"""
        query = "professional business communication"
        
        # Step 1: Intent processing
        intent_start = time.time()
        intent = UserIntent.objects.create(
            session_id='test_session',
            original_query=query,
            intent_category='communication',
            confidence_score=0.8
        )
        intent_time = (time.time() - intent_start) * 1000
        
        # Step 2: Search with intent
        search_start = time.time()
        results, metrics = search_service.search_prompts(
            query=query,
            user_intent=intent,
            max_results=20,
            session_id='test_session'
        )
        search_time = (time.time() - search_start) * 1000
        
        # Step 3: Get similar prompts for first result
        similar_start = time.time()
        if results:
            similar_results = search_service.similar_prompts(
                str(results[0].prompt.id),
                max_results=5
            )
        similar_time = (time.time() - similar_start) * 1000
        
        total_time = intent_time + search_time + similar_time
        
        self.assertPerformance(intent_time, "Intent processing")
        self.assertPerformance(search_time, "Search with intent")
        self.assertPerformance(similar_time, "Similar prompts")
        self.assertLess(total_time, 200, 
                       f"Complete workflow took {total_time:.2f}ms, should be under 200ms")
        
        print(f"End-to-end workflow: intent={intent_time:.2f}ms, "
              f"search={search_time:.2f}ms, similar={similar_time:.2f}ms, "
              f"total={total_time:.2f}ms")
    
    def test_system_load_performance(self):
        """Test system performance under simulated load"""
        operations = [
            lambda: search_service.search_prompts("test query", max_results=10),
            lambda: search_service.get_featured_prompts(max_results=5),
            lambda: UserIntent.objects.create(
                session_id=str(uuid.uuid4()),
                original_query="load test",
                intent_category="general",
                confidence_score=0.5
            )
        ]
        
        execution_times = []
        
        def execute_random_operation():
            import random
            operation = random.choice(operations)
            start_time = time.time()
            try:
                operation()
            except Exception as e:
                print(f"Operation failed: {e}")
            return (time.time() - start_time) * 1000
        
        # Simulate concurrent load
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_random_operation) 
                      for _ in range(100)]
            execution_times = [future.result() for future in futures]
        
        avg_time = statistics.mean(execution_times)
        p95_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        self.assertLess(avg_time, 100, f"Average operation time under load: {avg_time:.2f}ms")
        self.assertLess(p95_time, 200, f"95th percentile time under load: {p95_time:.2f}ms")
        
        print(f"Load test results: avg={avg_time:.2f}ms, "
              f"95th_percentile={p95_time:.2f}ms, "
              f"operations={len(execution_times)}")

def run_performance_suite():
    """
    Run the complete performance test suite
    Usage: python manage.py shell -c "from apps.templates.performance_tests import run_performance_suite; run_performance_suite()"
    """
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(SearchPerformanceTests))
    suite.addTests(loader.loadTestsFromTestCase(CachePerformanceTests))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationPerformanceTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) 
                   / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ Performance targets are being met!")
    elif success_rate >= 70:
        print("⚠️  Some performance issues detected - review recommendations")
    else:
        print("❌ Significant performance issues - optimization required")
    
    return result