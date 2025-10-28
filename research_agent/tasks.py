"""
Celery tasks for research agent background processing.
"""
import logging
from celery import shared_task
from .agent import run_research_job_sync

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def run_research_task(self, job_id: str):
    """
    Celery task to run a research job in the background.

    Args:
        job_id: UUID string of the research job

    Returns:
        Result dictionary from the research agent
    """
    try:
        logger.info(f"Starting Celery research task for job {job_id}")
        result = run_research_job_sync(job_id)
        logger.info(f"Celery research task completed for job {job_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Celery research task failed for job {job_id}: {e}")
        # Let Celery handle the retry logic
        raise


@shared_task
def cleanup_old_jobs(days_old: int = 30):
    """
    Cleanup old research jobs and their associated data.

    Args:
        days_old: Number of days after which jobs should be cleaned up

    Returns:
        Cleanup statistics
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .models import ResearchJob

        cutoff_date = timezone.now() - timedelta(days=days_old)

        # Find old jobs
        old_jobs = ResearchJob.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['done', 'error']  # Only cleanup completed jobs
        )

        job_count = old_jobs.count()

        if job_count == 0:
            logger.info("No old jobs to cleanup")
            return {"deleted_jobs": 0, "message": "No old jobs found"}

        # Delete old jobs (cascades to docs, chunks, answers)
        deleted_count, _ = old_jobs.delete()

        logger.info(f"Cleaned up {deleted_count} old research jobs")

        return {
            "deleted_jobs": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Successfully cleaned up {deleted_count} jobs older than {days_old} days"
        }

    except Exception as e:
        logger.error(f"Job cleanup task failed: {e}")
        return {"error": str(e)}


@shared_task
def rebuild_embeddings():
    """
    Rebuild embeddings for all chunks (useful after model updates).

    Returns:
        Rebuild statistics
    """
    try:
        from .models import Chunk
        from .embeddings import embed_texts
        from django.db import transaction

        chunks = list(Chunk.objects.all())
        if not chunks:
            return {"message": "No chunks to rebuild"}

        logger.info(f"Rebuilding embeddings for {len(chunks)} chunks")

        # Extract texts
        texts = [chunk.text for chunk in chunks]

        # Generate new embeddings
        new_embeddings = embed_texts(texts)

        # Update chunks with new embeddings
        updated_count = 0
        with transaction.atomic():
            for chunk, embedding in zip(chunks, new_embeddings):
                chunk.embedding = embedding
                chunk.save(update_fields=['embedding'])
                updated_count += 1

        logger.info(f"Successfully rebuilt embeddings for {updated_count} chunks")

        return {
            "updated_chunks": updated_count,
            "message": f"Successfully rebuilt embeddings for {updated_count} chunks"
        }

    except Exception as e:
        logger.error(f"Embedding rebuild task failed: {e}")
        return {"error": str(e)}


@shared_task
def health_check():
    """
    Health check task to verify research agent components.

    Returns:
        Health status
    """
    try:
        from django.utils import timezone

        health_status = {
            "timestamp": timezone.now().isoformat(),
            "database": False,
            "embeddings": False,
            "search": False,
            "synthesis": False,
            "overall": False
        }

        # Test database
        try:
            from .models import ResearchJob
            ResearchJob.objects.count()
            health_status["database"] = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Test embeddings
        try:
            from .embeddings import embed_texts
            test_embedding = embed_texts(["test"])
            health_status["embeddings"] = len(test_embedding) > 0
        except Exception as e:
            logger.error(f"Embeddings health check failed: {e}")

        # Test search
        try:
            from .search import web_search
            # Don't actually search, just check if the function is available
            health_status["search"] = callable(web_search)
        except Exception as e:
            logger.error(f"Search health check failed: {e}")

        # Test synthesis
        try:
            from .synthesis import synthesize_answer
            health_status["synthesis"] = callable(synthesize_answer)
        except Exception as e:
            logger.error(f"Synthesis health check failed: {e}")

        # Overall health
        health_status["overall"] = all([
            health_status["database"],
            health_status["embeddings"],
            health_status["search"],
            health_status["synthesis"]
        ])

        return health_status

    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        return {"error": str(e), "overall": False}


@shared_task
def generate_research_report():
    """
    Generate a report of recent research activity.

    Returns:
        Research activity report
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Avg
        from .models import ResearchJob, SourceDoc, Chunk

        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        report = {
            "generated_at": now.isoformat(),
            "period": {
                "last_week": last_week.isoformat(),
                "last_month": last_month.isoformat()
            }
        }

        # Job statistics
        report["jobs"] = {
            "total": ResearchJob.objects.count(),
            "last_week": ResearchJob.objects.filter(created_at__gte=last_week).count(),
            "last_month": ResearchJob.objects.filter(created_at__gte=last_month).count(),
            "completed": ResearchJob.objects.filter(status="done").count(),
            "failed": ResearchJob.objects.filter(status="error").count(),
            "in_progress": ResearchJob.objects.filter(status__in=["queued", "running"]).count()
        }

        # Content statistics
        report["content"] = {
            "total_documents": SourceDoc.objects.count(),
            "total_chunks": Chunk.objects.count(),
            "docs_last_week": SourceDoc.objects.filter(created_at__gte=last_week).count(),
            "chunks_last_week": Chunk.objects.filter(created_at__gte=last_week).count()
        }

        # Performance statistics
        completed_jobs = ResearchJob.objects.filter(
            status="done",
            finished_at__isnull=False,
            created_at__gte=last_month
        )

        if completed_jobs.exists():
            durations = []
            for job in completed_jobs:
                duration = (job.finished_at - job.created_at).total_seconds()
                durations.append(duration)

            if durations:
                report["performance"] = {
                    "avg_processing_time_seconds": sum(durations) / len(durations),
                    "min_processing_time_seconds": min(durations),
                    "max_processing_time_seconds": max(durations),
                    "jobs_analyzed": len(durations)
                }

        logger.info("Generated research activity report")
        return report

    except Exception as e:
        logger.error(f"Report generation task failed: {e}")
        return {"error": str(e)}


# Periodic task setup (if using django-celery-beat)
from celery.schedules import crontab
from django.conf import settings

# Define periodic tasks
RESEARCH_CELERY_BEAT_SCHEDULE = {
    'cleanup-old-research-jobs': {
        'task': 'research_agent.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (30,)  # Clean up jobs older than 30 days
    },
    'research-health-check': {
        'task': 'research_agent.tasks.health_check',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'generate-research-report': {
        'task': 'research_agent.tasks.generate_research_report',
        'schedule': crontab(hour=1, minute=0, day_of_week=1),  # Weekly on Monday at 1 AM
    }
}

# Add to Celery beat schedule if enabled
if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    settings.CELERY_BEAT_SCHEDULE.update(RESEARCH_CELERY_BEAT_SCHEDULE)