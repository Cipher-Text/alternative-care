import type { PlanOption } from '@/types/checkout'

/** "৳1,200" (decimal strings from the API; BDT is the only currency today). */
export function formatMoney(amount: string | number | null | undefined, currency = 'BDT'): string {
  if (amount === null || amount === undefined || amount === '') return '-'
  const n = Number(amount)
  if (!Number.isFinite(n)) return String(amount)
  const text = n.toLocaleString('en-US', { maximumFractionDigits: 2 })
  return currency === 'BDT' ? `৳${text}` : `${currency} ${text}`
}

/** Plan name in the UI language. */
export function planName(option: Pick<PlanOption, 'name_en' | 'name_bn'>, locale: string): string {
  return locale === 'bn' && option.name_bn ? option.name_bn : option.name_en
}

const PLAN_KEY_NAMES: Record<string, { en: string; bn: string }> = {
  free: { en: 'Free', bn: 'ফ্রি' },
  plus: { en: 'Plus', bn: 'প্লাস' },
  pro: { en: 'Pro', bn: 'প্রো' },
  enterprise: { en: 'Enterprise', bn: 'এন্টারপ্রাইজ' },
}

/** Display name for a stored plan key, e.g. for Free, which is never in the purchasable options. */
export function planKeyName(key: string, locale: string): string {
  const known = PLAN_KEY_NAMES[key]
  if (!known) return key.charAt(0).toUpperCase() + key.slice(1)
  return locale === 'bn' ? known.bn : known.en
}

/** Name for a pack/plan with optional Bengali text. */
export function localName(en: string, bn: string | null | undefined, locale: string): string {
  return locale === 'bn' && bn ? bn : en
}

/** How much paying yearly saves against twelve monthly payments, or null when not computable. */
export function yearlySaving(option: Pick<PlanOption, 'price_monthly' | 'price_yearly'>): { amount: number; percent: number } | null {
  if (option.price_monthly === null || option.price_yearly === null) return null
  const monthly = Number(option.price_monthly)
  const yearly = Number(option.price_yearly)
  if (!Number.isFinite(monthly) || !Number.isFinite(yearly) || monthly <= 0) return null
  const amount = monthly * 12 - yearly
  if (amount <= 0) return null
  return { amount, percent: Math.round((amount / (monthly * 12)) * 100) }
}
