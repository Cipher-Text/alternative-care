'use client'

import { useTranslations } from 'next-intl'
import { useAuthStore } from '@/store/authStore'
import { RequestsList } from '@/components/appointment-requests/RequestsList'

export default function AppointmentRequestsPage() {
  const t = useTranslations('appointmentRequestsUi')
  // Doctors and receptionists; platform staff have no clinic
  const allowed = useAuthStore((s) => s.user?.role === 'doctor' || s.user?.role === 'receptionist')
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
