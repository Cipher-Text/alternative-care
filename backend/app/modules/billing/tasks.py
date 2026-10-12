"""Celery task for daily billing housekeeping (scheduled by beat; see app/core/celery.py)."""

import asyncio

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.core.system_email import send_system_email_task
from app.modules.billing.maintenance import expire_stale_orders, send_expiry_reminders


def _send(recipient: str, subject: str, body_text: str, body_html: str) -> None:
    send_system_email_task.delay(
        recipient=recipient, subject=subject, body_text=body_text, body_html=body_html
    )


@celery_app.task
def billing_daily_maintenance() -> dict:
    async def _run():
        async with AsyncSessionLocal() as db:
            reminders = await send_expiry_reminders(db, _send)
            expired = await expire_stale_orders(db)
            return {"reminders": reminders, "orders_expired": expired}

    return asyncio.get_event_loop().run_until_complete(_run())
