'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { usePatient, useUpdatePatient } from '@/lib/hooks/usePatients'
import { PatientForm } from '@/components/patients/PatientForm'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Loader2 } from 'lucide-react'
import type { PatientUpdateRequest } from '@/types/patient'

export default function EditPatientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const t = useTranslations('patientEditUi')
  const tu = useTranslations('patientsUi')
  const td = useTranslations('patientDetailUi')
  const { data: patient, isLoading } = usePatient(id)
  const updatePatient = useUpdatePatient()

  const handleSubmit = async (data: PatientUpdateRequest) => {
    try {
      await updatePatient.mutateAsync({ id, data })
      router.push(`/patients/${id}`)
    } catch {
      // error is handled by onError in useUpdatePatient (shows toast)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">{t('notFound')}</p>
        <Link href="/patients">
          <Button className="mt-4">{td('backToPatients')}</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/patients/${id}`}>
          <Button variant="ghost" size="icon" aria-label={tu('back')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">{t('title')}</h1>
          <p className="text-muted-foreground">
            {t('subtitle', { name: patient.full_name })}
          </p>
        </div>
      </div>

      {/* Form */}
      <PatientForm
        patient={patient}
        onSubmit={handleSubmit}
        isSubmitting={updatePatient.isLoading}
      />
    </div>
  )
}
