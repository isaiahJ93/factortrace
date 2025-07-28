"""
Celery tasks for GHG Protocol Scope 3 Calculator
"""

from app.tasks.celery_app import celery_app
from app.tasks.calculation_tasks import calculate_emissions_task, batch_calculate_task
from app.tasks.report_tasks import generate_report_task
from app.tasks.import_tasks import bulk_import_task

__all__ = [
    'celery_app',
    'calculate_emissions_task',
    'batch_calculate_task',
    'generate_report_task',
    'bulk_import_task',
]
