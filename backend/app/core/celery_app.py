# app/core/celery_app.py
from celery import Celery
from app.core.config import settings
import os

# Set default Django settings module for Celery
os.environ.setdefault('FACTORTRACE_SETTINGS', 'production')

# Create Celery app
celery_app = Celery(
    "factortrace",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0"
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Task routing
    task_routes={
        'app.tasks.send_email_task': {'queue': 'email'},
        'app.tasks.generate_emissions_report': {'queue': 'reports'},
        'app.tasks.cleanup_expired_vouchers': {'queue': 'maintenance'},
        'app.tasks.send_compliance_reminders': {'queue': 'email'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-expired-vouchers': {
            'task': 'app.tasks.cleanup_expired_vouchers',
            'schedule': 60.0 * 60 * 24,  # Daily at midnight
        },
        'send-compliance-reminders': {
            'task': 'app.tasks.send_compliance_reminders',
            'schedule': 60.0 * 60 * 24,  # Daily at midnight
        },
        'health-check-dependencies': {
            'task': 'app.tasks.check_external_services',
            'schedule': 60.0 * 5,  # Every 5 minutes
        },
    },
    
    # Error handling
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

# Health check task
@celery_app.task(bind=True)
def health_check(self):
    """Simple task to verify Celery is working"""
    return {
        'status': 'healthy',
        'worker': self.request.hostname,
        'task_id': self.request.id
    }

# Debug task for testing
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task that prints request info"""
    print(f'Request: {self.request!r}')