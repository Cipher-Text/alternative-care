'use client'

import { PrescriptionBuilder } from '@/components/prescriptions/PrescriptionBuilder'

export default function NewPrescriptionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">New Prescription</h1>
        <p className="text-muted-foreground">Create a new prescription for a patient</p>
      </div>

      <PrescriptionBuilder />
    </div>
  )
}
