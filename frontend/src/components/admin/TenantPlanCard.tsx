'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { CreditCard, Loader2 } from 'lucide-react'
import { useAdminPlans } from '@/lib/hooks/usePlans'
import { useGrantPlan } from '@/lib/hooks/useCheckout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { ManualPaymentMethod, ManualPlanTerm } from '@/types/checkout'

const METHODS: ManualPaymentMethod[] = ['cash', 'bank_transfer', 'bkash', 'nagad', 'rocket', 'cheque', 'other']
const TERMS: ManualPlanTerm[] = ['monthly', 'yearly', 'until_date', 'no_expiry']

interface Props {
  tenantId: string
  currentPlan: string
  currentExpiresAt?: string | null
}

/** Admin-only: move a clinic to a plan after a payment taken outside the gateways (cash, bank, mobile transfer). */
export function TenantPlanCard({ tenantId, currentPlan, currentExpiresAt }: Props) {
  const t = useTranslations('billingUi.admin.plan')
  const locale = useLocale()
  const plans = useAdminPlans()
  const grant = useGrantPlan(tenantId)
  const [planKey, setPlanKey] = useState('')
  const [term, setTerm] = useState<ManualPlanTerm>('monthly')
  const [untilDate, setUntilDate] = useState('')
  const [amount, setAmount] = useState('')
  const [method, setMethod] = useState<ManualPaymentMethod>('bank_transfer')
  const [reference, setReference] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [errors, setErrors] = useState<{ plan?: boolean; date?: boolean; amount?: boolean; reference?: boolean; confirm?: boolean }>({})

  const planOptions = plans.data?.plans ?? []
  const isFree = planKey === 'free'
  const effectiveTerm: ManualPlanTerm = isFree ? 'no_expiry' : term
  const fmt = (iso: string) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(iso))

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const amountNumber = Number(amount)
    const next = {
      plan: !planKey,
      date: effectiveTerm === 'until_date' && !untilDate,
      amount: amount.trim() === '' || !Number.isFinite(amountNumber) || amountNumber < 0,
      reference: reference.trim().length < 3,
      confirm: !confirmed,
    }
    setErrors(next)
    if (Object.values(next).some(Boolean)) return
    try {
      await grant.mutateAsync({
        plan_key: planKey,
        term: effectiveTerm,
        until_date: effectiveTerm === 'until_date' ? untilDate : null,
        amount: amountNumber,
        payment_method: method,
        reference: reference.trim(),
      })
      setAmount('')
      setReference('')
      setConfirmed(false)
    } catch {
      /* the mutation's onError already showed the server's reason */
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('title')}
        </CardTitle>
        <CardDescription>{t('description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">{t('current')}</span>
          <Badge variant="outline" className="capitalize">{currentPlan}</Badge>
          <span className="text-muted-foreground">
            {currentExpiresAt ? t('expires', { date: fmt(currentExpiresAt) }) : t('noExpiry')}
          </span>
        </p>
        <form className="space-y-4" onSubmit={submit} noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>{t('plan')}</Label>
              <Select value={planKey} onValueChange={setPlanKey}>
                <SelectTrigger aria-label={t('plan')} aria-invalid={errors.plan}>
                  <SelectValue placeholder={t('planPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {planOptions.map((p) => (
                    <SelectItem key={p.key} value={p.key}>{p.name_en}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.plan && <p role="alert" className="text-sm text-red-600">{t('planRequired')}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>{t('term')}</Label>
              <Select value={effectiveTerm} onValueChange={(v) => setTerm(v as ManualPlanTerm)} disabled={isFree}>
                <SelectTrigger aria-label={t('term')}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TERMS.map((x) => (
                    <SelectItem key={x} value={x}>{t(`terms.${x}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {isFree && <p className="text-xs text-muted-foreground">{t('freeHint')}</p>}
            </div>
            {effectiveTerm === 'until_date' && (
              <div className="space-y-1.5">
                <Label htmlFor="plan-until">{t('untilDate')}</Label>
                <Input id="plan-until" type="date" value={untilDate} onChange={(e) => setUntilDate(e.target.value)} aria-invalid={errors.date} />
                {errors.date && <p role="alert" className="text-sm text-red-600">{t('dateRequired')}</p>}
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="plan-amount">{t('amount')}</Label>
              <Input id="plan-amount" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} aria-invalid={errors.amount} />
              <p className={`text-xs ${errors.amount ? 'text-red-600' : 'text-muted-foreground'}`}>
                {errors.amount ? t('amountInvalid') : t('amountHint')}
              </p>
            </div>
            <div className="space-y-1.5">
              <Label>{t('method')}</Label>
              <Select value={method} onValueChange={(v) => setMethod(v as ManualPaymentMethod)}>
                <SelectTrigger aria-label={t('method')}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {METHODS.map((m) => (
                    <SelectItem key={m} value={m}>{t(`methods.${m}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="plan-reference">{t('reference')}</Label>
            <Input id="plan-reference" maxLength={200} value={reference} placeholder={t('referencePlaceholder')} onChange={(e) => setReference(e.target.value)} aria-invalid={errors.reference} />
            {errors.reference && <p role="alert" className="text-sm text-red-600">{t('referenceRequired')}</p>}
          </div>
          <div className="space-y-1.5">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
              {t('confirm')}
            </label>
            {errors.confirm && <p role="alert" className="text-sm text-red-600">{t('confirmRequired')}</p>}
          </div>
          <Button type="submit" disabled={grant.isLoading} className="h-10">
            {grant.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {grant.isLoading ? t('working') : t('submit')}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
