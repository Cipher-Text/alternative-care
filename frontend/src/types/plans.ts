/** Plan configuration & entitlements (mirrors backend app/modules/plans/schemas.py). */

export type EntitlementKind = 'limit' | 'feature'

export interface CatalogItem {
  key: string
  kind: EntitlementKind
  label_en: string
  label_bn: string
  unit_en: string
  unit_bn: string
  period: 'total' | 'monthly' | 'quarterly' | null
}

export interface EntitlementValue {
  key: string
  enabled: boolean
  /** null = unlimited (limit kinds) */
  limit: number | null
}

export interface PlanConfig {
  key: string
  name_en: string
  name_bn: string | null
  description_en: string | null
  description_bn: string | null
  /** Decimal serialised as a string; null = "contact us" */
  price_monthly: string | null
  price_yearly: string | null
  currency: string
  is_public: boolean
  sort_order: number
  entitlements: EntitlementValue[]
  tenant_count: number
}

export interface AdminPlansResponse {
  catalog: CatalogItem[]
  plans: PlanConfig[]
}

export interface PlanUpdateRequest {
  name_en: string
  name_bn: string | null
  description_en: string | null
  description_bn: string | null
  price_monthly: string | null
  price_yearly: string | null
  currency: string
  is_public: boolean
  entitlements: EntitlementValue[]
}

export interface PlanAuditEntry {
  id: number
  plan_key: string | null
  tenant_id: string | null
  entitlement_key: string | null
  field: string
  old_value: string | null
  new_value: string | null
  changed_by: string | null
  changed_at: string
}

export interface PublicPlan {
  key: string
  name_en: string
  name_bn: string | null
  description_en: string | null
  description_bn: string | null
  price_monthly: string | null
  price_yearly: string | null
  currency: string
  entitlements: EntitlementValue[]
}

export interface PublicPlansResponse {
  catalog: CatalogItem[]
  plans: PublicPlan[]
}

export interface TenantEntitlementItem {
  key: string
  kind: EntitlementKind
  label_en: string
  label_bn: string
  enabled: boolean
  limit: number | null
  used: number | null
  period: 'total' | 'monthly' | 'quarterly' | null
  source: 'plan' | 'override'
}

export interface TenantEntitlements {
  plan: string
  expired: boolean
  entitlements: TenantEntitlementItem[]
}

export interface OverrideRequest {
  enabled: boolean
  limit: number | null
  note?: string | null
}
