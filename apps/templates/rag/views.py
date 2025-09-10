"""
RAG API views for template optimization
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from apps.templates.rag.services import get_langchain_service, langchain_status
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_optimize(request):
    """
    Optimize a prompt using RAG
    Requires authentication and uses the RAG service if available
    """
    svc = get_langchain_service()
    if not svc:
        return Response({
            "detail": "RAG service temporarily unavailable",
            "reason": "Service disabled or failed to initialize"
        }, status=503)
    
    # Get prompt from request
    prompt = request.data.get('prompt', '')
    if not prompt:
        return Response({
            "detail": "Missing 'prompt' field in request"
        }, status=400)
    
    try:
        # For now, return a simple response
        # TODO: Implement actual RAG optimization logic
        return Response({
            "original": prompt,
            "optimized": f"Optimized: {prompt}",
            "improvements": ["Added clarity", "Improved structure"],
            "service_info": {
                "strategy": svc.get("strategy", "unknown"),
                "available_factories": list(svc.keys())
            }
        })
    except Exception as e:
        logger.error(f"RAG optimization failed: {e}")
        return Response({
            "detail": "RAG optimization failed",
            "error": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def rag_status_view(request):
    """
    Get RAG service status - public endpoint
    """
    return Response(langchain_status())