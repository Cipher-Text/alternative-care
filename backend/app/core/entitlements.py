"""Plan entitlements: what each subscription plan allows, and enforcement of it.

Two kinds of entitlement, both keyed by a string defined *in code* (only code can enforce a key):

- ``limit``   — a number a tenant may not exceed. ``None`` means unlimited. Either a running
                total (``period="total"``: patients, seats) or per calendar month
                (``period="monthly"``: SMS, AI queries).
- ``feature`` — an on/off capability (invoicing, AI assistant).

The *values* (and prices) are editable by platform admins and stored in the ``plans`` /
``plan_entitlements`` tables. A tenant-specific override (``tenant_entitlement_overrides``)
replaces a single entitlement for a single tenant. When a plan has no stored row for a key, the
defaults below apply, so the system behaves sensibly on a fresh database.

Defaults are deliberately permissive (no limits) except where the product already restricted
something (the AI assistant is Pro-only): nothing is capped until an admin sets a limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.usage_tracking import UsageService
from app.shared.models import (
    Patient,
    Plan,
    PlanEntitlement,
    Tenant,
    TenantEntitlementOverride,
    User,
)

Kind = Literal["limit", "feature"]
Period = Literal["total", "monthly"]


@dataclass(frozen=True)
class EntitlementDef:
    key: str
    kind: Kind
    label_en: str
    label_bn: str
    unit_en: str = ""
    unit_bn: str = ""
    period: Period | None = None


CATALOG: dict[str, EntitlementDef] = {
    d.key: d
    for d in (
        EntitlementDef("max_patients", "limit", "Patients", "রোগী", "patients", "রোগী", "total"),
        EntitlementDef(
            "max_seats", "limit", "Practitioner seats", "চিকিৎসক সংখ্যা", "doctors", "চিকিৎসক", "total"
        ),
        EntitlementDef(
            "monthly_sms", "limit", "SMS per month", "মাসিক এসএমএস", "SMS / month", "এসএমএস / মাস", "monthly"
        ),
        EntitlementDef(
            "monthly_ai_queries",
            "limit",
            "AI assistant queries per month",
            "মাসিক এআই প্রশ্ন",
            "queries / month",
            "প্রশ্ন / মাস",
            "monthly",
        ),
        EntitlementDef("feature_invoicing", "feature", "Payments & invoicing", "পেমেন্ট ও ইনভয়েস"),
        EntitlementDef("feature_ai_assistant", "feature", "AI assistant", "এআই সহকারী"),
    )
}


@dataclass(frozen=True)
class PlanDefaults:
    name_en: str
    name_bn: str
    description_en: str
    description_bn: str
    sort_order: int
    # key -> (enabled, limit)  (limit None = unlimited)
    entitlements: dict[str, tuple[bool, int | None]]


def _defaults(ai_enabled: bool, ai_quota: int) -> dict[str, tuple[bool, int | None]]:
    return {
        "max_patients": (True, None),
        "max_seats": (True, None),
        "monthly_sms": (True, None),
        "monthly_ai_queries": (True, ai_quota),
        "feature_invoicing": (True, None),
        "feature_ai_assistant": (ai_enabled, None),
    }


DEFAULT_PLANS: dict[str, PlanDefaults] = {
    "free": PlanDefaults(
        "Free", "ফ্রি",
        "For solo practitioners getting started", "শুরু করা একক চিকিৎসকদের জন্য",
        1, _defaults(False, 0),
    ),
    "plus": PlanDefaults(
        "Plus", "প্লাস",
        "For growing clinics", "বর্ধনশীল ক্লিনিকের জন্য",
        2, _defaults(False, 0),
    ),
    "pro": PlanDefaults(
        "Pro", "প্রো",
        "For established practices", "প্রতিষ্ঠিত প্র্যাকটিসের জন্য",
        3, _defaults(True, 200),
    ),
}
FALLBACK_PLAN = "free"


@dataclass(frozen=True)
class Effective:
    key: str
    kind: Kind
    enabled: bool
    limit: int | None  # None = unlimited (limit kinds)
    source: Literal["plan", "override"]


def plan_defaults(plan_key: str) -> PlanDefaults:
    return DEFAULT_PLANS.get(plan_key, DEFAULT_PLANS[FALLBACK_PLAN])


async def load_plan_values(
    db: AsyncSession, plan_key: str
) -> dict[str, tuple[bool, int | None]]:
    """Defaults merged with whatever the admin has stored for this plan."""
    values = dict(plan_defaults(plan_key).entitlements)
    rows = await db.execute(select(PlanEntitlement).where(PlanEntitlement.plan_key == plan_key))
    for row in rows.scalars().all():
        if row.entitlement_key in CATALOG:
            values[row.entitlement_key] = (row.enabled, row.limit_value)
    return values


def effective_plan_key(tenant: Tenant) -> tuple[str, bool]:
    """(plan key to apply, expired?). An expired plan falls back to the free plan's entitlements."""
    expires = tenant.plan_expires_at
    if expires is not None and expires < datetime.now(timezone.utc):
        return FALLBACK_PLAN, True
    return (tenant.plan or FALLBACK_PLAN), False


