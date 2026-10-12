'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useCreatePatient } from '@/lib/hooks/usePatients'
import { useLinkIdentity } from '@/lib/hooks/useIdentity'
import { PatientForm, type PatientFormPrefill } from '@/components/patients/PatientForm'
import { PhoneVerificationDialog, type PrefillResult } from '@/components/identity/PhoneVerificationDialog'
import { identityError, newProfileFromPatient, toLocalPhone } from '@/components/identity/identityUtils'
import { errorMessage } from '@/lib/apiErrors'
import { Button } from '@/components/ui/button'
import { ArrowLeft, ShieldCheck } from 'lucide-react'
import { toast } from 'react-hot-toast'
import Link from 'next/link'
import type { PatientCreateRequest } from '@/types/patient'

const GENDERS = ['male', 'female', 'other'] as const

export default function NewPatientPage() {
  const router = useRouter()
  const t = useTranslations('patientNewUi')
  const tu = useTranslations('patientsUi')
  const ti = useTranslations('identityUi')
  const createPatient = useCreatePatient()
  const linkIdentity = useLinkIdentity()

  const [verifyOpen, setVerifyOpen] = useState(false)
  const [verified, setVerified] = useState<PrefillResult | null>(null)
  const [prefill, setPrefill] = useState<PatientFormPrefill | undefined>()

  const handlePrefill = (result: PrefillResult) => {
    setVerified(result)
    const d = result.details
    if (!d) {
      if (result.phone) setPrefill({ version: Date.now(), values: { phone: toLocalPhone(result.phone) } })
      return
    }
    const gender = GENDERS.find((g) => g === d.gender)
    setPrefill({
      version: Date.now(),
      values: {
        full_name: d.display_name,
        date_of_birth: d.date_of_birth ?? undefined,
        gender,
        phone: d.phone ? toLocalPhone(d.phone) : undefined,
        division_id: d.division_id ?? undefined,
        district_id: d.district_id ?? undefined,
        upazila_id: d.upazila_id ?? undefined,
      },
    })
  }

  const handleSubmit = async (data: PatientCreateRequest) => {
    let patient
    try {
      patient = await createPatient.mutateAsync(data)
    } catch {
      // error is handled by onError in useCreatePatient (shows toast)
      return
    }

    if (verified) {
      // The patient record exists either way; a failed link never undoes the save.
      try {
        await linkIdentity.mutateAsync(
          verified.details
            ? { verification_token: verified.token, patient_id: patient.id, profile_id: verified.details.profile_id }
            : {
                verification_token: verified.token,
                patient_id: patient.id,
                new_profile: newProfileFromPatient(patient, verified.relationship ?? 'self', verified.approxBirthYear),
              }
        )
        toast.success(ti('prefill.linked'))
      } catch (err) {
        const info = identityError(err)
        const reason =
          info.code === 'invalid_verification' ? ti('errors.verificationExpired') : errorMessage(err, ti('errors.generic'))
        toast.error(ti('prefill.linkFailed', { reason }), { duration: 10000 })
        router.push(`/patients/${patient.id}`)
        return
      }
    }
    router.push('/patients')
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

      {/* Optional phone verification (never required to register a patient) */}
      <div className="flex flex-wrap items-center gap-3 rounded-md border border-dashed p-3">
        {verified ? (
          <p role="status" className="flex items-center gap-2 text-sm text-emerald-800 dark:text-emerald-300">
            <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            <span>
              {ti('prefill.verifiedNote')}
              {verified.approxBirthYear ? ` ${ti('prefill.approxYear', { year: verified.approxBirthYear })}` : ''}
            </span>
          </p>
        ) : (
          <>
            <Button type="button" variant="outline" size="sm" onClick={() => setVerifyOpen(true)}>
              <ShieldCheck className="mr-2 h-4 w-4" aria-hidden="true" />
              {ti('prefill.button')}
            </Button>
            <p className="text-xs text-muted-foreground">{ti('prefill.hint')}</p>
          </>
        )}
      </div>

      {/* Form */}
      <PatientForm onSubmit={handleSubmit} isSubmitting={createPatient.isLoading || linkIdentity.isLoading} prefill={prefill} />

      <PhoneVerificationDialog
        mode="prefill"
        open={verifyOpen}
        onClose={() => setVerifyOpen(false)}
        onPrefill={handlePrefill}
      />
    </div>
  )
}
