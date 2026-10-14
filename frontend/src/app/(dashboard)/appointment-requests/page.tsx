'use client'

import { useTranslations } from 'next-intl'
import { RequestsList } from '@/components/appointment-requests/RequestsList'
import { useCan } from '@/lib/auth/permissions'

export default function AppointmentRequestsPage() {
  const t = useTranslations('appointmentRequestsUi')
  // Doctors and receptionists; platform staff have no clinic
  const { can } = useCan()
  const allowed = can('appointment_requests.manage')
  if (!allowed) return null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>
      <RequestsList />
    </div>
  )
}
