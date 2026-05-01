'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { usePatient, useUpdatePatient } from '@/lib/hooks/usePatients'
import { PatientForm } from '@/components/patients/PatientForm'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Loader2 } from 'lucide-react'
import type { PatientUpdateRequest } from '@/types/patient'

export default function EditPatientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const { data: patient, isLoading } = usePatient(id)
  const updatePatient = useUpdatePatient()

  const handleSubmit = async (data: PatientUpdateRequest) => {
    await updatePatient.mutateAsync({ id, data })
    router.push(`/patients/${id}`)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Patient not found</p>
        <Link href="/patients">
          <Button className="mt-4">Back to Patients</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/patients/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Edit Patient</h1>
          <p className="text-muted-foreground">
            Update patient information for {patient.first_name} {patient.last_name}
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
