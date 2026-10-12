'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { useStartCheckout } from '@/lib/hooks/useCheckout'
import { errorMessage } from '@/lib/apiErrors'
import { formatMoney } from '@/lib/billingFormat'
import { GatewayLabel } from '@/components/billing/GatewayLabel'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import type { CheckoutRequest } from '@/types/checkout'

export interface Purchase {
  /** What is being bought, e.g. "Plus plan, 1 month" */
  summary: string
  amount: string
  currency: string
  build: (gateway: string) => CheckoutRequest
}

/**
 * The step before leaving for the payment page: states exactly what is bought and the amount,
 * then one button per available payment method. Refusals (409) show the server's message.
 */
export function CheckoutConfirmDialog({
  purchase,
  gateways,
  onClose,
}: {
  purchase: Purchase | null
  gateways: string[]
  onClose: () => void
}) {
  const t = useTranslations('billingUi.confirm')
  const start = useStartCheckout()
  const [error, setError] = useState<string | null>(null)
  const [redirecting, setRedirecting] = useState(false)
  const busy = start.isLoading || redirecting

  const close = () => {
    if (busy) return
    setError(null)
    start.reset()
    onClose()
  }

  const pay = async (gateway: string) => {
    if (!purchase) return
    setError(null)
    try {
      const res = await start.mutateAsync(purchase.build(gateway))
      setRedirecting(true)
      window.location.assign(res.redirect_url)
    } catch (e) {
      setError(errorMessage(e, t('failed')))
    }
  }

  return (
    <Dialog open={purchase !== null} onOpenChange={(open) => !open && close()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('title')}</DialogTitle>
          <DialogDescription>{t('description')}</DialogDescription>
        </DialogHeader>
        {purchase && (
          <div className="space-y-4">
            <div className="rounded-lg border bg-muted/40 p-4">
              <p className="text-sm text-muted-foreground">{t('youAreBuying')}</p>
              <p className="font-semibold">{purchase.summary}</p>
              <p className="mt-2 text-sm text-muted-foreground">{t('amount')}</p>
              <p className="text-2xl font-bold">{formatMoney(purchase.amount, purchase.currency)}</p>
            </div>
            {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
            <div className="flex flex-col gap-2">
              {gateways.map((g) => (
                <Button key={g} className="h-11 justify-center" disabled={busy} onClick={() => void pay(g)}>
                  {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                  <span>{t('payWith', { amount: formatMoney(purchase.amount, purchase.currency) })}</span>
                  <span className="ml-2 text-sm font-normal"><GatewayLabel gateway={g} /></span>
                </Button>
              ))}
              <Button variant="outline" className="h-10" disabled={busy} onClick={close}>
                {t('cancel')}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
