/** Checkout (matches backend app/shared/schemas/checkout.py). */

export type OrderStatus = 'pending' | 'paid' | 'failed' | 'cancelled' | 'expired'
export type BillingPeriod = 'monthly' | 'yearly'
export type OrderKind = 'subscription' | 'credit_pack'

/** subscribe | renew | upgrade | current (never expires) | blocked | unavailable (no online price) */
export type PlanAction = 'subscribe' | 'renew' | 'upgrade' | 'current' | 'blocked' | 'unavailable'

export interface PlanOption {
  plan_key: string
  name_en: string
  name_bn: string | null
  /** Decimal strings from the API; null = no online price */
  price_monthly: string | null
  price_yearly: string | null
  currency: string
  action: PlanAction
  reason: string | null
}

export interface SubscriptionInfo {
  plan: string
  /** Plan whose limits apply right now (Free after expiry) */
  applied_plan: string
  expired: boolean
  plan_expires_at: string | null
  days_left: number | null
  options: PlanOption[]
  /** Payment methods usable right now, e.g. ["fake"]. Empty = online payment not available. */
  gateways: string[]
  /** True when a usable method moves no real money (the test gateway or a provider sandbox) */
  test_mode: boolean
}

export interface CreditPack {
  id: number
  channel: 'sms' | 'email'
  quantity: number
  price: string
  currency: string
  name_en: string
  name_bn: string | null
  is_active: boolean
  sort_order: number
}

export interface CreditPackInput {
  channel: 'sms' | 'email'
  quantity: number
  price: number
  name_en: string
  name_bn?: string | null
  is_active?: boolean
  sort_order?: number
}

/** Quantity and channel are fixed once a pack exists. */
export type CreditPackUpdate = Partial<Pick<CreditPackInput, 'price' | 'name_en' | 'name_bn' | 'is_active' | 'sort_order'>>

export interface Order {
  id: string
  receipt_no: string
  kind: OrderKind
  status: OrderStatus
  description: string
  amount: string
  currency: string
  plan_key: string | null
  period: BillingPeriod | null
  channel: 'sms' | 'email' | null
  quantity: number | null
  gateway: string
  payer_name: string
  created_at: string
  paid_at: string | null
  /** What was done: {plan, plan_expires_at, extended} or {channel, added, balance} */
  fulfilment: Record<string, unknown> | null
}

export interface AdminOrder extends Order {
  tenant_id: string
  tenant_name: string
  payer_phone: string | null
  gateway_txn_id: string | null
}

export type ManualPaymentMethod = 'cash' | 'bank_transfer' | 'bkash' | 'nagad' | 'rocket' | 'cheque' | 'other'
export type ManualPlanTerm = 'monthly' | 'yearly' | 'until_date' | 'no_expiry'

/** An admin sets a clinic's plan after a payment taken outside the gateways. */
export interface ManualPlanGrantInput {
  plan_key: string
  term: ManualPlanTerm
  until_date?: string | null
  amount: number
  payment_method: ManualPaymentMethod
  reference: string
}

export type CheckoutRequest =
  | { kind: 'subscription'; gateway: string; plan_key: string; period: BillingPeriod }
  | { kind: 'credit_pack'; gateway: string; pack_id: number }

export interface CheckoutResponse {
  order: Order
  /** Send the browser here to pay (full URL) */
  redirect_url: string
}

/** 409 body for refused purchases, e.g. {code:'not_allowed_now', message} */
export interface CheckoutRefusal {
  code: 'not_purchasable' | 'not_allowed_now'
  message: string
}
