# celery_config.py
"""
Celery configuration for background task processing
"""
import os
from celery import Celery
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')

# Create Celery app
app = Celery('promptcraft')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Task configurations
app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker configuration for Windows compatibility
    worker_pool='threads',  # Use threads on Windows instead of prefork
    worker_concurrency=2,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'chat_template_service.process_chat_message_templates': {'queue': 'template_extraction'},
        'chat_template_service.publish_template_to_library': {'queue': 'template_publishing'},
        'chat_template_service.batch_process_chat_history': {'queue': 'batch_processing'},
        'monetization_tasks.*': {'queue': 'monetization'},
        'analytics_tasks.*': {'queue': 'analytics'},
    },
    
    # Task priorities
    task_default_priority=5,
    task_inherit_parent_priority=True,
    
    # Task retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Result backend
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks - temporarily disabled during setup
    beat_schedule={
        # Basic health check only during setup
        'health-check': {
            'task': 'celery_config.health_check',
            'schedule': 300.0,  # Every 5 minutes
        },
    },
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'


@app.task
def health_check():
    """Health check task for monitoring"""
    from django.db import connection
    from django.utils import timezone
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "healthy", "timestamp": timezone.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": timezone.now().isoformat()}


@app.task
def verify_system_setup():
    """Verify that the system is properly configured"""
    from django.conf import settings
    from django.db import connection
    
    checks = {
        "database": False,
        "deepseek_api": False,
        "celery": True,  # If this runs, Celery is working
        "models": False
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Check DeepSeek API configuration
    deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
    if deepseek_config.get('API_KEY') and deepseek_config.get('BASE_URL'):
        checks["deepseek_api"] = True
    
    # Check if models are migrated
    try:
        from apps.chat.models import ChatSession
        from monetization_models import SubscriptionPlan
        ChatSession.objects.exists()
        SubscriptionPlan.objects.exists()
        checks["models"] = True
    except Exception:
        pass
    
    return checks


if __name__ == '__main__':
    app.start()