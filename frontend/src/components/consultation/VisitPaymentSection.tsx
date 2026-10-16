'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { Banknote, Loader2, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { errorMessage } from '@/lib/apiErrors'
import { useCan } from '@/lib/auth/permissions'
import { useClinicProfile } from '@/lib/hooks/useClinicLogo'
import { useCreatePayment, usePayments } from '@/lib/hooks/usePayments'
import type { PaymentMethod } from '@/types/payment'
import { visitFeeBdt } from './visitDraft'

/** What was paid for this visit, and a quick way to record a payment (cash, prefilled with the clinic's usual fee). */
export function VisitPaymentSection({ visitId, patientId, visitType }: { visitId: string; patientId: string; visitType: string }) {
  const t = useTranslations('consultationUi.payment')
  const locale = useLocale()
  const { can } = useCan()
  const { data: clinic } = useClinicProfile()
  const { data: payments } = usePayments({ visit_id: visitId, limit: 50 })
  const create = useCreatePayment()
  const [open, setOpen] = useState(false)
  const [amount, setAmount] = useState('')
  const [method, setMethod] = useState<PaymentMethod>('cash')
  const [note, setNote] = useState('')

  const money = (n: number) => new Intl.NumberFormat(locale, { style: 'currency', currency: 'BDT', maximumFractionDigits: 0 }).format(n)
  const fee = visitFeeBdt(visitType, clinic)
  const paid = (payments ?? []).filter((p) => p.status === 'paid').reduce((sum, p) => sum + Number(p.amount), 0)
  const due = fee !== null ? Math.max(0, fee - paid) : null

  const startRecording = () => {
    setAmount(due && due > 0 ? String(due) : fee !== null && paid === 0 ? String(fee) : '')
    setOpen(true)
  }

  const record = async () => {
    const value = Number(amount)
    if (!Number.isFinite(value) || value <= 0) {
      toast.error(t('badAmount'))
      return
    }
    try {
      await create.mutateAsync({ patient_id: patientId, visit_id: visitId, amount: value, payment_method: method, description: note.trim() || undefined })
      toast.success(t('recorded'))
      setOpen(false)
      setNote('')
    } catch (error) {
      toast.error(errorMessage(error, t('failed')))
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Banknote className="h-5 w-5 text-emerald-600" aria-hidden="true" />
            {t('title')}
          </CardTitle>
          {can('payments.write') && !open && (
            <Button type="button" variant="outline" size="sm" onClick={startRecording}>
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              {t('record')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">
          {fee !== null ? t('usualFee', { fee: money(fee) }) : t('noFee')}
          {' · '}
          <span className="font-medium text-foreground">{t('paid', { amount: money(paid) })}</span>
          {due !== null && due > 0 && paid > 0 && <span className="text-amber-600"> · {t('stillDue', { amount: money(due) })}</span>}
        </p>
        {(payments ?? []).map((p) => (
          <div key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 text-sm">
            <span>
              <span className="font-medium">{money(Number(p.amount))}</span>
              <span className="ml-2 text-muted-foreground">
                {t(`method.${p.payment_method}`)} · {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(`${p.payment_date}T00:00:00`))}
                {p.description ? ` · ${p.description}` : ''}
              </span>
            </span>
            {p.status !== 'paid' && <Badge variant="secondary">{p.status}</Badge>}
          </div>
        ))}
        {payments && payments.length === 0 && !open && <p className="text-sm text-muted-foreground">{t('none')}</p>}

        {open && (
          <div className="grid grid-cols-1 gap-3 rounded-md border bg-muted/30 p-3 sm:grid-cols-[10rem_10rem_1fr_auto] sm:items-end">
            <div className="space-y-1.5">
              <Label htmlFor="pay-amount">{t('amount')}</Label>
              <Input id="pay-amount" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value.replace(/[^\d.]/g, ''))} autoFocus />
            </div>
            <div className="space-y-1.5">
              <Label>{t('methodLabel')}</Label>
              <Select value={method} onValueChange={(v) => setMethod(v as PaymentMethod)}>
                <SelectTrigger aria-label={t('methodLabel')}><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">{t('method.cash')}</SelectItem>
                  <SelectItem value="bkash">{t('method.bkash')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="pay-note">{t('note')}</Label>
              <Input id="pay-note" maxLength={200} value={note} onChange={(e) => setNote(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Button type="button" onClick={record} disabled={create.isLoading}>
                {create.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                {t('save')}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>{t('cancel')}</Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
