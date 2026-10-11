'use client'

import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useCreatePatient } from '@/lib/hooks/usePatients'
import { PatientForm } from '@/components/patients/PatientForm'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import type { PatientCreateRequest } from '@/types/patient'

export default function NewPatientPage() {
  const router = useRouter()
  const t = useTranslations('patientNewUi')
  const tu = useTranslations('patientsUi')
  const createPatient = useCreatePatient()

  const handleSubmit = async (data: PatientCreateRequest) => {
    try {
      await createPatient.mutateAsync(data)
      router.push('/patients')
    } catch {
      // error is handled by onError in useCreatePatient (shows toast)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
            <Link href="/patients" aria-label={tu('back')}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
        <div>
          <h1 className="text-3xl font-bold">{t('title')}</h1>
          <p className="text-muted-foreground">
            {t('subtitle')}
          </p>
        </div>
      </div>

      {/* Form */}
      <PatientForm onSubmit={handleSubmit} isSubmitting={createPatient.isLoading} />
    </div>
  )
}
