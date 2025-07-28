"""
Celery configuration for GHG Protocol Scope 3 Calculator
"""

from celery import Celery

# Create Celery app
celery_app = Celery(
    'ghg_calculator',
    broker='redis://localhost:6379',
    backend='redis://localhost:6379'
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'app.tasks.calculation_tasks.*': {'queue': 'calculations'},
        'app.tasks.report_tasks.*': {'queue': 'reports'},
        'app.tasks.import_tasks.*': {'queue': 'imports'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-calculations': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_calculations',
            'schedule': 86400.0,  # Daily
        },
    }
)
