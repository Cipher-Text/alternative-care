'use client'

import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { getErrorMessage } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { MedicalSystem } from '@/types/auth'

const MEDICAL_SYSTEMS: Array<{ value: MedicalSystem; label: string }> = [
  { value: 'homeopathy', label: 'Homeopathy' },
  { value: 'ayurveda', label: 'Ayurveda' },
  { value: 'unani', label: 'Unani' },
  { value: 'herbal', label: 'Herbal' },
]

const schema = z.object({
  phone: z.string().optional(),
  clinic_name: z.string().optional(),
  clinic_address: z.string().optional(),
  license_number: z.string().optional(),
  specializations: z.array(z.enum(['homeopathy', 'ayurveda', 'unani', 'herbal'])).min(1, {
    message: 'Select at least one medical system',
  }),
})

type GoogleRegisterFormData = z.infer<typeof schema>

interface GoogleRegisterFormProps {
  idToken: string
  email: string
  fullName: string
  language: 'en' | 'bn'
}

export function GoogleRegisterForm({ idToken, email, fullName, language }: GoogleRegisterFormProps) {
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    control,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<GoogleRegisterFormData>({
    resolver: zodResolver(schema),
    defaultValues: { specializations: ['homeopathy'] },
  })

  const watchedSpecializations = useWatch({ control, name: 'specializations' })
  const selectedSystems = new Set(watchedSpecializations)

  const toggleSystem = (system: MedicalSystem) => {
    const current = getValues('specializations')
    const next = current.includes(system)
      ? current.filter((item) => item !== system)
      : [...current, system]
    setValue('specializations', next, { shouldValidate: true })
  }

  const onSubmit = async (data: GoogleRegisterFormData) => {
    setLoading(true)
    try {
      const response = await authApi.googleRegister({
        id_token: idToken,
        language,
        phone: data.phone?.trim() || null,
        clinic_name: data.clinic_name?.trim() || null,
        clinic_address: data.clinic_address?.trim() || null,
        license_number: data.license_number?.trim() || null,
        specializations: data.specializations,
      })
      setSubmitted(response.message)
    } catch (error) {
      toast.error(getErrorMessage(error, 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Registration submitted</CardTitle>
          <CardDescription>{submitted}</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/login" className="text-sm font-medium text-primary hover:underline">
            Back to login
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Complete your registration</CardTitle>
        <CardDescription>
          Signing up as <span className="font-medium">{fullName}</span> ({email}). A few clinic
          details, then your account goes to admin for approval.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input id="phone" placeholder="01700000000" {...register('phone')} disabled={loading} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="clinic_name">Clinic Name</Label>
            <Input
              id="clinic_name"
              placeholder="Example Clinic"
              {...register('clinic_name')}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="clinic_address">Clinic Address</Label>
            <Textarea
              id="clinic_address"
              placeholder="Clinic address"
              rows={2}
              {...register('clinic_address')}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="license_number">License Number</Label>
            <Input
              id="license_number"
              placeholder="BMDC-123"
              {...register('license_number')}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label>Medical Systems *</Label>
            <div className="grid grid-cols-2 gap-2">
              {MEDICAL_SYSTEMS.map((system) => (
                <Button
                  key={system.value}
                  type="button"
                  variant={selectedSystems.has(system.value) ? 'default' : 'outline'}
                  onClick={() => toggleSystem(system.value)}
                  disabled={loading}
                  className="justify-center"
                >
                  {system.label}
                </Button>
              ))}
            </div>
            {errors.specializations && (
              <p className="text-sm text-red-500">{errors.specializations.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Submitting...' : 'Complete Registration'}
          </Button>

          <Link
            href="/login"
            className="block text-center text-sm font-medium text-primary hover:underline"
          >
            Back to login
          </Link>
        </form>
      </CardContent>
    </Card>
  )
}
