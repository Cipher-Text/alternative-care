"""Demo platform-admin work for local development (called from seed.py, development only).

Gives the platform admin dashboard something to show: a clinic waiting for approval, a clinic that listed itself in
the directory but is not verified, new contact messages, a plan about to end, and some billing activity. Fixed
ids and emails make running the seed again change nothing.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.shared.models import BillingOrder, ContactMessage, PractitionerListing, Tenant, User


def _id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "altcare-demo-platform:" + ":".join(parts)))


async def seed_demo_platform(session: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    created = 0

    async def tenant(key: str, name: str, doctor: str, **fields) -> Tenant:
        nonlocal created
        row = await session.get(Tenant, _id("tenant", key))
        if row is None:
            row = Tenant(
                id=_id("tenant", key), name=doctor, email=f"{key}@demo-clinic.example", clinic_name=name,
                specializations=["homeopathy"], is_active=True, **{"is_approved": True, "is_verified": True, **fields},
            )
            session.add(row)
            await session.flush()
            session.add(
                User(
                    id=_id("user", key), tenant_id=row.id, email=f"dr.{key}@demo-clinic.example", full_name=doctor, role="doctor",
                    password_hash=get_password_hash("Test@1234"), is_active=True, is_email_verified=True,
                )
            )
            created += 1
        return row

    pending = await tenant("pending", "Mirpur Healing Clinic", "Dr. Nusrat Jahan", is_approved=False, is_verified=False, plan="free")
    pending.created_at = now - timedelta(days=3)
    listed = await tenant("listed", "Sylhet Herbal Care", "Dr. Abul Kalam", is_verified=False, plan="plus", plan_expires_at=now + timedelta(days=90))
    renewal = await tenant("renewal", "Rajshahi Unani Centre", "Hakim Sirajul Islam", plan="pro", plan_expires_at=now + timedelta(days=6, hours=1))
    await session.flush()

    if (await session.execute(select(PractitionerListing.id).where(PractitionerListing.tenant_id == listed.id))).first() is None:
        session.add(
            PractitionerListing(
                id=_id("listing", "listed"), tenant_id=listed.id, user_id=_id("user", "listed"), slug="dr-abul-kalam-demo",
                is_listed=True, listed_at=now - timedelta(days=2),
            )
        )

    for key, topic, name, message in (
        ("enterprise", "enterprise", "Dr. Rezaul Karim", "We run 4 branches and want one account for all of them. Please call me."),
        ("billing", "billing", "Shirin Sultana", "I paid for the Pro plan by bKash two days ago but it still shows Plus."),
    ):
        if await session.get(ContactMessage, _id("contact", key)) is None:
            session.add(
                ContactMessage(
                    id=_id("contact", key), topic=topic, name=name, email=f"{key}@demo-contact.example", message=message,
                    created_at=now - timedelta(hours=5 if key == "enterprise" else 30),
                )
            )

    for key, status, amount, extra in (
        ("paid1", "paid", 3000, dict(paid_at=now - timedelta(days=2), fulfilled_at=now - timedelta(days=2))),
        ("failed1", "failed", 3000, dict(created_at=now - timedelta(days=1), gateway="sslcommerz")),
        ("stale1", "pending", 1000, dict(created_at=now - timedelta(hours=8), gateway="sslcommerz")),
    ):
        if await session.get(BillingOrder, _id("order", key)) is not None:
            continue
        session.add(
            BillingOrder(
                id=_id("order", key), receipt_no=f"AC-DEMO-{key.upper()}", tenant_id=renewal.id, payer_user_id=_id("user", "renewal"),
                payer_name="Demo payer", kind="subscription", plan_key="pro", period="monthly", description="Pro plan, 1 month",
                amount=Decimal(amount), status=status, **{"gateway": "manual", **extra},
            )
        )
    await session.flush()
    return created
