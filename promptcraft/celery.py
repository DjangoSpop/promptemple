"""
Celery configuration for PromptCraft project.

This module configures Celery for background task processing in production.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.production')

app = Celery('promptcraft')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration for production
app.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_routes={
        'apps.ai_services.tasks.*': {'queue': 'ai_processing'},
        'apps.analytics.tasks.*': {'queue': 'analytics'},
        'apps.templates.tasks.*': {'queue': 'templates'},
    },
    task_default_queue='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')