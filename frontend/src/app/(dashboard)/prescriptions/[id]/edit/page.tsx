'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { usePrescription } from '@/lib/hooks/usePrescriptions'
import { PrescriptionBuilder } from '@/components/prescriptions/PrescriptionBuilder'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'

export default function EditPrescriptionPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const { data: prescription, isLoading, error } = usePrescription(id)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error || !prescription) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Prescription Not Found</h2>
        <p className="text-muted-foreground mb-4">
          The prescription you're trying to edit doesn't exist or has been removed.
        </p>
        <Link href="/prescriptions">
          <Button>Back to Prescriptions</Button>
        </Link>
      </div>
    )
  }

  if (prescription.status !== 'draft') {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-amber-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Cannot Edit Prescription</h2>
        <p className="text-muted-foreground mb-4">
          Only draft prescriptions can be edited. This prescription has status: {prescription.status}
        </p>
        <Link href={`/prescriptions/${id}`}>
          <Button>View Prescription</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/prescriptions/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Edit Prescription</h1>
          <p className="text-sm text-muted-foreground font-mono">ID: {prescription.id}</p>
        </div>
      </div>

      <PrescriptionBuilder prescription={prescription} isEdit />
    </div>
  )
}