def _denied(detail: dict) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class EntitlementService:
    """Resolves a tenant's effective entitlements and enforces them."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _tenant(self, tenant_id: str) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise _denied({"code": "no_tenant", "message": "Tenant not found."})
        return tenant

    async def resolve(self, tenant_id: str) -> tuple[str, bool, dict[str, Effective]]:
        """Return (applied plan key, expired?, effective entitlements by key)."""
        tenant = await self._tenant(tenant_id)
        plan_key, expired = effective_plan_key(tenant)
        values = await load_plan_values(self.db, plan_key)

        effective = {
            key: Effective(key, CATALOG[key].kind, enabled, limit, "plan")
            for key, (enabled, limit) in values.items()
        }
        overrides = await self.db.execute(
            select(TenantEntitlementOverride).where(
                TenantEntitlementOverride.tenant_id == tenant_id
            )
        )
        for row in overrides.scalars().all():
            if row.entitlement_key in CATALOG:
                effective[row.entitlement_key] = Effective(
                    row.entitlement_key,
                    CATALOG[row.entitlement_key].kind,
                    row.enabled,
                    row.limit_value,
                    "override",
                )
        return plan_key, expired, effective

    async def used(self, tenant_id: str, key: str) -> int:
        """Current consumption for a limit entitlement."""
        if key == "max_patients":
            result = await self.db.execute(
                select(func.count())
                .select_from(Patient)
                .where(Patient.tenant_id == tenant_id, Patient.is_active.is_(True))
            )
            return int(result.scalar_one())
        if key == "max_seats":
            result = await self.db.execute(
                select(func.count())
                .select_from(User)
                .where(User.tenant_id == tenant_id, User.is_active.is_(True))
            )
            return int(result.scalar_one())
        if key in ("monthly_sms", "monthly_ai_queries"):
            month = await UsageService(self.db, tenant_id).get_month_to_date()
            return int(month["sms_sent" if key == "monthly_sms" else "ai_queries_made"])
        return 0

    async def check_feature(self, tenant_id: str, key: str) -> None:
        plan_key, expired, effective = await self.resolve(tenant_id)
        item = effective[key]
        if not item.enabled:
            label = CATALOG[key].label_en
            raise _denied(
                {
                    "code": "plan_expired" if expired else "feature_not_in_plan",
                    "message": (
                        "Your plan has expired."
                        if expired
                        else f"{label} is not included in your {plan_key.capitalize()} plan."
                    ),
                    "entitlement": key,
                    "plan": plan_key,
                }
            )

    async def check_limit(self, tenant_id: str, key: str, increment: int = 1) -> None:
        plan_key, expired, effective = await self.resolve(tenant_id)
        item = effective[key]
        label = CATALOG[key].label_en
        if not item.enabled:
            raise _denied(
                {
                    "code": "plan_expired" if expired else "feature_not_in_plan",
                    "message": f"{label} is not included in your {plan_key.capitalize()} plan.",
                    "entitlement": key,
                    "plan": plan_key,
                }
            )
        if item.limit is None:
            return
        used = await self.used(tenant_id, key)
        if used + increment > item.limit:
            raise _denied(
                {
                    "code": "plan_expired" if expired else "plan_limit_reached",
                    "message": (
                        "Your plan has expired."
                        if expired
                        else f"You have reached your {plan_key.capitalize()} plan limit "
                        f"for {label.lower()} ({used} of {item.limit}). Upgrade your plan to "
                        "continue."
                    ),
                    "entitlement": key,
                    "limit": item.limit,
                    "used": used,
                    "plan": plan_key,
                }
            )

    async def snapshot(self, tenant_id: str) -> dict:
        """Everything the UI needs: applied plan, each entitlement with its usage."""
        plan_key, expired, effective = await self.resolve(tenant_id)
        items = []
        for key, item in effective.items():
            definition = CATALOG[key]
            used = await self.used(tenant_id, key) if definition.kind == "limit" else None
            items.append(
                {
                    "key": key,
                    "kind": item.kind,
                    "label_en": definition.label_en,
                    "label_bn": definition.label_bn,
                    "enabled": item.enabled,
                    "limit": item.limit,
                    "used": used,
                    "period": definition.period,
                    "source": item.source,
                }
            )
        return {"plan": plan_key, "expired": expired, "entitlements": items}
