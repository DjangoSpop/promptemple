"""
Server-Sent Events (SSE) streaming for research agent.
Provides real-time updates during research processing.
"""
import json
import logging
import asyncio
from typing import Generator, Dict, Any, Optional
from django.http import StreamingHttpResponse
from django.utils.timezone import now
from django.core.cache import cache

from .contracts import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


class ResearchStreamer:
    """Manages SSE streaming for research jobs."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.cache_key = f"research_stream_{job_id}"
        
    def push_event(self, event_type: StreamEventType, data: Dict[str, Any]) -> None:
        """
        Push an event to the stream cache for pickup by SSE endpoint.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            event = StreamEvent(event=event_type, data=data)
            
            # Get existing events from cache
            events = cache.get(self.cache_key, [])
            events.append(event.dict())
            
            # Keep only last 50 events to prevent memory issues
            if len(events) > 50:
                events = events[-50:]
            
            # Store back in cache with 1 hour expiry
            cache.set(self.cache_key, events, 3600)
            
            logger.debug(f"Pushed {event_type.value} event for job {self.job_id}")
            
        except Exception as e:
            logger.error(f"Failed to push event: {e}")
    
    def get_events(self, since_index: int = 0) -> list:
        """
        Get events since the specified index.
        
        Args:
            since_index: Index to start from
            
        Returns:
            List of events since the index
        """
        try:
            events = cache.get(self.cache_key, [])
            return events[since_index:] if since_index < len(events) else []
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    def clear_events(self) -> None:
        """Clear all cached events for this job."""
        try:
            cache.delete(self.cache_key)
        except Exception as e:
            logger.error(f"Failed to clear events: {e}")


def create_sse_response(event_generator) -> StreamingHttpResponse:
    """
    Create an SSE streaming response.
    
    Args:
        event_generator: Generator function that yields SSE events
        
    Returns:
        StreamingHttpResponse configured for SSE
    """
    response = StreamingHttpResponse(
        event_generator,
        content_type='text/event-stream'
    )
    
    # Set SSE headers
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable Nginx buffering
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    
    return response


