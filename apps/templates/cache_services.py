"""
High-performance caching service for sub-50ms response times
Multi-level caching strategy with Redis and in-memory optimization
"""

import time
import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet

# Try Redis-specific features
try:
    from django.core.cache.backends.redis import RedisCache
    REDIS_AVAILABLE = True
except ImportError:
    RedisCache = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class MultiLevelCache:
    """
    Multi-level caching system:
    Level 1: In-memory Python dict (fastest, limited size)
    Level 2: Redis cache (fast, shared across instances)
    Level 3: Database with optimized queries
    """
    
    def __init__(self, max_memory_items: int = 1000):
        self.memory_cache = {}
        self.memory_access_order = []
        self.max_memory_items = max_memory_items
        self.hit_stats = {"L1": 0, "L2": 0, "L3": 0, "miss": 0}
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def get(self, key: str, default=None) -> Any:
        """Get item from cache with performance tracking"""
        start_time = time.time()
        
        try:
            # Level 1: Memory cache
            if key in self.memory_cache:
                self._update_access_order(key)
                self.hit_stats["L1"] += 1
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms < 50:  # Target sub-50ms
                    logger.debug(f"L1 cache hit: {key} ({elapsed_ms:.2f}ms)")
                return self.memory_cache[key]
            
            # Level 2: Redis cache
            redis_value = cache.get(key)
            if redis_value is not None:
                # Store in memory cache for next time
                self._set_memory_cache(key, redis_value)
                self.hit_stats["L2"] += 1
                elapsed_ms = (time.time() - start_time) * 1000
                logger.debug(f"L2 cache hit: {key} ({elapsed_ms:.2f}ms)")
                return redis_value
            
            # Cache miss
            self.hit_stats["miss"] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: int = 300, levels: List[str] = None):
        """Set item in cache levels"""
        if levels is None:
            levels = ["L1", "L2"]  # Default to both levels
        
        try:
            # Level 1: Memory cache
            if "L1" in levels:
                self._set_memory_cache(key, value)
            
            # Level 2: Redis cache
            if "L2" in levels:
                cache.set(key, value, timeout)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    def delete(self, key: str):
        """Delete from all cache levels"""
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                if key in self.memory_access_order:
                    self.memory_access_order.remove(key)
            
            # Remove from Redis
            cache.delete(key)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    def _set_memory_cache(self, key: str, value: Any):
        """Set item in memory cache with LRU eviction"""
        # Add/update item
        self.memory_cache[key] = value
        self._update_access_order(key)
        
        # Evict oldest items if necessary
        while len(self.memory_cache) > self.max_memory_items:
            oldest_key = self.memory_access_order.pop(0)
            if oldest_key in self.memory_cache:
                del self.memory_cache[oldest_key]
    
    def _update_access_order(self, key: str):
        """Update LRU access order"""
        if key in self.memory_access_order:
            self.memory_access_order.remove(key)
        self.memory_access_order.append(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = sum(self.hit_stats.values())
        if total_requests == 0:
            return {"hit_rate": 0, "levels": self.hit_stats}
        
        return {
            "hit_rate": (total_requests - self.hit_stats["miss"]) / total_requests,
            "levels": self.hit_stats,
            "memory_items": len(self.memory_cache),
            "memory_utilization": len(self.memory_cache) / self.max_memory_items
        }
    
    def clear_stats(self):
        """Clear performance statistics"""
        self.hit_stats = {"L1": 0, "L2": 0, "L3": 0, "miss": 0}

# Global cache instance
multi_cache = MultiLevelCache()

def cached_function(
    timeout: int = 300,
    key_prefix: str = "",
    cache_levels: List[str] = None,
    vary_on: List[str] = None
):
    """
    Decorator for caching function results with automatic key generation
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        cache_levels: Which cache levels to use ["L1", "L2"]
        vary_on: List of parameter names to include in cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func, key_prefix, args, kwargs, vary_on)
            
            # Try to get from cache
            result = multi_cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Cache the result
            multi_cache.set(cache_key, result, timeout, cache_levels)
            
            # Log performance
            if execution_time > 50:
                logger.warning(f"Slow function execution: {func.__name__} ({execution_time:.2f}ms)")
            
            return result
        return wrapper
    return decorator

async def async_cached_function(
    timeout: int = 300,
    key_prefix: str = "",
    cache_levels: List[str] = None,
    vary_on: List[str] = None
):
    """Async version of cached_function decorator"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func, key_prefix, args, kwargs, vary_on)
            
            # Try to get from cache
            result = multi_cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute async function and cache result
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Cache the result
            multi_cache.set(cache_key, result, timeout, cache_levels)
            
            # Log performance
            if execution_time > 50:
                logger.warning(f"Slow async function execution: {func.__name__} ({execution_time:.2f}ms)")
            
            return result
        return wrapper
    return decorator

class QuerysetCache:
    """Specialized caching for Django QuerySets with smart invalidation"""
    
    @staticmethod
    def cache_queryset(
        queryset: QuerySet,
        cache_key: str,
        timeout: int = 300,
        transform_func: Callable = None
    ) -> List[Dict]:
        """Cache queryset results with optional transformation"""
        
        # Try cache first
        cached_result = multi_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute queryset
        start_time = time.time()
        
        # Use select_related and prefetch_related for optimization
        if hasattr(queryset, 'select_related'):
            queryset = queryset.select_related()
        
        # Convert to list and apply transformation
        if transform_func:
            result = [transform_func(item) for item in queryset]
        else:
            result = list(queryset.values())
        
        execution_time = (time.time() - start_time) * 1000
        
        # Cache the result
        multi_cache.set(cache_key, result, timeout)
        
        # Log performance
        logger.debug(f"QuerySet cached: {cache_key} ({execution_time:.2f}ms, {len(result)} items)")
        
        return result
    
    @staticmethod
    def invalidate_model_cache(model_name: str, instance_id: str = None):
        """Invalidate cache entries for a specific model"""
        # This would typically use cache tagging or pattern matching
        # For simplicity, we'll implement basic pattern invalidation
        
        patterns_to_clear = [
            f"search:*",  # Clear search caches
            f"queryset:{model_name}:*",  # Clear model-specific caches
            f"intent:*",  # Clear intent caches if prompt-related
        ]
        
        if instance_id:
            patterns_to_clear.append(f"*:{instance_id}:*")
        
        for pattern in patterns_to_clear:
            try:
                # In production, use Redis SCAN with pattern
                cache.delete_many(cache.keys(pattern))
            except Exception as e:
                logger.error(f"Cache invalidation error for pattern {pattern}: {e}")

class PerformanceOptimizedCache:
    """Cache service optimized for specific use cases"""
    
    @staticmethod
    @cached_function(timeout=600, key_prefix="featured_prompts", cache_levels=["L1", "L2"])
    def get_featured_prompts(category: Optional[str] = None, max_count: int = 10) -> List[Dict]:
        """Cache featured prompts with longer timeout"""
        from .models import PromptLibrary
        
        queryset = PromptLibrary.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('-average_rating', '-usage_count')
        
        if category:
            queryset = queryset.filter(category=category)
        
        return QuerysetCache.cache_queryset(
            queryset[:max_count],
            f"featured_prompts:{category}:{max_count}",
            timeout=600,
            transform_func=lambda p: {
                'id': str(p.id),
                'title': p.title,
                'category': p.category,
                'average_rating': p.average_rating,
                'usage_count': p.usage_count
            }
        )
    
    @staticmethod
    @cached_function(timeout=300, key_prefix="popular_categories", cache_levels=["L1", "L2"])
    def get_popular_categories(limit: int = 10) -> List[Dict]:
        """Cache popular categories"""
        from .models import PromptLibrary
        from django.db.models import Count, Avg
        
        return list(PromptLibrary.objects.filter(
            is_active=True
        ).values('category').annotate(
            prompt_count=Count('id'),
            avg_rating=Avg('average_rating')
        ).order_by('-prompt_count')[:limit])
    
    @staticmethod
    def cache_user_session(session_id: str, data: Dict, timeout: int = 1800):
        """Cache user session data with 30-minute timeout"""
        cache_key = f"session:{session_id}"
        multi_cache.set(cache_key, data, timeout, ["L2"])  # Only Redis for sessions
    
    @staticmethod
    def get_user_session(session_id: str) -> Optional[Dict]:
        """Get cached user session data"""
        cache_key = f"session:{session_id}"
        return multi_cache.get(cache_key)
    
    @staticmethod
    def preload_hot_data():
        """Preload frequently accessed data into cache"""
        try:
            logger.info("Starting cache preload...")
            
            # Preload featured prompts
            PerformanceOptimizedCache.get_featured_prompts()
            
            # Preload popular categories
            PerformanceOptimizedCache.get_popular_categories()
            
            # Preload top-rated prompts by category
            from .models import PromptLibrary
            categories = PromptLibrary.objects.values_list('category', flat=True).distinct()[:10]
            
            for category in categories:
                PerformanceOptimizedCache.get_featured_prompts(category=category)
            
            logger.info("Cache preload completed")
            
        except Exception as e:
            logger.error(f"Cache preload error: {e}")

def _generate_cache_key(
    func: Callable,
    prefix: str,
    args: tuple,
    kwargs: dict,
    vary_on: List[str] = None
) -> str:
    """Generate consistent cache key for function calls"""
    key_parts = [prefix or func.__name__]
    
    # Include specific arguments if vary_on is specified
    if vary_on:
        # Get function signature to map args to parameter names
        import inspect
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        
        # Map positional args to parameter names
        args_dict = dict(zip(param_names, args))
        args_dict.update(kwargs)
        
        # Include only specified parameters in cache key
        for param in vary_on:
            if param in args_dict:
                key_parts.append(f"{param}:{args_dict[param]}")
    else:
        # Include all arguments in cache key
        if args:
            args_str = ":".join(str(arg) for arg in args)
            key_parts.append(f"args:{hashlib.md5(args_str.encode()).hexdigest()[:8]}")
        
        if kwargs:
            kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key_parts.append(f"kwargs:{hashlib.md5(kwargs_str.encode()).hexdigest()[:8]}")
    
    return ":".join(key_parts)

def warm_cache_startup():
    """Warm up cache during application startup"""
    logger.info("Starting cache warmup...")
    
    try:
        # Run preload in background
        multi_cache.executor.submit(PerformanceOptimizedCache.preload_hot_data)
        logger.info("Cache warmup initiated")
    except Exception as e:
        logger.error(f"Cache warmup error: {e}")

def get_cache_performance_report() -> Dict[str, Any]:
    """Get comprehensive cache performance report"""
    stats = multi_cache.get_stats()
    
    # Add Redis-specific stats if available
    try:
        if hasattr(cache, '_cache'):
            redis_info = cache._cache.get_client().info('memory')
            stats['redis'] = {
                'used_memory_human': redis_info.get('used_memory_human', 'N/A'),
                'used_memory_peak_human': redis_info.get('used_memory_peak_human', 'N/A')
            }
    except Exception:
        pass
    
    return stats

# Cache performance monitoring
class CachePerformanceMonitor:
    """Monitor cache performance and automatically optimize"""
    
    def __init__(self):
        self.response_times = []
        self.max_samples = 100
    
    def record_response_time(self, operation: str, response_time_ms: float):
        """Record response time for performance monitoring"""
        self.response_times.append({
            'operation': operation,
            'time_ms': response_time_ms,
            'timestamp': time.time()
        })
        
        # Keep only recent samples
        if len(self.response_times) > self.max_samples:
            self.response_times.pop(0)
        
        # Alert if response time exceeds target
        if response_time_ms > 50:
            logger.warning(f"Slow cache operation: {operation} ({response_time_ms:.2f}ms)")
    
    def get_average_response_time(self, operation: str = None) -> float:
        """Get average response time for operations"""
        filtered_times = self.response_times
        
        if operation:
            filtered_times = [r for r in self.response_times if r['operation'] == operation]
        
        if not filtered_times:
            return 0.0
        
        return sum(r['time_ms'] for r in filtered_times) / len(filtered_times)
    
    def recommend_optimizations(self) -> List[str]:
        """Recommend cache optimizations based on performance data"""
        recommendations = []
        avg_time = self.get_average_response_time()
        
        if avg_time > 50:
            recommendations.append("Consider increasing memory cache size")
        
        if multi_cache.get_stats()['hit_rate'] < 0.8:
            recommendations.append("Low cache hit rate - review cache keys and timeouts")
        
        return recommendations

# Global performance monitor
performance_monitor = CachePerformanceMonitor()