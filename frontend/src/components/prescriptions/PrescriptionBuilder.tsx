'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useCreatePrescription, useUpdatePrescription } from '@/lib/hooks/usePrescriptions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { PatientSelector } from './PatientSelector'
import { MedicineItemsBuilder } from './MedicineItemsBuilder'
import type { Prescription, PrescriptionItemCreate } from '@/types/prescription'
import { Save, CheckCircle, Loader2 } from 'lucide-react'

interface PrescriptionBuilderProps {
  prescription?: Prescription
  isEdit?: boolean
}

export function PrescriptionBuilder({ prescription, isEdit = false }: PrescriptionBuilderProps) {
  const router = useRouter()
  const createPrescription = useCreatePrescription()
  const updatePrescription = useUpdatePrescription()

  // Form state
  const [patientId, setPatientId] = useState<string>(prescription?.patient_id || '')
  const [visitId, setVisitId] = useState<string>(prescription?.visit_id || '')
  const [diagnosis, setDiagnosis] = useState<string>(prescription?.diagnosis || '')
  const [doctorsNotes, setDoctorsNotes] = useState<string>(prescription?.doctors_notes || '')
  const [advice, setAdvice] = useState<string>(prescription?.advice || '')
  const [items, setItems] = useState<PrescriptionItemCreate[]>(
    prescription?.items.map((item) => ({
      medicine_id: item.medicine_id,
      medicine_name: item.medicine_name,
      dosage: item.dosage,
      frequency: item.frequency,
      duration: item.duration,
      quantity: item.quantity,
      instructions: item.instructions,
      display_order: item.display_order,
    })) || []
  )

  // Validation
  const isValid = patientId && items.length > 0

  const handleSaveDraft = async () => {
    if (!patientId) return

    const data = {
      patient_id: patientId,
      visit_id: visitId || null,
      diagnosis: diagnosis || null,
      doctors_notes: doctorsNotes || null,
      advice: advice || null,
      items,
      status: 'draft' as const,
    }

    if (isEdit && prescription) {
      // Update existing draft
      await updatePrescription.mutateAsync({
        id: prescription.id,
        data: {
          diagnosis: diagnosis || null,
          doctors_notes: doctorsNotes || null,
          advice: advice || null,
        },
      })
      router.push(`/prescriptions/${prescription.id}`)
    } else {
      // Create new draft
      const result = await createPrescription.mutateAsync(data)
      router.push(`/prescriptions/${result.id}`)
    }
  }

  const handleIssue = async () => {
    if (!isValid) return

    const data = {
      patient_id: patientId,
      visit_id: visitId || null,
      diagnosis: diagnosis || null,
      doctors_notes: doctorsNotes || null,
      advice: advice || null,
      items,
      status: 'issued' as const,
    }

    if (isEdit && prescription) {
      // Update and issue
      await updatePrescription.mutateAsync({
        id: prescription.id,
        data: {
          diagnosis: diagnosis || null,
          doctors_notes: doctorsNotes || null,
          advice: advice || null,
          status: 'issued',
        },
      })
      router.push(`/prescriptions/${prescription.id}`)
    } else {
      // Create and issue
      const result = await createPrescription.mutateAsync(data)
      router.push(`/prescriptions/${result.id}`)
    }
  }

  const isLoading = createPrescription.isLoading || updatePrescription.isLoading

  return (
    <div className="space-y-6">
      {/* Patient & Visit Information */}
      <Card>
        <CardHeader>
          <CardTitle>Patient Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="patient">
              Patient <span className="text-red-500">*</span>
            </Label>
            <PatientSelector
              value={patientId}
              onChange={setPatientId}
              disabled={isEdit}
            />
            {isEdit && (
              <p className="text-xs text-muted-foreground">
                Patient cannot be changed when editing
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="visit_id">Visit ID (Optional)</Label>
            <Input
              id="visit_id"
              placeholder="Enter visit ID if applicable"
              value={visitId}
              onChange={(e) => setVisitId(e.target.value)}
              disabled={isEdit}
            />
          </div>
        </CardContent>
      </Card>

      {/* Clinical Information */}
      <Card>
        <CardHeader>
          <CardTitle>Clinical Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="diagnosis">Diagnosis</Label>
            <Input
              id="diagnosis"
              placeholder="Enter diagnosis"
              value={diagnosis}
              onChange={(e) => setDiagnosis(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="doctors_notes">Doctor's Notes</Label>
            <Textarea
              id="doctors_notes"
              placeholder="Enter clinical notes, observations, etc."
              value={doctorsNotes}
              onChange={(e) => setDoctorsNotes(e.target.value)}
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="advice">Advice</Label>
            <Textarea
              id="advice"
              placeholder="Enter advice for the patient (dietary, lifestyle, etc.)"
              value={advice}
              onChange={(e) => setAdvice(e.target.value)}
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Medicines */}
      <Card>
        <CardHeader>
          <CardTitle>
            Medicines <span className="text-red-500">*</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <MedicineItemsBuilder
            items={items}
            onChange={setItems}
            prescriptionId={prescription?.id}
            isEdit={isEdit}
          />
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between items-center sticky bottom-4 bg-background p-4 border rounded-lg shadow-lg">
        <div className="text-sm text-muted-foreground">
          {!isValid && (
            <p className="text-amber-600">
              Please select a patient and add at least one medicine
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={handleSaveDraft}
            disabled={!patientId || isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Save as Draft
          </Button>
          <Button onClick={handleIssue} disabled={!isValid || isLoading}>
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle className="mr-2 h-4 w-4" />
            )}
            Issue Prescription
          </Button>
        </div>
      </div>
    </div>
  )
}
