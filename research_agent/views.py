"""
API views and SSE streaming endpoints for research agent.
"""
import uuid
import json
import time
import logging
from typing import Generator, Optional, Dict, Any

from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes, action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.pagination import PageNumberPagination

from .models import ResearchJob, SourceDoc, Chunk, ResearchAnswer
from .serializers import (
    CreateJobSerializer, ResearchJobSerializer, JobWithAnswerSerializer,
    SourceDocSerializer, ChunkSerializer, ResearchAnswerSerializer,
    JobProgressSerializer, SystemStatsSerializer, HealthCheckSerializer,
    JobSummarySerializer
)
from .tasks import run_research_task
from .agent import ResearchJobStats

logger = logging.getLogger(__name__)


class ResearchThrottle(AnonRateThrottle):
    """Custom throttle for research endpoints."""
    scope = 'research'


class AuthenticatedResearchThrottle(UserRateThrottle):
    """Throttle for authenticated users."""
    scope = 'research_auth'


def sse_response(event_type: str, data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class ResearchJobPagination(PageNumberPagination):
    """Custom pagination for research jobs."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ResearchJobViewSet(viewsets.ModelViewSet):
    """ViewSet for research job management."""

    queryset = ResearchJob.objects.all()
    serializer_class = JobWithAnswerSerializer
    permission_classes = [permissions.AllowAny]  # Adjust as needed
    throttle_classes = [ResearchThrottle, AuthenticatedResearchThrottle]
    pagination_class = ResearchJobPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CreateJobSerializer
        elif self.action == 'list':
            return JobSummarySerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return JobWithAnswerSerializer
        return ResearchJobSerializer

    def get_queryset(self):
        """Filter queryset based on user and parameters."""
        queryset = ResearchJob.objects.all().order_by('-created_at')

        # Filter by status if specified
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new research job."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create job
        job_id = uuid.uuid4()
        job = ResearchJob.objects.create(
            id=job_id,
            query=serializer.validated_data['query'],
            top_k=serializer.validated_data.get('top_k', 6),
            created_by=request.user if request.user.is_authenticated else None
        )

        # Start background processing
        run_research_task.delay(str(job_id))

        # Return job details
        response_serializer = ResearchJobSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get detailed progress for a specific job."""
        try:
            progress_data = ResearchJobStats.get_job_progress(str(pk))
            serializer = JobProgressSerializer(data=progress_data)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(progress_data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """Get chunks associated with a job."""
        try:
            job = self.get_object()
            chunks = Chunk.objects.filter(doc__job=job)

            paginator = PageNumberPagination()
            paginator.page_size = 20
            paginated_chunks = paginator.paginate_queryset(chunks, request)

            serializer = ChunkSerializer(paginated_chunks, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def docs(self, request, pk=None):
        """Get source documents for a job."""
        try:
            job = self.get_object()
            docs = job.docs.all()
            serializer = SourceDocSerializer(docs, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@require_http_methods(["GET"])
@never_cache
def stream_job_progress(request, job_id):
    """
    Enhanced SSE streaming for research job progress with card events.
    
    This endpoint provides real-time updates including individual card synthesis.
    """
    from .sse import stream_research_progress, create_sse_response
    
    try:
        # Validate job exists
        job = ResearchJob.objects.get(pk=job_id)
    except ResearchJob.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)
    
    # Create SSE response with enhanced streaming
    return create_sse_response(stream_research_progress(job_id))


@require_http_methods(["GET"])
@never_cache  
def stream_cards(request, job_id):
    """
    Stream individual insight cards as they are generated.
    
    This endpoint specifically streams card events for real-time card display.
    """
    def card_event_generator():
        """Generate SSE events focused on cards."""
        from .sse import ResearchStreamer, format_sse_event
        
        yield format_sse_event("stream_start", {"job_id": job_id, "type": "cards"})
        
        streamer = ResearchStreamer(job_id)
        last_event_index = 0
        
        # Poll for card events
        for iteration in range(300):  # 5 minutes for card-specific streaming
            try:
                # Get new events, filter for card events
                events = streamer.get_events(since_index=last_event_index)
                
                for event_data in events:
                    event_type = event_data.get('event', '')
                    if event_type == 'card':
                        data = event_data.get('data', {})
                        yield format_sse_event('card', data)
                    elif event_type in ['synthesis', 'end', 'error']:
                        data = event_data.get('data', {})
                        yield format_sse_event(event_type, data)
                        
                        # End streaming on completion or error
                        if event_type in ['end', 'error']:
                            break
                
                last_event_index += len(events)
                
                # Check job status
                job = ResearchJob.objects.get(pk=job_id)
                if job.status in ["done", "error"]:
                    break
                    
                time.sleep(1.0)
                
            except ResearchJob.DoesNotExist:
                yield format_sse_event("error", {"message": "Job not found"})
                break
            except Exception as e:
                yield format_sse_event("error", {"message": str(e)})
                break
        
        yield "data: [DONE]\n\n"
    
    response = StreamingHttpResponse(
        card_event_generator(),
        content_type="text/event-stream"
    )
    
    # SSE headers
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    
    return response


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def system_health(request):
    """Get system health status."""
    try:
        from .tasks import health_check

        # Run health check
        health_data = health_check.apply().get()

        serializer = HealthCheckSerializer(data=health_data)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(health_data)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            {"error": str(e), "overall": False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def system_stats(request):
    """Get system statistics."""
    try:
        stats_data = ResearchJobStats.get_system_stats()
        serializer = SystemStatsSerializer(data=stats_data)

        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(stats_data)

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([ResearchThrottle])
def quick_research(request):
    """
    Quick research endpoint for simple queries.
    Returns job ID immediately and processes in background.
    """
    serializer = CreateJobSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create job
        job_id = uuid.uuid4()
        job = ResearchJob.objects.create(
            id=job_id,
            query=serializer.validated_data['query'],
            top_k=serializer.validated_data.get('top_k', 6),
            created_by=request.user if request.user.is_authenticated else None
        )

        # Start background processing
        run_research_task.delay(str(job_id))

        return Response({
            "job_id": str(job_id),
            "query": job.query,
            "status": job.status,
            "stream_url": f"/api/v2/research/jobs/{job_id}/stream/",
            "cards_stream_url": f"/api/v2/research/jobs/{job_id}/cards/stream/",
            "progress_url": f"/api/v2/research/jobs/{job_id}/progress/"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Quick research failed: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([ResearchThrottle])
def intent_fast(request):
    """
    Fast-path intent endpoint with optional warm card generation.
    
    This endpoint returns immediately with intent_id and optionally includes
    a warm card if quick synthesis is possible, then schedules full processing.
    """
    serializer = CreateJobSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create intent/job
        intent_id = uuid.uuid4()
        job = ResearchJob.objects.create(
            id=intent_id,
            query=serializer.validated_data['query'],
            top_k=serializer.validated_data.get('top_k', 6),
            created_by=request.user if request.user.is_authenticated else None
        )

        response_data = {
            "intent_id": str(intent_id),
            "query": job.query,
            "status": job.status,
            "stream_url": f"/api/v2/research/jobs/{intent_id}/stream/",
            "cards_stream_url": f"/api/v2/research/jobs/{intent_id}/cards/stream/"
        }

        # Try to generate a quick warm card (optional)
        warm_card = None
        try:
            warm_card = _generate_warm_card(job.query)
            if warm_card:
                response_data["warm_card"] = warm_card
        except Exception as e:
            logger.warning(f"Warm card generation failed: {e}")

        # Schedule background processing (high priority)
        run_research_task.apply_async(args=[str(intent_id)], priority=9)

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Fast intent processing failed: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _generate_warm_card(query: str) -> Optional[Dict[str, Any]]:
    """
    Generate a quick warm card for immediate response.
    
    Args:
        query: Research query
        
    Returns:
        Warm card data or None if generation fails
    """
    try:
        # Simple template-based warm card for immediate user feedback
        warm_card = {
            "id": f"warm_{uuid.uuid4()}",
            "title": f"Initial insights for: {query[:50]}...",
            "content": f"## Researching: {query}\n\nWe're currently gathering comprehensive information about your query from multiple authoritative sources. This will include:\n\n- Web search across relevant domains\n- Content analysis and synthesis\n- Evidence-based insights with citations\n\nPlease monitor the stream for real-time updates as we process your research request.",
            "type": "warm",
            "confidence": 1.0,
            "authority": 0.5,
            "citations": [],
            "generated_at": now().isoformat()
        }
        
        return warm_card
        
    except Exception as e:
        logger.error(f"Warm card generation error: {e}")
        return None


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def batch_research(request):
    """Create multiple research jobs in batch."""
    from .serializers import BatchJobSerializer

    serializer = BatchJobSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        queries = serializer.validated_data['queries']
        top_k = serializer.validated_data.get('top_k', 6)

        jobs = []
        for query in queries:
            job_id = uuid.uuid4()
            job = ResearchJob.objects.create(
                id=job_id,
                query=query,
                top_k=top_k,
                created_by=request.user if request.user.is_authenticated else None
            )

            # Start background processing
            run_research_task.delay(str(job_id))

            jobs.append({
                "job_id": str(job_id),
                "query": query,
                "status": job.status
            })

        return Response({
            "jobs": jobs,
            "total_created": len(jobs)
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Batch research failed: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Legacy endpoint compatibility
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([ResearchThrottle])
def start_job(request):
    """Legacy endpoint for starting research jobs."""
    return quick_research(request)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def job_status(request, job_id):
    """Legacy endpoint for job status."""
    try:
        job = ResearchJob.objects.get(pk=job_id)
        data = ResearchJobSerializer(job).data

        if hasattr(job, "answer") and job.answer:
            data["answer"] = ResearchAnswerSerializer(job.answer).data

        return Response(data)
    except ResearchJob.DoesNotExist:
        return Response(
            {"error": "Job not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@require_http_methods(["GET"])
@never_cache
def stream_answer(request, job_id):
    """Legacy SSE endpoint for streaming answers."""
    return stream_job_progress(request, job_id)


# Error handlers
def handle_404(request, exception=None):
    """Custom 404 handler for API endpoints."""
    return JsonResponse({
        "error": "Endpoint not found",
        "detail": "The requested research endpoint does not exist."
    }, status=404)


def handle_500(request):
    """Custom 500 handler for API endpoints."""
    return JsonResponse({
        "error": "Internal server error",
        "detail": "An unexpected error occurred while processing your research request."
    }, status=500)
