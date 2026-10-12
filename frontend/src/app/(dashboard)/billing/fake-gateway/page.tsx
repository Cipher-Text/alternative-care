'use client'

import { Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { FlaskConical, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useCompleteFake, useOrder } from '@/lib/hooks/useCheckout'
import { errorMessage } from '@/lib/apiErrors'
import { formatMoney } from '@/lib/billingFormat'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type Outcome = 'success' | 'failed' | 'cancelled'

/** TEST payment page: a tester picks the outcome. Real gateways have their own hosted pages. */
function FakeGateway() {
  const t = useTranslations('billingUi.fake')
  const router = useRouter()
  const search = useSearchParams()
  const id = search.get('order')
  const isDoctor = useAuthStore((s) => s.user?.role === 'doctor')
  const order = useOrder(id, { enabled: isDoctor })
  const complete = useCompleteFake()
  const status = order.data?.status

  // Already settled (or opened twice): nothing to choose, go to the result
  useEffect(() => {
    if (id && status && status !== 'pending') router.replace(`/billing/return?order=${encodeURIComponent(id)}`)
  }, [id, status, router])

  if (!isDoctor) return null

  const choose = async (outcome: Outcome) => {
    if (!id) return
    try {
      await complete.mutateAsync({ id, outcome })
    } catch {
      /* shown below; the return page re-checks the real state either way for a 409 */
      return
    }
    router.push(`/billing/return?order=${encodeURIComponent(id)}`)
  }

  const o = order.data

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <div role="alert" className="flex items-center gap-3 rounded-lg bg-amber-400 p-4 text-black">
        <FlaskConical className="h-7 w-7 shrink-0" aria-hidden="true" />
        <p className="text-xl font-extrabold">{t('banner')}</p>
      </div>

      {!id ? (
        <p role="alert" className="text-sm text-red-600">{t('missingOrder')}</p>
      ) : order.isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" aria-hidden="true" />
        </div>
      ) : order.error || !o ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>{t('title')}</CardTitle>
            <CardDescription>{t('description')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="rounded-lg border bg-muted/40 p-4">
              <p className="text-sm text-muted-foreground">{o.receipt_no}</p>
              <p className="font-semibold">{o.description}</p>
              <p className="mt-2 text-3xl font-bold">{formatMoney(o.amount, o.currency)}</p>
            </div>
            {complete.error != null && (
              <p role="alert" className="text-sm text-red-600">{errorMessage(complete.error, t('completeFailed'))}</p>
            )}
            <div className="flex flex-col gap-2">
              <Button className="h-11 bg-emerald-600 hover:bg-emerald-700" disabled={complete.isLoading} onClick={() => void choose('success')}>
                {complete.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                {t('paySuccess')}
              </Button>
              <Button variant="destructive" className="h-11" disabled={complete.isLoading} onClick={() => void choose('failed')}>
                {t('payFailed')}
              </Button>
              <Button variant="outline" className="h-11" disabled={complete.isLoading} onClick={() => void choose('cancelled')}>
                {t('cancel')}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default function FakeGatewayPage() {
  return (
    <Suspense fallback={null}>
      <FakeGateway />
    </Suspense>
  )
}
