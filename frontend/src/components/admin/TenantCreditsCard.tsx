'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2, MessageSquare } from 'lucide-react'
import { useAdjustCredits } from '@/lib/hooks/useBilling'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { CreditChannel } from '@/types/credits'

/** Admin-only: add or remove a clinic's purchased SMS/email credits. Hidden for operators. */
export function TenantCreditsCard({ tenantId }: { tenantId: string }) {
  const t = useTranslations('billingUi.admin.credits')
  const tc = useTranslations('billingUi.channel')
  const adjust = useAdjustCredits(tenantId)
  const [channel, setChannel] = useState<CreditChannel>('sms')
  const [quantity, setQuantity] = useState('')
  const [note, setNote] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [errors, setErrors] = useState<{ quantity?: boolean; note?: boolean; confirm?: boolean }>({})
  const [result, setResult] = useState<{ channel: CreditChannel; purchased: number } | null>(null)

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const qty = Number(quantity)
    const next = {
      quantity: !/^[+-]?\d+$/.test(quantity.trim()) || qty === 0,
      note: note.trim().length < 3,
      confirm: !confirmed,
    }
    setErrors(next)
    if (next.quantity || next.note || next.confirm) return
    try {
      const res = await adjust.mutateAsync({ channel, quantity: qty, note: note.trim() })
      setResult(res)
      setQuantity('')
      setNote('')
      setConfirmed(false)
    } catch {
      /* the mutation's onError already showed the server's reason (422 = would go below zero) */
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('title')}
        </CardTitle>
        <CardDescription>{t('description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={submit} noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>{t('channel')}</Label>
              <Select value={channel} onValueChange={(v) => setChannel(v as CreditChannel)}>
                <SelectTrigger aria-label={t('channel')}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sms">{tc('sms')}</SelectItem>
                  <SelectItem value="email">{tc('email')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="credit-quantity">{t('quantity')}</Label>
              <Input
                id="credit-quantity"
                inputMode="numeric"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                aria-invalid={errors.quantity}
                aria-describedby="credit-quantity-hint"
              />
              <p id="credit-quantity-hint" className={`text-xs ${errors.quantity ? 'text-red-600' : 'text-muted-foreground'}`}>
                {errors.quantity ? t('quantityInvalid') : t('quantityHint')}
              </p>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="credit-note">{t('note')}</Label>
            <Input
              id="credit-note"
              maxLength={500}
              value={note}
              placeholder={t('notePlaceholder')}
              onChange={(e) => setNote(e.target.value)}
              aria-invalid={errors.note}
            />
            {errors.note && <p role="alert" className="text-sm text-red-600">{t('noteRequired')}</p>}
          </div>
          <div className="space-y-1.5">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
              {t('confirm')}
            </label>
            {errors.confirm && <p role="alert" className="text-sm text-red-600">{t('confirmRequired')}</p>}
          </div>
          <Button type="submit" disabled={adjust.isLoading} className="h-10">
            {adjust.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {adjust.isLoading ? t('working') : t('submit')}
          </Button>
          {result && (
            <p role="status" className="text-sm font-medium">
              {t('result', { channel: tc(result.channel), balance: result.purchased })}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
