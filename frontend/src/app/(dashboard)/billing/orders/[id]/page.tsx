'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useQuery } from 'react-query'
import { useTranslations } from 'next-intl'
import { ArrowLeft, Loader2, Printer } from 'lucide-react'
import { authApi } from '@/lib/api/auth'
import { useOrder } from '@/lib/hooks/useCheckout'
import { useDateFormat } from '@/lib/i18n/date'
import { formatMoney } from '@/lib/billingFormat'
import { OrderStatusBadge } from '@/components/billing/OrderStatusBadge'
import { useGatewayName } from '@/components/billing/GatewayLabel'
import { Button } from '@/components/ui/button'
import { useCan } from '@/lib/auth/permissions'

/** A simple printable receipt, issued to the clinic. */
export default function ReceiptPage() {
  const t = useTranslations('billingUi.receipt')
  const { fmt } = useDateFormat()
  const gatewayName = useGatewayName()
  const params = useParams<{ id: string }>()
  const id = typeof params?.id === 'string' ? params.id : null
  const { can } = useCan()
  const isDoctor = can('billing.manage')
  const order = useOrder(id, { enabled: isDoctor })
  const profile = useQuery(['auth', 'me'], () => authApi.getCurrentUser(), { enabled: isDoctor, staleTime: 60000, retry: false })

  if (!isDoctor) return null

  const clinic = profile.data?.tenant?.clinic_name || profile.data?.tenant?.name || null
  const o = order.data

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Link href="/billing" className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:underline dark:text-emerald-400">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t('back')}
        </Link>
        {o && (
          <Button className="h-10" onClick={() => window.print()}>
            <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
            {t('print')}
          </Button>
        )}
      </div>

      {order.isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" aria-hidden="true" />
        </div>
      ) : order.error || !o ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : (
        <article className="rounded-xl border bg-white p-6 text-gray-900 shadow-sm print:border-0 print:p-0 print:shadow-none sm:p-8 dark:bg-slate-900 dark:text-gray-100 print:bg-white print:text-black">
          <header className="flex flex-wrap items-start justify-between gap-4 border-b pb-4">
            <div>
              <p className="text-2xl font-bold">AltCare</p>
              <h1 className="text-lg font-semibold">{t('title')}</h1>
            </div>
            <div className="text-right text-sm">
              <p className="text-muted-foreground print:text-gray-600">{t('receiptNo')}</p>
              <p className="font-mono text-base font-semibold">{o.receipt_no}</p>
            </div>
          </header>

          <dl className="grid grid-cols-1 gap-x-6 gap-y-4 py-6 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('clinic')}</dt>
              <dd className="font-medium">{clinic ?? '-'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('payer')}</dt>
              <dd className="font-medium">{o.payer_name}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground print:text-gray-600">{t('description')}</dt>
              <dd className="font-medium">{o.description}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('amount')}</dt>
              <dd className="text-2xl font-bold">{formatMoney(o.amount, o.currency)}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('status')}</dt>
              <dd className="mt-1"><OrderStatusBadge status={o.status} /></dd>
            </div>
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('ordered')}</dt>
              <dd>{fmt(o.created_at, 'MMM d, yyyy h:mm a')}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('paidOn')}</dt>
              <dd>{o.paid_at ? fmt(o.paid_at, 'MMM d, yyyy h:mm a') : '-'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground print:text-gray-600">{t('method')}</dt>
              <dd>{gatewayName(o.gateway)}</dd>
            </div>
          </dl>

          {o.gateway === 'fake' && (
            <p className="rounded border border-amber-400 bg-amber-50 p-2 text-center text-sm font-semibold text-amber-900 print:text-black">
              {t('testNotice')}
            </p>
          )}
          {o.status !== 'paid' && <p className="mt-3 text-sm text-muted-foreground print:text-gray-600">{t('notPaidNote')}</p>}
        </article>
      )}
    </div>
  )
}
