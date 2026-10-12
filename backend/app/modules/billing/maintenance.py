"""Daily billing housekeeping: remind clinics before a plan ends, and close abandoned orders."""

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import FALLBACK_PLAN
from app.modules.billing.orders import OrderService
from app.shared.models import BillingOrder, Tenant

logger = structlog.get_logger()

REMINDER_DAYS = {1: 7, 2: 1}  # stage -> send when this many days (or fewer) are left
PENDING_ORDER_TTL = timedelta(hours=24)


def reminder_stage_due(tenant: Tenant, now: datetime) -> int:
    """The reminder stage to send now (0 = none). Later stages win; a stage is sent once."""
    if tenant.plan == FALLBACK_PLAN or tenant.plan_expires_at is None or tenant.plan_expires_at <= now:
        return 0
    left = tenant.plan_expires_at - now
    for stage in (2, 1):
        if left <= timedelta(days=REMINDER_DAYS[stage]) and tenant.plan_reminder_stage < stage:
            return stage
    return 0


def _reminder_email(tenant: Tenant, days: int) -> tuple[str, str, str]:
    ends = tenant.plan_expires_at.strftime("%d %B %Y")
    plan = tenant.plan.capitalize()
    subject = f"Your AltCare {plan} plan ends on {ends}"
    url = f"{settings.FRONTEND_URL}/billing"
    text = (
        f"Your AltCare {plan} plan ends on {ends} ({days} day{'s' if days != 1 else ''} left).\n"
        "After that your clinic moves to the Free plan's limits. Nothing is deleted.\n"
        f"Renew here: {url}\n"
    )
    html = (
        f"<p>Your AltCare <b>{plan}</b> plan ends on <b>{ends}</b> ({days} day{'s' if days != 1 else ''} left).</p>"
        "<p>After that your clinic moves to the Free plan's limits. Nothing is deleted.</p>"
        f'<p><a href="{url}">Renew your plan</a></p>'
    )
    return subject, text, html


async def send_expiry_reminders(db: AsyncSession, send) -> int:
    """Send due reminders. `send(recipient, subject, body_text, body_html)` is injected so tests
    don't need a broker; the Celery task passes the real system-email sender."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=REMINDER_DAYS[1])
    tenants = (
        await db.execute(
            select(Tenant).where(
                Tenant.is_active.is_(True),
                Tenant.plan != FALLBACK_PLAN,
                Tenant.plan_expires_at.is_not(None),
                Tenant.plan_expires_at > now,
                Tenant.plan_expires_at <= horizon,
            )
        )
    ).scalars().all()
    sent = 0
    for tenant in tenants:
        stage = reminder_stage_due(tenant, now)
        if not stage:
            continue
        recipient = tenant.clinic_email or tenant.email
        days = max(1, (tenant.plan_expires_at - now).days)
        if recipient:
            subject, text, html = _reminder_email(tenant, days)
            send(recipient, subject, text, html)
            sent += 1
        tenant.plan_reminder_stage = stage  # also when there is no address, so we don't retry daily
    await db.commit()
    return sent


async def expire_stale_orders(db: AsyncSession) -> int:
    """Close pending orders older than a day. A last gateway check first, in case a payment landed."""
    cutoff = datetime.now(timezone.utc) - PENDING_ORDER_TTL
    stale = (
        await db.execute(
            select(BillingOrder).where(BillingOrder.status == "pending", BillingOrder.created_at < cutoff)
        )
    ).scalars().all()
    service = OrderService(db)
    closed = 0
    for order in stale:
        order = await service.refresh(order)
        if order.status == "pending":
            order.status = "expired"
            closed += 1
    await db.commit()
    return closed
