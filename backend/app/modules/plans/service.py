"""Plan configuration service (admin) and public pricing read."""

import json
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entitlements import (
    CATALOG,
    DEFAULT_PLANS,
    EntitlementService,
    load_plan_values,
    plan_defaults,
)
from app.modules.plans.schemas import (
    AdminPlansResponse,
    CatalogItem,
    EntitlementValue,
    PlanAuditEntry,
    PlanConfig,
    PlanUpdateRequest,
    PublicPlan,
    PublicPlansResponse,
    OverrideRequest,
)
from app.shared.models import (
    Plan,
    PlanAuditLog,
    PlanEntitlement,
    Tenant,
    TenantEntitlementOverride,
)

INF = float("inf")


def _catalog_items() -> list[CatalogItem]:
    return [
        CatalogItem(
            key=d.key,
            kind=d.kind,
            label_en=d.label_en,
            label_bn=d.label_bn,
            unit_en=d.unit_en,
            unit_bn=d.unit_bn,
            period=d.period,
        )
        for d in CATALOG.values()
    ]


def _fmt(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


class PlansService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- reading -------------------------------------------------------------------------

    async def _ensure_plan_rows(self) -> dict[str, Plan]:
        """Materialise any missing plan rows from the code defaults (idempotent)."""
        result = await self.db.execute(select(Plan))
        plans = {p.key: p for p in result.scalars().all()}
        created = False
        for key, d in DEFAULT_PLANS.items():
            if key not in plans:
                plan = Plan(
                    key=key,
                    name_en=d.name_en,
                    name_bn=d.name_bn,
                    description_en=d.description_en,
                    description_bn=d.description_bn,
                    price_monthly=d.price_monthly,
                    price_yearly=d.price_yearly,
                    currency="BDT",
                    is_public=True,
                    sort_order=d.sort_order,
                )
                self.db.add(plan)
                plans[key] = plan
                created = True
        if created:
            await self.db.commit()
        return plans

    async def plan_rows(self) -> dict[str, Plan]:
        """All plan rows by key, creating any missing ones from the code defaults."""
        return await self._ensure_plan_rows()

    async def _plan_config(self, plan: Plan, tenant_count: int = 0) -> PlanConfig:
        values = await load_plan_values(self.db, plan.key)
        return PlanConfig(
            key=plan.key,
            name_en=plan.name_en,
            name_bn=plan.name_bn,
            description_en=plan.description_en,
            description_bn=plan.description_bn,
            price_monthly=plan.price_monthly,
            price_yearly=plan.price_yearly,
            currency=plan.currency,
            is_public=plan.is_public,
            sort_order=plan.sort_order,
            entitlements=[
                EntitlementValue(key=k, enabled=values[k][0], limit=values[k][1]) for k in CATALOG
            ],
            tenant_count=tenant_count,
        )

    async def admin_plans(self) -> AdminPlansResponse:
        plans = await self._ensure_plan_rows()
        counts = dict(
            (
                await self.db.execute(
                    select(Tenant.plan, func.count()).group_by(Tenant.plan)
                )
            ).all()
        )
        ordered = sorted(plans.values(), key=lambda p: (p.sort_order, p.key))
        return AdminPlansResponse(
            catalog=_catalog_items(),
            plans=[await self._plan_config(p, counts.get(p.key, 0)) for p in ordered],
        )

    async def public_plans(self) -> PublicPlansResponse:
        plans = await self._ensure_plan_rows()
        ordered = [p for p in sorted(plans.values(), key=lambda p: (p.sort_order, p.key)) if p.is_public]
        out = []
        for plan in ordered:
            cfg = await self._plan_config(plan)
            out.append(PublicPlan(**cfg.model_dump(exclude={"tenant_count", "is_public", "sort_order"})))
        return PublicPlansResponse(catalog=_catalog_items(), plans=out)

    async def audit(self, limit: int = 100, plan_key: str | None = None) -> list[PlanAuditEntry]:
        query = select(PlanAuditLog).order_by(PlanAuditLog.id.desc()).limit(limit)
        if plan_key:
            query = query.where(PlanAuditLog.plan_key == plan_key)
        rows = (await self.db.execute(query)).scalars().all()
        return [
            PlanAuditEntry(
                id=r.id,
                plan_key=r.plan_key,
                tenant_id=r.tenant_id,
                entitlement_key=r.entitlement_key,
                field=r.field,
                old_value=r.old_value,
                new_value=r.new_value,
                changed_by=r.changed_by,
                changed_at=r.changed_at,
            )
            for r in rows
        ]

    # ----- updating ------------------------------------------------------------------------

    async def _validate_ordering(
        self, plan_key: str, new_values: dict[str, tuple[bool, int | None]]
    ) -> None:
        """A higher plan must never allow less than a lower plan (by sort_order)."""
        plans = await self._ensure_plan_rows()
        ordered = sorted(plans.values(), key=lambda p: (p.sort_order, p.key))
        values: dict[str, dict[str, tuple[bool, int | None]]] = {}
        for p in ordered:
            values[p.key] = (
                new_values if p.key == plan_key else await load_plan_values(self.db, p.key)
            )

        for lower, higher in zip(ordered, ordered[1:]):
            for key, definition in CATALOG.items():
                lo_enabled, lo_limit = values[lower.key][key]
                hi_enabled, hi_limit = values[higher.key][key]
                if definition.kind == "feature":
                    if lo_enabled and not hi_enabled:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"{definition.label_en} is on for {lower.name_en} but off for "
                            f"{higher.name_en}. A higher plan cannot offer less.",
                        )
                else:
                    lo = (lo_limit if lo_limit is not None else INF) if lo_enabled else -1
                    hi = (hi_limit if hi_limit is not None else INF) if hi_enabled else -1
                    if lo > hi:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"{definition.label_en}: {lower.name_en} allows more than "
                            f"{higher.name_en}. A higher plan cannot offer less.",
                        )

    async def update_plan(
        self, plan_key: str, data: PlanUpdateRequest, admin_user_id: str
    ) -> PlanConfig:
        if plan_key not in DEFAULT_PLANS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        unknown = {e.key for e in data.entitlements} - set(CATALOG)
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown entitlement(s): {sorted(unknown)}",
            )
        if (
            data.price_monthly is not None
            and data.price_yearly is not None
            and data.price_yearly > data.price_monthly * 12
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Yearly price cannot exceed 12 times the monthly price.",
            )

        plans = await self._ensure_plan_rows()
        plan = plans[plan_key]

        current = await load_plan_values(self.db, plan_key)
        new_values = dict(current)
        for e in data.entitlements:
            kind = CATALOG[e.key].kind
            # features have no limit; limits are on unless limit is explicitly 0
            new_values[e.key] = (e.enabled, None if kind == "feature" else e.limit)
        await self._validate_ordering(plan_key, new_values)

        def log(field: str, old: object, new: object, ent: str | None = None) -> None:
            if _fmt(old) != _fmt(new):
                self.db.add(
                    PlanAuditLog(
                        plan_key=plan_key,
                        entitlement_key=ent,
                        field=field,
                        old_value=_fmt(old),
                        new_value=_fmt(new),
                        changed_by=admin_user_id,
                    )
                )

        for field in (
            "name_en", "name_bn", "description_en", "description_bn",
            "price_monthly", "price_yearly", "currency", "is_public",
        ):
            new = getattr(data, field)
            log(field, getattr(plan, field), new)
            setattr(plan, field, new)
        plan.updated_by = admin_user_id

        existing = {
            r.entitlement_key: r
            for r in (
                await self.db.execute(
                    select(PlanEntitlement).where(PlanEntitlement.plan_key == plan_key)
                )
            ).scalars().all()
        }
        for key, (enabled, limit) in new_values.items():
            old_enabled, old_limit = current[key]
            log("enabled", old_enabled, enabled, key)
            log("limit", old_limit, limit, key)
            row = existing.get(key)
            if row is None:
                self.db.add(
                    PlanEntitlement(
                        plan_key=plan_key,
                        entitlement_key=key,
                        enabled=enabled,
                        limit_value=limit,
                        created_by=admin_user_id,
                    )
                )
            else:
                row.enabled = enabled
                row.limit_value = limit
                row.updated_by = admin_user_id

        await self.db.commit()
        await self.db.refresh(plan)
        return await self._plan_config(plan)

    # ----- per-tenant ----------------------------------------------------------------------

    async def _tenant_or_404(self, tenant_id: str) -> Tenant:
        tenant = (
            await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return tenant

    async def tenant_entitlements(self, tenant_id: str) -> dict:
        await self._tenant_or_404(tenant_id)
        return await EntitlementService(self.db).snapshot(tenant_id)

    async def set_override(
        self, tenant_id: str, key: str, data: OverrideRequest, admin_user_id: str
    ) -> dict:
        await self._tenant_or_404(tenant_id)
        if key not in CATALOG:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown entitlement")
        limit = None if CATALOG[key].kind == "feature" else data.limit

        row = (
            await self.db.execute(
                select(TenantEntitlementOverride).where(
                    TenantEntitlementOverride.tenant_id == tenant_id,
                    TenantEntitlementOverride.entitlement_key == key,
                )
            )
        ).scalar_one_or_none()
        old = None if row is None else json.dumps({"enabled": row.enabled, "limit": row.limit_value})
        if row is None:
            row = TenantEntitlementOverride(
                tenant_id=tenant_id, entitlement_key=key, created_by=admin_user_id
            )
            self.db.add(row)
        row.enabled = data.enabled
        row.limit_value = limit
        row.note = data.note
        row.updated_by = admin_user_id
        self.db.add(
            PlanAuditLog(
                tenant_id=tenant_id,
                entitlement_key=key,
                field="override",
                old_value=old,
                new_value=json.dumps({"enabled": data.enabled, "limit": limit, "note": data.note}),
                changed_by=admin_user_id,
            )
        )
        await self.db.commit()
        return await EntitlementService(self.db).snapshot(tenant_id)

    async def delete_override(self, tenant_id: str, key: str, admin_user_id: str) -> dict:
        await self._tenant_or_404(tenant_id)
        row = (
            await self.db.execute(
                select(TenantEntitlementOverride).where(
                    TenantEntitlementOverride.tenant_id == tenant_id,
                    TenantEntitlementOverride.entitlement_key == key,
                )
            )
        ).scalar_one_or_none()
        if row is not None:
            self.db.add(
                PlanAuditLog(
                    tenant_id=tenant_id,
                    entitlement_key=key,
                    field="override",
                    old_value=json.dumps({"enabled": row.enabled, "limit": row.limit_value}),
                    new_value=None,
                    changed_by=admin_user_id,
                )
            )
            await self.db.delete(row)
            await self.db.commit()
        return await EntitlementService(self.db).snapshot(tenant_id)
