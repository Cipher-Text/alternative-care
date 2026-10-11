'use client'

import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useMemo, useState } from 'react'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCreateAppointment } from '@/lib/hooks/useAppointments'
import { usePatients } from '@/lib/hooks/usePatients'
import { useAuthStore } from '@/store/authStore'

export default function NewAppointmentPage() {
  const t = useTranslations('apptNewUi')
  const router = useRouter()
  const searchParams = useSearchParams()
  const createAppointment = useCreateAppointment()
  const user = useAuthStore((state) => state.user)
  const { data: patients, isLoading: isLoadingPatients } = usePatients({ limit: 200 })

  const [formData, setFormData] = useState({
    patient_id: '',
    appointment_date: searchParams.get('date') || '',
    appointment_time: searchParams.get('time') || '',
    duration_minutes: 30,
    reason: '',
    notes: '',
  })

  const selectedPatient = useMemo(
    () => patients?.find((patient) => patient.id === formData.patient_id),
    [patients, formData.patient_id]
  )

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!user?.id) return

    await createAppointment.mutateAsync({
      patient_id: formData.patient_id,
      doctor_id: user.id,
      appointment_date: formData.appointment_date,
      appointment_time: formData.appointment_time,
      duration_minutes: formData.duration_minutes,
      reason: formData.reason || undefined,
      notes: formData.notes || undefined,
    })
    router.push('/appointments')
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/appointments">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            {t('back')}
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">{t('title')}</h1>
          <p className="text-muted-foreground">{t('subtitle')}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 border rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="patient_id">{t('patient')}</Label>
            <Select
              value={formData.patient_id}
              onValueChange={(value) => setFormData((prev) => ({ ...prev, patient_id: value }))}
              disabled={isLoadingPatients || !patients?.length}
            >
              <SelectTrigger id="patient_id">
                <SelectValue placeholder={t('selectPatient')} />
              </SelectTrigger>
              <SelectContent>
                {patients?.map((patient) => (
                  <SelectItem key={patient.id} value={patient.id}>
                    {patient.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedPatient ? (
              <p className="text-xs text-muted-foreground">
                {selectedPatient.phone
                  ? t('selectedWithPhone', { name: selectedPatient.full_name, phone: selectedPatient.phone })
                  : t('selected', { name: selectedPatient.full_name })}
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="doctor_name">{t('doctor')}</Label>
            <Input id="doctor_name" value={user?.full_name || ''} readOnly disabled />
            <p className="text-xs text-muted-foreground">{t('doctorHint')}</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="appointment_date">{t('date')}</Label>
            <Input
              id="appointment_date"
              type="date"
              value={formData.appointment_date}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, appointment_date: e.target.value }))
              }
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="appointment_time">{t('time')}</Label>
            <Input
              id="appointment_time"
              type="time"
              value={formData.appointment_time}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, appointment_time: e.target.value }))
              }
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="duration_minutes">{t('duration')}</Label>
            <Input
              id="duration_minutes"
              type="number"
              min={15}
              max={240}
              value={formData.duration_minutes}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  duration_minutes: Number(e.target.value || 30),
                }))
              }
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="reason">{t('reason')}</Label>
          <Input
            id="reason"
            value={formData.reason}
            onChange={(e) => setFormData((prev) => ({ ...prev, reason: e.target.value }))}
            placeholder={t('reasonPlaceholder')}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">{t('notes')}</Label>
          <Input
            id="notes"
            value={formData.notes}
            onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
            placeholder={t('notesPlaceholder')}
          />
        </div>

        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={createAppointment.isLoading || !user?.id || !formData.patient_id}
          >
            {createAppointment.isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                {t('creating')}
              </>
            ) : (
              t('submit')
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
