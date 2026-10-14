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
        "app.modules.messaging.tasks",
        "app.core.system_email",
        "app.modules.billing.tasks",
    ],
    # Run with `celery -A app.core.celery:celery_app beat` (a separate process in deployment)
    beat_schedule={
        "billing-daily-maintenance": {
            "task": "app.modules.billing.tasks.billing_daily_maintenance",
            "schedule": 24 * 60 * 60,
        },
    },
)

# Task routes (optional - for prioritization)
celery_app.conf.task_routes = {
    "app.modules.messaging.tasks.send_platform_sms_task": {"queue": "sms"},
    "app.modules.messaging.tasks.send_platform_email_task": {"queue": "email"},
    "app.core.system_email.send_system_email_task": {"queue": "email"},
}
