'use client'

import { useTranslations } from 'next-intl'
import { PrescriptionBuilder } from '@/components/prescriptions/PrescriptionBuilder'

export default function NewPrescriptionPage() {
  const t = useTranslations('rxNewUi')
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t('title')}</h1>
        <p className="text-muted-foreground">{t('subtitle')}</p>
      </div>

      <PrescriptionBuilder />
    </div>
  )
}
