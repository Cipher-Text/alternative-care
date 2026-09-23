"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "altcare",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task result settings
    result_expires=3600,  # 1 hour
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Rate limiting
    task_default_rate_limit="100/m",
    # Autodiscover tasks
    imports=[
        "app.modules.integration.tasks",
        "app.core.system_email",
    ],
)

# Task routes (optional - for prioritization)
celery_app.conf.task_routes = {
    "app.modules.integration.tasks.send_sms_task": {"queue": "sms"},
    "app.modules.integration.tasks.send_email_task": {"queue": "email"},
    "app.core.system_email.send_system_email_task": {"queue": "email"},
}
