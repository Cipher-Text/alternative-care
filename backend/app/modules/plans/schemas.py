"""Schemas for plan configuration, public pricing and tenant entitlements."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    key: str
    kind: str  # "limit" | "feature"
    label_en: str
    label_bn: str
    unit_en: str
    unit_bn: str
    period: str | None


class EntitlementValue(BaseModel):
    key: str
    enabled: bool = True
    limit: int | None = Field(default=None, ge=0, description="None = unlimited (limit kinds)")


class PlanConfig(BaseModel):
    key: str
    name_en: str
    name_bn: str | None
    description_en: str | None
    description_bn: str | None
    price_monthly: Decimal | None
    price_yearly: Decimal | None
    currency: str
    is_public: bool
    sort_order: int
    entitlements: list[EntitlementValue]
    tenant_count: int = 0


class AdminPlansResponse(BaseModel):
    catalog: list[CatalogItem]
    plans: list[PlanConfig]


class PlanUpdateRequest(BaseModel):
    """Full replacement of the editable fields of one plan."""

    name_en: str = Field(..., min_length=1, max_length=100)
    name_bn: str | None = Field(default=None, max_length=100)
    description_en: str | None = None
    description_bn: str | None = None
    price_monthly: Decimal | None = Field(default=None, ge=0)
    price_yearly: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="BDT", min_length=3, max_length=3)
    is_public: bool = True
    entitlements: list[EntitlementValue]


class PlanAuditEntry(BaseModel):
    id: int
    plan_key: str | None
    tenant_id: str | None
    entitlement_key: str | None
    field: str
    old_value: str | None
    new_value: str | None
    changed_by: str | None
    changed_at: datetime


class PublicPlan(BaseModel):
    key: str
    name_en: str
    name_bn: str | None
    description_en: str | None
    description_bn: str | None
    price_monthly: Decimal | None
    price_yearly: Decimal | None
    currency: str
    entitlements: list[EntitlementValue]


class PublicPlansResponse(BaseModel):
    catalog: list[CatalogItem]
    plans: list[PublicPlan]


class TenantEntitlementItem(BaseModel):
    key: str
    kind: str
    label_en: str
    label_bn: str
    enabled: bool
    limit: int | None
    used: int | None
    period: str | None
    source: str  # "plan" | "override"


class TenantEntitlementsResponse(BaseModel):
    plan: str
    expired: bool
    entitlements: list[TenantEntitlementItem]


class OverrideRequest(BaseModel):
    enabled: bool = True
    limit: int | None = Field(default=None, ge=0, description="None = unlimited")
    note: str | None = Field(default=None, max_length=500)
