"""
High-performance search services for 100K+ prompt library
Optimized for sub-50ms response times with caching and indexing
"""

import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from django.db.models import Q, F
from django.core.cache import cache
from django.conf import settings

# Try PostgreSQL search features, fallback if not available
try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
    POSTGRES_SEARCH_AVAILABLE = True
except ImportError:
    SearchQuery = SearchRank = SearchVector = None
    POSTGRES_SEARCH_AVAILABLE = False

try:
    from .models import PromptLibrary, UserIntent, PerformanceMetrics
    MODELS_AVAILABLE = True
except ImportError:
    PromptLibrary = UserIntent = PerformanceMetrics = None
    MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result data structure"""
    prompt: PromptLibrary
    score: float
    relevance_reason: str
    category_match: bool = False
    intent_match: bool = False

class HighPerformanceSearchService:
    """Ultra-fast search service optimized for 100K+ prompts"""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    MAX_RESULTS = 50
    CACHE_KEY_PREFIX = "prompt_search"
    
    def __init__(self):
        self.redis_available = hasattr(settings, 'CACHES') and 'redis' in str(settings.CACHES.get('default', {}))
    
    def search_prompts(
        self, 
        query: str, 
        user_intent: Optional[UserIntent] = None,
        category: Optional[str] = None,
        max_results: int = 20,
        session_id: Optional[str] = None
    ) -> Tuple[List[SearchResult], Dict]:
        """
        Main search method with performance tracking
        
        Returns: (results, performance_metrics)
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query, category, user_intent)
            
            # Try cache first
            cached_results = cache.get(cache_key)
            if cached_results:
                results = self._deserialize_results(cached_results)[:max_results]
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # Log performance
                self._log_performance("search", session_id, elapsed_ms, True, "cache_hit")
                
                return results, {
                    "total_time_ms": elapsed_ms,
                    "from_cache": True,
                    "total_results": len(results)
                }
            
            # Perform search
            results = self._perform_search(query, user_intent, category, max_results)
            
            # Cache results
            cache.set(cache_key, self._serialize_results(results), self.CACHE_TIMEOUT)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Log performance
            self._log_performance("search", session_id, elapsed_ms, True)
            
            return results, {
                "total_time_ms": elapsed_ms,
                "from_cache": False,
                "total_results": len(results)
            }
            
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Search error: {e}")
            
            # Log error
            self._log_performance("search", session_id, elapsed_ms, False, str(e))
            
            return [], {
                "total_time_ms": elapsed_ms,
                "error": str(e),
                "total_results": 0
            }
    
    def _perform_search(
        self, 
        query: str, 
        user_intent: Optional[UserIntent],
        category: Optional[str],
        max_results: int
    ) -> List[SearchResult]:
        """Core search logic with multiple ranking factors"""
        
        # Base queryset with optimizations
        queryset = PromptLibrary.objects.filter(
            is_active=True
        ).select_related().prefetch_related()
        
        # Apply category filter
        if category:
            queryset = queryset.filter(category=category)
        
        # Intent-based filtering
        if user_intent and user_intent.intent_category:
            queryset = queryset.filter(
                Q(intent_category=user_intent.intent_category) |
                Q(category__icontains=user_intent.intent_category)
            )
        
        # Full-text search
        search_query = SearchQuery(query)
        search_vector = SearchVector('title', weight='A') + \
                       SearchVector('content', weight='B') + \
                       SearchVector('category', weight='C')
        
        # Apply search and ranking
        queryset = queryset.annotate(
            search=search_vector,
            rank=SearchRank(F('search'), search_query)
        ).filter(
            Q(search=search_query) |
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__contains=[query])
        ).order_by(
            '-rank',
            '-usage_count',
            '-average_rating',
            '-quality_score'
        )
        
        # Execute query with limit
        prompts = list(queryset[:max_results * 2])  # Get more for better ranking
        
        # Advanced ranking
        results = []
        for prompt in prompts:
            score, reason = self._calculate_relevance_score(prompt, query, user_intent)
            
            if score > 0.1:  # Minimum relevance threshold
                results.append(SearchResult(
                    prompt=prompt,
                    score=score,
                    relevance_reason=reason,
                    category_match=category and prompt.category == category,
                    intent_match=user_intent and prompt.intent_category == user_intent.intent_category
                ))
        
        # Sort by final score and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]
    
    def _calculate_relevance_score(
        self, 
        prompt: PromptLibrary, 
        query: str, 
        user_intent: Optional[UserIntent]
    ) -> Tuple[float, str]:
        """Calculate advanced relevance score with multiple factors"""
        
        score = 0.0
        reasons = []
        
        # Text similarity (base score)
        title_match = query.lower() in prompt.title.lower()
        content_match = query.lower() in prompt.content.lower()
        
        if title_match:
            score += 0.4
            reasons.append("title_match")
        
        if content_match:
            score += 0.3
            reasons.append("content_match")
        
        # Tag matching
        query_words = set(query.lower().split())
        tag_matches = sum(1 for tag in prompt.tags if tag.lower() in query_words)
        if tag_matches:
            score += 0.2 * min(tag_matches / len(query_words), 1.0)
            reasons.append("tag_match")
        
        # Intent alignment
        if user_intent and user_intent.intent_category:
            if prompt.intent_category == user_intent.intent_category:
                score += 0.3
                reasons.append("intent_match")
            elif user_intent.intent_category.lower() in prompt.category.lower():
                score += 0.2
                reasons.append("category_intent_match")
        
        # Quality factors
        quality_bonus = (
            prompt.quality_score / 100 * 0.15 +
            prompt.success_rate * 0.1 +
            min(prompt.average_rating / 5, 1.0) * 0.1 +
            min(prompt.usage_count / 1000, 1.0) * 0.05
        )
        score += quality_bonus
        
        if quality_bonus > 0.1:
            reasons.append("high_quality")
        
        return score, ", ".join(reasons) if reasons else "basic_match"
    
    def search_by_intent(
        self, 
        intent_category: str, 
        confidence_threshold: float = 0.7,
        max_results: int = 20
    ) -> List[SearchResult]:
        """Search prompts specifically by intent category"""
        
        start_time = time.time()
        
        cache_key = f"{self.CACHE_KEY_PREFIX}:intent:{intent_category}:{max_results}"
        cached = cache.get(cache_key)
        
        if cached:
            return self._deserialize_results(cached)[:max_results]
        
        # Query by intent with quality ranking
        queryset = PromptLibrary.objects.filter(
            intent_category=intent_category,
            is_active=True
        ).annotate(
            composite_score=F('quality_score') + F('success_rate') * 20 + F('average_rating') * 10
        ).order_by('-composite_score', '-usage_count')
        
        results = []
        for prompt in queryset[:max_results]:
            score = 0.8 + (prompt.quality_score / 100 * 0.2)  # High base score for intent match
            results.append(SearchResult(
                prompt=prompt,
                score=score,
                relevance_reason="intent_category_exact_match",
                intent_match=True
            ))
        
        # Cache results
        cache.set(cache_key, self._serialize_results(results), self.CACHE_TIMEOUT)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Intent search completed in {elapsed_ms}ms")
        
        return results
    
    def get_featured_prompts(self, category: Optional[str] = None, max_results: int = 10) -> List[SearchResult]:
        """Get high-quality featured prompts for quick access"""
        
        cache_key = f"{self.CACHE_KEY_PREFIX}:featured:{category}:{max_results}"
        cached = cache.get(cache_key)
        
        if cached:
            return self._deserialize_results(cached)
        
        queryset = PromptLibrary.objects.filter(
            is_featured=True,
            is_active=True
        )
        
        if category:
            queryset = queryset.filter(category=category)
        
        queryset = queryset.order_by('-average_rating', '-usage_count')[:max_results]
        
        results = []
        for prompt in queryset:
            results.append(SearchResult(
                prompt=prompt,
                score=0.9,  # High score for featured content
                relevance_reason="featured_prompt"
            ))
        
        # Cache for longer (featured content changes less frequently)
        cache.set(cache_key, self._serialize_results(results), self.CACHE_TIMEOUT * 4)
        
        return results
    
    def similar_prompts(self, prompt_id: str, max_results: int = 5) -> List[SearchResult]:
        """Find similar prompts using tags and category matching"""
        
        try:
            source_prompt = PromptLibrary.objects.get(id=prompt_id)
        except PromptLibrary.DoesNotExist:
            return []
        
        cache_key = f"{self.CACHE_KEY_PREFIX}:similar:{prompt_id}:{max_results}"
        cached = cache.get(cache_key)
        
        if cached:
            return self._deserialize_results(cached)
        
        # Find similar by category and tags
        queryset = PromptLibrary.objects.filter(
            is_active=True
        ).exclude(id=prompt_id)
        
        # Same category gets priority
        same_category = queryset.filter(category=source_prompt.category)
        
        # Tag overlap calculation
        if source_prompt.tags:
            # Find prompts with overlapping tags
            similar_by_tags = queryset.filter(
                tags__overlap=source_prompt.tags
            ).annotate(
                tag_score=F('average_rating') + F('usage_count') / 100
            ).order_by('-tag_score')
            
            # Combine and deduplicate
            combined_ids = list(same_category.values_list('id', flat=True)[:max_results//2]) + \
                          list(similar_by_tags.values_list('id', flat=True)[:max_results//2])
            
            final_queryset = queryset.filter(id__in=combined_ids).order_by('-average_rating')
        else:
            final_queryset = same_category.order_by('-average_rating')
        
        results = []
        for prompt in final_queryset[:max_results]:
            # Calculate similarity score
            tag_overlap = len(set(source_prompt.tags) & set(prompt.tags)) if source_prompt.tags and prompt.tags else 0
            category_match = prompt.category == source_prompt.category
            
            score = 0.3 + (0.4 if category_match else 0) + (tag_overlap * 0.1)
            
            results.append(SearchResult(
                prompt=prompt,
                score=score,
                relevance_reason=f"similar_content ({'category_match' if category_match else 'tag_overlap'})"
            ))
        
        # Cache for extended period
        cache.set(cache_key, self._serialize_results(results), self.CACHE_TIMEOUT * 2)
        
        return results
    
    def _generate_cache_key(self, query: str, category: Optional[str], user_intent: Optional[UserIntent]) -> str:
        """Generate consistent cache key for search parameters"""
        key_parts = [self.CACHE_KEY_PREFIX, query.lower().replace(" ", "_")]
        
        if category:
            key_parts.append(f"cat:{category}")
        
        if user_intent and user_intent.intent_category:
            key_parts.append(f"intent:{user_intent.intent_category}")
        
        return ":".join(key_parts)[:200]  # Limit key length
    
    def _serialize_results(self, results: List[SearchResult]) -> str:
        """Serialize search results for caching"""
        data = []
        for result in results:
            data.append({
                'prompt_id': str(result.prompt.id),
                'score': result.score,
                'relevance_reason': result.relevance_reason,
                'category_match': result.category_match,
                'intent_match': result.intent_match
            })
        return json.dumps(data)
    
    def _deserialize_results(self, cached_data: str) -> List[SearchResult]:
        """Deserialize cached search results"""
        try:
            data = json.loads(cached_data)
            prompt_ids = [item['prompt_id'] for item in data]
            
            # Bulk fetch prompts
            prompts_dict = {
                str(p.id): p for p in 
                PromptLibrary.objects.filter(id__in=prompt_ids).select_related()
            }
            
            results = []
            for item in data:
                prompt_id = item['prompt_id']
                if prompt_id in prompts_dict:
                    results.append(SearchResult(
                        prompt=prompts_dict[prompt_id],
                        score=item['score'],
                        relevance_reason=item['relevance_reason'],
                        category_match=item['category_match'],
                        intent_match=item['intent_match']
                    ))
            
            return results
        except Exception as e:
            logger.error(f"Cache deserialization error: {e}")
            return []
    
    def _log_performance(
        self, 
        operation_type: str, 
        session_id: Optional[str], 
        response_time_ms: int, 
        success: bool, 
        error_message: str = ""
    ):
        """Log performance metrics"""
        try:
            PerformanceMetrics.objects.create(
                operation_type=operation_type,
                session_id=session_id,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                endpoint="search_service"
            )
        except Exception as e:
            logger.error(f"Failed to log performance: {e}")
    
    def clear_search_cache(self, pattern: Optional[str] = None):
        """Clear search cache (admin utility)"""
        if pattern:
            # Clear specific pattern
            cache.delete_many(cache.keys(f"{self.CACHE_KEY_PREFIX}:{pattern}*"))
        else:
            # Clear all search cache
            cache.delete_many(cache.keys(f"{self.CACHE_KEY_PREFIX}:*"))
    
    def warm_cache(self, popular_queries: List[str]):
        """Pre-warm cache with popular search queries"""
        for query in popular_queries:
            try:
                self.search_prompts(query, max_results=10)
                logger.info(f"Warmed cache for query: {query}")
            except Exception as e:
                logger.error(f"Cache warming failed for '{query}': {e}")

# Global service instance
search_service = HighPerformanceSearchService()