def stream_research_progress(job_id: str) -> Generator[str, None, None]:
    """
    Generator for streaming research job progress via SSE.
    
    Args:
        job_id: Research job ID
        
    Yields:
        SSE formatted event strings
    """
    from .models import ResearchJob
    
    streamer = ResearchStreamer(job_id)
    last_event_index = 0
    
    # Send initial event
    yield format_sse_event("stream_start", {"job_id": job_id, "timestamp": now().isoformat()})
    
    # Poll for updates for up to 10 minutes
    for iteration in range(600):  # 600 iterations * 1 second = 10 minutes
        try:
            # Check if job exists
            try:
                job = ResearchJob.objects.get(pk=job_id)
            except ResearchJob.DoesNotExist:
                yield format_sse_event("error", {"message": "Job not found"})
                break
            
            # Get new events from cache
            events = streamer.get_events(since_index=last_event_index)
            
            for event_data in events:
                event_type = event_data.get('event', 'update')
                data = event_data.get('data', {})
                yield format_sse_event(event_type, data)
            
            last_event_index += len(events)
            
            # Check job status
            if job.status == "error":
                yield format_sse_event("error", {
                    "message": job.error or "Job failed",
                    "job_id": job_id
                })
                break
            elif job.status == "done":
                # Send final answer if available
                if hasattr(job, 'answer'):
                    from .serializers import ResearchAnswerSerializer
                    answer_data = ResearchAnswerSerializer(job.answer).data
                    yield format_sse_event("answer", answer_data)
                
                yield format_sse_event("complete", {"job_id": job_id})
                break
            
            # Send periodic heartbeat
            if iteration % 30 == 0:  # Every 30 seconds
                yield format_sse_event("heartbeat", {
                    "timestamp": now().isoformat(),
                    "status": job.status
                })
            
            # Wait before next poll
            asyncio.sleep(1.0) if asyncio.iscoroutinefunction(asyncio.sleep) else None
            
        except Exception as e:
            logger.error(f"Stream error for job {job_id}: {e}")
            yield format_sse_event("error", {"message": str(e)})
            break
    
    else:
        # Timeout reached
        yield format_sse_event("timeout", {"message": "Stream timeout reached"})
    
    # Final event
    yield "data: [DONE]\n\n"


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Format data as Server-Sent Event string.
    
    Args:
        event_type: Event type name
        data: Event data dictionary
        
    Returns:
        SSE formatted string
    """
    try:
        json_data = json.dumps(data, default=str, ensure_ascii=False)
        return f"event: {event_type}\ndata: {json_data}\n\n"
    except Exception as e:
        logger.error(f"Failed to format SSE event: {e}")
        return f"event: error\ndata: {{\"message\": \"Event formatting failed\"}}\n\n"


def stream_card_events(job_id: str, cards: list) -> None:
    """
    Stream individual card events as they are generated.
    
    Args:
        job_id: Research job ID
        cards: List of InsightCard objects
    """
    streamer = ResearchStreamer(job_id)
    
    for card in cards:
        try:
            card_data = {
                "id": card.id,
                "title": card.title,
                "content": card.content,
                "citations": [
                    {
                        "n": cite.n,
                        "url": cite.url,
                        "title": cite.title,
                        "score": cite.score
                    } for cite in card.citations
                ],
                "confidence": card.confidence,
                "authority": card.authority,
                "domain_cluster": card.domain_cluster,
                "tags": card.tags
            }
            
            streamer.push_event(StreamEventType.CARD, card_data)
            
        except Exception as e:
            logger.error(f"Failed to stream card event: {e}")


def push_update_event(job_id: str, stage: str, message: str, progress: Optional[Dict] = None) -> None:
    """
    Push an update event for job progress.
    
    Args:
        job_id: Research job ID
        stage: Current processing stage
        message: Status message
        progress: Optional progress data
    """
    streamer = ResearchStreamer(job_id)
    
    data = {
        "stage": stage,
        "message": message,
        "timestamp": now().isoformat()
    }
    
    if progress:
        data.update(progress)
    
    streamer.push_event(StreamEventType.UPDATE, data)


# Stage-specific helper functions
def push_planning_event(job_id: str, query: str, search_terms: list = None):
    """Push planning stage event."""
    data = {
        "query": query,
        "search_terms": search_terms or [],
        "stage": "planning"
    }
    ResearchStreamer(job_id).push_event(StreamEventType.PLANNING, data)


def push_searching_event(job_id: str, search_count: int, found_urls: int):
    """Push searching stage event."""
    data = {
        "searches_completed": search_count,
        "urls_found": found_urls,
        "stage": "searching"
    }
    ResearchStreamer(job_id).push_event(StreamEventType.SEARCHING, data)


def push_clustering_event(job_id: str, clusters_created: int, domains: list):
    """Push clustering stage event."""
    data = {
        "clusters_created": clusters_created,
        "domains": domains,
        "stage": "clustering"
    }
    ResearchStreamer(job_id).push_event(StreamEventType.CLUSTERING, data)


def push_fetching_event(job_id: str, urls_processed: int, total_urls: int):
    """Push content fetching event."""
    data = {
        "urls_processed": urls_processed,
        "total_urls": total_urls,
        "progress_percent": int((urls_processed / total_urls * 100)) if total_urls > 0 else 0,
        "stage": "fetching"
    }
    ResearchStreamer(job_id).push_event(StreamEventType.FETCHING, data)


def push_synthesis_event(job_id: str, cards_generated: int, cards_rejected: int):
    """Push synthesis stage event."""
    data = {
        "cards_generated": cards_generated,
        "cards_rejected": cards_rejected,
        "stage": "synthesis"
    }
    ResearchStreamer(job_id).push_event(StreamEventType.SYNTHESIS, data)


def push_end_event(job_id: str, total_cards: int, processing_time_ms: int):
    """Push completion event."""
    data = {
        "total_cards": total_cards,
        "processing_time_ms": processing_time_ms,
        "completed_at": now().isoformat()
    }
    ResearchStreamer(job_id).push_event(StreamEventType.END, data)


def push_error_event(job_id: str, error_message: str, stage: str = "unknown"):
    """Push error event."""
    data = {
        "error": error_message,
        "stage": stage,
        "timestamp": now().isoformat()
    }
    ResearchStreamer(job_id).push_event(StreamEventType.ERROR, data)