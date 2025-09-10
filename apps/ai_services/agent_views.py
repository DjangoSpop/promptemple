"""
RAG Agent API Views for Prompt Optimization
Integrates with existing credit system and provides budget-aware optimization
"""

import time
import hashlib
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import uuid

from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes

from apps.billing.models import UsageQuota, UserSubscription
from apps.ai_services.rag_service import get_rag_agent, OptimizationRequest
from apps.templates.models import PromptOptimization

logger = logging.getLogger(__name__)
User = get_user_model()


class CreditTracker:
    """Handles credit tracking and budget enforcement"""
    
    @staticmethod
    def check_user_credits(user, requested_credits: int) -> Dict[str, Any]:
        """Check if user has sufficient credits"""
        try:
            subscription = UserSubscription.objects.get(user=user)
            
            # Get today's quota
            today = timezone.now().date()
            quota, created = UsageQuota.objects.get_or_create(
                user=user,
                quota_type='daily',
                quota_date=today,
                defaults={
                    'template_limit': subscription.plan.daily_template_limit,
                    'copy_limit': subscription.plan.daily_copy_limit,
                    'api_call_limit': 50  # Default API limit
                }
            )
            
            # Check if user can afford the request
            available_credits = quota.api_call_limit - quota.api_calls_made
            
            return {
                "has_credits": available_credits >= requested_credits,
                "available": available_credits,
                "requested": requested_credits,
                "subscription_active": subscription.is_active,
                "is_trial": subscription.is_trial
            }
            
        except UserSubscription.DoesNotExist:
            # No subscription - trial user
            return {
                "has_credits": requested_credits <= 3,  # Trial limit
                "available": 3,
                "requested": requested_credits,
                "subscription_active": False,
                "is_trial": True
            }
    
    @staticmethod
    def consume_credits(user, credits_used: int, tokens_in: int, tokens_out: int) -> bool:
        """Consume credits and track usage"""
        try:
            with transaction.atomic():
                today = timezone.now().date()
                quota, created = UsageQuota.objects.get_or_create(
                    user=user,
                    quota_type='daily',
                    quota_date=today,
                    defaults={
                        'template_limit': 50,
                        'copy_limit': 30,
                        'api_call_limit': 50
                    }
                )
                
                # Update usage
                quota.api_calls_made += credits_used
                quota.save()
                
                # Create optimization record
                PromptOptimization.objects.create(
                    user=user,
                    original_prompt="[RAG Agent Request]",
                    optimized_prompt="[RAG Agent Response]",
                    processing_time_ms=0,  # Will be updated
                    tokens_used=tokens_in + tokens_out,
                    credits_consumed=credits_used
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to consume credits: {e}")
            return False


def generate_idempotency_key(session_id: str, content: str) -> str:
    """Generate idempotency key for deduplication"""
    combined = f"{session_id}:{content}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


@extend_schema(
    summary="Optimize prompt using RAG agent",
    description="""
    Optimize a prompt using Retrieval-Augmented Generation with internal knowledge base.
    
    Features:
    - Retrieves relevant context from templates, docs, and usage history
    - Budget-aware optimization with token/credit limits
    - Idempotent requests based on session_id + content hash
    - Trial user limitations and subscription enforcement
    """,
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Unique session identifier"},
                "original": {"type": "string", "description": "Original prompt to optimize"},
                "mode": {
                    "type": "string", 
                    "enum": ["fast", "deep"],
                    "default": "fast",
                    "description": "Optimization mode"
                },
                "context": {
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string", "description": "Intended use case"},
                        "domain": {"type": "string", "description": "Domain context"}
                    }
                },
                "budget": {
                    "type": "object",
                    "properties": {
                        "tokens_in": {"type": "integer", "default": 2000},
                        "tokens_out": {"type": "integer", "default": 800},
                        "max_credits": {"type": "integer", "default": 5}
                    }
                }
            },
            "required": ["session_id", "original"]
        }
    },
    responses={
        200: {
            "description": "Optimization successful",
            "content": {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "optimized": {"type": "string"},
                        "citations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "score": {"type": "number"}
                                }
                            }
                        },
                        "diff_summary": {"type": "string"},
                        "usage": {
                            "type": "object",
                            "properties": {
                                "tokens_in": {"type": "integer"},
                                "tokens_out": {"type": "integer"},
                                "credits": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request"},
        402: {"description": "Insufficient credits"},
        429: {"description": "Rate limit exceeded"}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def optimize_prompt(request):
    """RAG-powered prompt optimization endpoint"""
    start_time = time.time()
    
    try:
        # Parse request
        data = request.data
        session_id = data.get('session_id')
        original = data.get('original')
        mode = data.get('mode', 'fast')
        context = data.get('context', {})
        budget = data.get('budget', {})
        
        # Validation
        if not session_id or not original:
            return Response(
                {"error": "session_id and original are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(original) > 10000:
            return Response(
                {"error": "Prompt too long (max 10000 characters)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Apply budget defaults and limits
        budget_tokens_in = min(budget.get('tokens_in', 2000), 5000)
        budget_tokens_out = min(budget.get('tokens_out', 800), 2000)
        max_credits = min(budget.get('max_credits', 5), 10)
        
        # Determine credit cost based on mode
        credits_needed = 1 if mode == 'fast' else 3
        credits_needed = min(credits_needed, max_credits)
        
        # Check credits
        credit_check = CreditTracker.check_user_credits(request.user, credits_needed)
        if not credit_check["has_credits"]:
            return Response({
                "error": "Insufficient credits",
                "available": credit_check["available"],
                "required": credits_needed,
                "subscription_active": credit_check["subscription_active"]
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check for idempotent request
        idempotency_key = generate_idempotency_key(session_id, original)
        cache_key = f"rag_agent:{request.user.id}:{idempotency_key}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for {idempotency_key}")
            return Response(cached_result)
        
        # Rate limiting
        rate_key = f"rag_rate:{request.user.id}"
        rate_count = cache.get(rate_key, 0)
        if rate_count >= 20:  # 20 requests per hour
            return Response(
                {"error": "Rate limit exceeded"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Create optimization request
        opt_request = OptimizationRequest(
            session_id=session_id,
            original=original,
            mode=mode,
            context=context,
            budget={
                "tokens_in": budget_tokens_in,
                "tokens_out": budget_tokens_out,
                "max_credits": max_credits
            }
        )
        
        # Get RAG agent and optimize
        rag_agent = get_rag_agent()
        
        try:
            result = await rag_agent.optimize_prompt(opt_request)
        except Exception as e:
            logger.error(f"RAG optimization failed: {e}")
            return Response(
                {"error": "Optimization service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Consume credits
        success = CreditTracker.consume_credits(
            request.user,
            credits_needed,
            result.usage["tokens_in"],
            result.usage["tokens_out"]
        )
        
        if not success:
            logger.error("Failed to consume credits after optimization")
        
        # Prepare response
        response_data = {
            "optimized": result.optimized,
            "citations": [
                {
                    "id": c.id,
                    "title": c.title,
                    "source": c.source,
                    "score": c.score
                }
                for c in result.citations
            ],
            "diff_summary": result.diff_summary,
            "usage": result.usage,
            "run_id": result.run_id,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
        # Cache result for idempotency
        cache.set(cache_key, response_data, timeout=3600)  # 1 hour
        
        # Update rate limiting
        cache.set(rate_key, rate_count + 1, timeout=3600)
        
        logger.info(f"RAG optimization completed in {response_data['processing_time_ms']}ms")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"RAG optimization error: {e}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get RAG agent statistics",
    description="Get usage statistics and performance metrics for the RAG agent",
    responses={
        200: {
            "description": "Statistics retrieved",
            "content": {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "index_status": {"type": "object"},
                        "user_usage": {"type": "object"},
                        "system_metrics": {"type": "object"}
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_stats(request):
    """Get RAG agent statistics"""
    try:
        # Check if user has access to stats
        if not request.user.is_staff:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get index status
        from apps.ai_services.rag_service import get_document_indexer
        from pathlib import Path
        import json
        
        indexer = get_document_indexer()
        metadata_file = indexer.index_path / "metadata.json"
        
        index_status = {"available": False}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    index_status = json.load(f)
                index_status["available"] = True
            except Exception:
                pass
        
        # Get user usage stats
        today = timezone.now().date()
        user_quota = UsageQuota.objects.filter(
            user=request.user,
            quota_date=today
        ).first()
        
        user_usage = {
            "api_calls_today": user_quota.api_calls_made if user_quota else 0,
            "api_limit": user_quota.api_call_limit if user_quota else 0,
            "subscription_active": hasattr(request.user, 'subscription') and request.user.subscription.is_active
        }
        
        # System metrics
        total_optimizations = PromptOptimization.objects.filter(
            created_at__date=today
        ).count()
        
        system_metrics = {
            "optimizations_today": total_optimizations,
            "avg_processing_time": 250,  # Placeholder
            "success_rate": 0.95  # Placeholder
        }
        
        return Response({
            "index_status": index_status,
            "user_usage": user_usage,
            "system_metrics": system_metrics
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return Response(
            {"error": "Failed to retrieve stats"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Async wrapper for Django views
import asyncio
from functools import wraps

def async_api_view(func):
    """Decorator to run async functions in Django views"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

# Apply async wrapper to the optimize function
optimize_prompt = async_api_view(optimize_prompt)


@extend_schema(
    summary="Retrieve documents for a query",
    description="Return top-k retrieved documents from the RAG index",
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_retrieve(request):
    try:
        query = request.data.get('query')
        top_k = int(request.data.get('top_k', 5))
        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.ai_services.rag_service import get_document_indexer
        indexer = get_document_indexer()
        retriever = indexer
        # Use RAGRetriever via get_rag_agent for consistent interface
        from apps.ai_services.rag_service import RAGRetriever
        retr = RAGRetriever()
        docs = retr.retrieve_documents(query, top_k=top_k)

        results = [
            {
                'id': d.metadata.get('doc_id'),
                'title': d.metadata.get('title'),
                'source': d.metadata.get('source'),
                'snippet': (d.page_content[:400] + '...') if len(d.page_content) > 400 else d.page_content,
                'metadata': d.metadata
            }
            for d in docs
        ]

        return Response({'query': query, 'results': results, 'count': len(results)})
    except Exception as e:
        logger.error(f"rag_retrieve error: {e}")
        return Response({'error': 'internal_error', 'details': str(e)}, status=500)


@extend_schema(
    summary="RAG answer endpoint",
    description="Run retrieval and generate an answer (non-streaming).",
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_answer(request):
    try:
        query = request.data.get('query')
        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        # use get_rag_agent to perform retrieval + optimization/answer
        rag_agent = get_rag_agent()
        opt_request = OptimizationRequest(session_id=str(uuid.uuid4()), original=query, mode='fast')

        # Run optimization / answer
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(rag_agent.optimize_prompt(opt_request))
        finally:
            loop.close()

        response_data = {
            'optimized': result.optimized,
            'citations': [
                {
                    'id': c.id,
                    'title': c.title,
                    'source': c.source,
                    'score': c.score,
                    'snippet': c.snippet
                } for c in result.citations
            ],
            'diff_summary': result.diff_summary,
            'usage': result.usage,
            'run_id': result.run_id
        }

        return Response(response_data)
    except Exception as e:
        logger.error(f"rag_answer error: {e}")
        return Response({'error': 'internal_error', 'details': str(e)}, status=500)