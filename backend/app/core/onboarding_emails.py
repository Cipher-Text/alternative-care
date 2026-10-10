"""Onboarding lifecycle emails: signup received, account approved, admin heads-up.

Sent through the platform's system-email task (`app/core/system_email.py`). Delivery is
best-effort: a failure to queue an email is logged and never breaks signup or approval,
since the account state change is what matters and an admin can still act on it.
"""

from html import escape

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.system_email import send_system_email_task
from app.shared.models import Tenant, User

logger = structlog.get_logger(__name__)


def _queue(recipient: str, subject: str, text: str, html_paragraphs: list[str]) -> None:
    try:
        send_system_email_task.delay(
            recipient=recipient,
            subject=subject,
            body_html="".join(f"<p>{p}</p>" for p in html_paragraphs),
            body_text=text,
        )
    except Exception:  # noqa: BLE001 - never let email trouble block an account change
        logger.warning("onboarding_email_queue_failed", recipient=recipient, subject=subject)


def send_signup_received_email(user: User) -> None:
    """Tell a new doctor their signup arrived and what happens next."""
    name = user.full_name
    login_url = f"{settings.FRONTEND_URL}/login"
    if user.language == "bn":
        subject = "আপনার AltCare নিবন্ধন পেয়েছি"
        lines = [
            f"প্রিয় {name},",
            "AltCare-এ নিবন্ধনের জন্য ধন্যবাদ। আমরা আপনার আবেদন পেয়েছি এবং এটি পর্যালোচনা করছি।",
            "সাধারণত অল্প সময়ের মধ্যে আপনার অ্যাকাউন্ট অনুমোদিত হয়। অনুমোদিত হলেই আমরা আপনাকে ইমেইল করব।",
            "অনুগ্রহ করে আলাদা ইমেইলে পাঠানো লিংকে আপনার ইমেইল ঠিকানা যাচাই করুন।",
        ]
    else:
        subject = "We received your AltCare registration"
        lines = [
            f"Hi {name},",
            "Thanks for signing up for AltCare. We have received your registration and "
            "are reviewing it.",
            "We will email you as soon as your account is approved. In the meantime, please "
            "verify your email address using the separate verification email we sent.",
        ]
    lines.append(login_url)
    _queue(user.email, subject, "\n\n".join(lines), [escape(x) for x in lines[:-1]]
           + [f'<a href="{escape(login_url)}">{escape(login_url)}</a>'])


def send_tenant_approved_email(user: User) -> None:
    """Tell a doctor their account is approved and they can log in."""
    name = user.full_name
    login_url = f"{settings.FRONTEND_URL}/login"
    if user.language == "bn":
        subject = "আপনার AltCare অ্যাকাউন্ট অনুমোদিত হয়েছে"
        lines = [
            f"প্রিয় {name},",
            "সুসংবাদ: আপনার AltCare অ্যাকাউন্ট অনুমোদিত হয়েছে। এখন লগইন করে শুরু করতে পারেন।",
        ]
    else:
        subject = "Your AltCare account is approved"
        lines = [
            f"Hi {name},",
            "Good news: your AltCare account has been approved. You can log in now and "
            "get started.",
        ]
    lines.append(login_url)
    _queue(user.email, subject, "\n\n".join(lines), [escape(x) for x in lines[:-1]]
           + [f'<a href="{escape(login_url)}">{escape(login_url)}</a>'])


async def notify_admins_new_signup(
    db: AsyncSession, tenant: Tenant, user: User, requested_plan: str | None = None
) -> None:
    """Email active platform admins that a tenant is waiting for approval."""
    try:
        result = await db.execute(
            select(User.email).where(User.role == "admin", User.is_active.is_(True))
        )
        admin_emails = [row[0] for row in result.all()]
    except Exception:  # noqa: BLE001
        logger.warning("admin_signup_notification_lookup_failed", tenant_id=tenant.id)
        return

    review_url = f"{settings.FRONTEND_URL}/admin/clients"
    facts = [
        f"Name: {user.full_name}",
        f"Email: {user.email}",
        f"Clinic: {tenant.clinic_name or '-'}",
        f"Specializations: {', '.join(tenant.specializations or []) or '-'}",
        f"License: {tenant.license_number or '-'}",
    ]
    if requested_plan:
        facts.append(f"Interested in plan: {requested_plan}")
    text = "A new tenant is waiting for approval.\n\n" + "\n".join(facts) + f"\n\n{review_url}"
    html = ["A new tenant is waiting for approval."] + [escape(f) for f in facts] + [
        f'<a href="{escape(review_url)}">{escape(review_url)}</a>'
    ]
    for email in admin_emails:
        _queue(email, f"New AltCare signup awaiting approval: {user.full_name}", text, html)
