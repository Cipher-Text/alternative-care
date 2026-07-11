'use client'

import { useRouter } from 'next/navigation'
import { useCreatePatient } from '@/lib/hooks/usePatients'
import { PatientForm } from '@/components/patients/PatientForm'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import type { PatientCreateRequest } from '@/types/patient'

export default function NewPatientPage() {
  const router = useRouter()
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
        <Link href="/patients">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Add New Patient</h1>
          <p className="text-muted-foreground">
            Create a new patient record with their information
          </p>
        </div>
      </div>

      {/* Form */}
      <PatientForm onSubmit={handleSubmit} isSubmitting={createPatient.isLoading} />
    </div>
  )
}
