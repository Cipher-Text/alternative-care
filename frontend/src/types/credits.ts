/** Messaging credits (matches backend app/shared/schemas/credits.py). */

export type CreditChannel = 'sms' | 'email'

export interface ChannelBalance {
  channel: CreditChannel
  /** Plan allowance for the month; null = unlimited */
  allowance_limit: number | null
  allowance_used: number
  allowance_remaining: number | null
  /** Credits the clinic bought; used after the allowance runs out */
  purchased: number
  plan: string
}

export interface CreditSummary {
  channels: ChannelBalance[]
  /** False when the platform has not set up that provider (nothing can be sent) */
  sms_available: boolean
  email_available: boolean
}

export interface LedgerEntry {
  id: number
  channel: CreditChannel
  kind: 'purchase' | 'use' | 'refund' | 'adjustment'
  quantity: number
  balance_after: number
  reference: string | null
  note: string | null
  created_at: string
}

export interface CreditAdjustmentInput {
  channel: CreditChannel
  /** Positive adds, negative removes */
  quantity: number
  note: string
}

/** 403 body when a send is blocked because allowance and purchased credits are both used up. */
export interface CreditsExhaustedDetail {
  code: 'credits_exhausted'
  message: string
  channel: CreditChannel
  allowance_limit: number | null
  allowance_used: number
  purchased: number
  plan: string
}

/** Admin-only: provider configured or not. Never contains credentials. */
export interface MessagingStatus {
  sms: { provider: string | null; configured: boolean }
  email: { provider: string | null; configured: boolean }
}
