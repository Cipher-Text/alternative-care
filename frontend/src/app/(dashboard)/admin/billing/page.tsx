'use client'

import { useTranslations } from 'next-intl'
import { ShieldAlert } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { AdminOrdersSection } from '@/components/admin/AdminOrdersSection'
import { AdminPacksSection } from '@/components/admin/AdminPacksSection'
import { Card, CardContent } from '@/components/ui/card'
import { useCan } from '@/lib/auth/permissions'

/** Platform admin: credit pack catalogue and every clinic's orders. Admin only (operators get no access). */
export default function AdminBillingPage() {
  const t = useTranslations('billingUi.adminBilling')
  const user = useAuthStore((s) => s.user)
  const { can } = useCan()

  if (user && !can('billing.admin')) {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 p-6">
          <ShieldAlert className="h-5 w-5 text-red-500" aria-hidden="true" />
          {t('adminOnly')}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>
      <AdminPacksSection />
      <AdminOrdersSection />
    </div>
  )
}
