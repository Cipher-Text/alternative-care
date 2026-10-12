'use client'

import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { getErrorMessage } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PendingApprovalNotice } from '@/components/auth/PendingApprovalNotice'
import type { MedicalSystem, RequestedPlan } from '@/types/auth'

type RegisterFormData = {
  full_name: string
  email: string
  phone?: string
  password: string
  confirm_password: string
  specializations: MedicalSystem[]
}

// Mirrors backend `_validate_password_strength`: 8+ chars, upper + lower + number.
const PASSWORD_COMPLEXITY = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/

const SYSTEMS: Array<{ value: MedicalSystem; labelKey: string }> = [
  { value: 'homeopathy', labelKey: 'systemHomeopathy' },
  { value: 'ayurveda', labelKey: 'systemAyurveda' },
  { value: 'unani', labelKey: 'systemUnani' },
  { value: 'herbal', labelKey: 'systemHerbal' },
]

const PLANS: RequestedPlan[] = ['free', 'plus', 'pro', 'enterprise']

export function RegisterForm({ plan }: { plan?: string | null }) {
  const t = useTranslations('auth')
  const locale = useLocale()
  const [loading, setLoading] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null)

  const requestedPlan = PLANS.find((p) => p === plan) ?? null

  const schema = z
    .object({
      full_name: z.string().trim().min(2, { message: t('nameTooShort') }),
      email: z.string().email({ message: t('invalidEmail') }),
      phone: z.string().optional(),
      password: z
        .string()
        .min(8, { message: t('passwordMinLength8') })
        .regex(PASSWORD_COMPLEXITY, { message: t('passwordComplexity') }),
      confirm_password: z.string(),
      specializations: z
        .array(z.enum(['homeopathy', 'ayurveda', 'unani', 'herbal']))
        .min(1, { message: t('selectSystemError') }),
    })
    .refine((data) => data.password === data.confirm_password, {
      message: t('passwordsDoNotMatch'),
      path: ['confirm_password'],
    })

  const {
    register,
    handleSubmit,
    control,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(schema),
    defaultValues: { specializations: ['homeopathy'] },
  })

  const selected = new Set(useWatch({ control, name: 'specializations' }))

  const toggleSystem = (system: MedicalSystem) => {
    const current = getValues('specializations')
    const next = current.includes(system)
      ? current.filter((item) => item !== system)
      : [...current, system]
    setValue('specializations', next, { shouldValidate: true })
  }

  const onSubmit = async (data: RegisterFormData) => {
    setLoading(true)
    try {
      await authApi.register({
        email: data.email.trim(),
        password: data.password,
        full_name: data.full_name.trim(),
        phone: data.phone?.trim() || null,
        language: locale === 'bn' ? 'bn' : 'en',
        specializations: data.specializations,
        requested_plan: requestedPlan,
      })
      setSubmittedEmail(data.email.trim())
    } catch (error) {
      toast.error(getErrorMessage(error, t('registrationFailed')))
    } finally {
      setLoading(false)
    }
  }

  if (submittedEmail) {
    return <PendingApprovalNotice variant="submitted" email={submittedEmail} />
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">{t('createAccountTitle')}</CardTitle>
        <CardDescription>{t('createAccountDescription')}</CardDescription>
        {requestedPlan && requestedPlan !== 'free' && (
          <p className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300">
            {t('planInterest', { plan: requestedPlan.charAt(0).toUpperCase() + requestedPlan.slice(1) })}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="full_name">{t('fullName')}</Label>
            <Input
              id="full_name"
              autoComplete="name"
              placeholder={t('fullNamePlaceholder')}
              {...register('full_name')}
              disabled={loading}
            />
            {errors.full_name && <p className="text-sm text-red-500">{errors.full_name.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">{t('email')}</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder={t('emailPlaceholder')}
              {...register('email')}
              disabled={loading}
            />
            {errors.email && <p className="text-sm text-red-500">{errors.email.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">{t('phone')}</Label>
            <Input
              id="phone"
              type="tel"
              autoComplete="tel"
              placeholder="01700000000"
              {...register('phone')}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label>{t('medicalSystems')}</Label>
            <div className="grid grid-cols-2 gap-2">
              {SYSTEMS.map((system) => (
                <Button
                  key={system.value}
                  type="button"
                  variant={selected.has(system.value) ? 'default' : 'outline'}
                  aria-pressed={selected.has(system.value)}
                  onClick={() => toggleSystem(system.value)}
                  disabled={loading}
                >
                  {t(system.labelKey)}
                </Button>
              ))}
            </div>
            {errors.specializations && (
              <p className="text-sm text-red-500">{errors.specializations.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">{t('password')}</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              {...register('password')}
              disabled={loading}
            />
            {errors.password && <p className="text-sm text-red-500">{errors.password.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">{t('confirmPassword')}</Label>
            <Input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              {...register('confirm_password')}
              disabled={loading}
            />
            {errors.confirm_password && (
              <p className="text-sm text-red-500">{errors.confirm_password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? t('creatingAccount') : t('createAccount')}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            {t('consentPrefix')}{' '}
            <Link href="/terms" className="underline" target="_blank">
              {t('consentTerms')}
            </Link>{' '}
            {t('consentAnd')}{' '}
            <Link href="/privacy" className="underline" target="_blank">
              {t('consentPrivacy')}
            </Link>
          </p>

          <p className="text-center text-xs text-gray-500 dark:text-gray-400">{t('googleHint')}</p>
          <p className="text-center text-sm">
            {t('haveAccount')}{' '}
            <Link href="/login" className="font-medium text-primary hover:underline">
              {t('login')}
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  )
}
