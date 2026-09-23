'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { getErrorMessage } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

type ResetPasswordFormData = {
  new_password: string
  confirm_password: string
}

// Mirrors backend `_validate_password_strength`: 8+ chars, upper + lower + number.
const PASSWORD_COMPLEXITY = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/

export function ResetPasswordForm({ token }: { token: string | null }) {
  const t = useTranslations('auth')
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  const schema = z
    .object({
      new_password: z
        .string()
        .min(8, { message: t('passwordMinLength8') })
        .regex(PASSWORD_COMPLEXITY, { message: t('passwordComplexity') }),
      confirm_password: z.string(),
    })
    .refine((data) => data.new_password === data.confirm_password, {
      message: t('passwordsDoNotMatch'),
      path: ['confirm_password'],
    })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) return
    setLoading(true)
    try {
      await authApi.resetPassword({ token, new_password: data.new_password })
      toast.success(t('resetSuccess'))
      router.push('/login')
    } catch (error) {
      toast.error(getErrorMessage(error, t('resetFailed')))
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">{t('resetPasswordTitle')}</CardTitle>
          <CardDescription>{t('missingResetToken')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/forgot-password" className="text-sm font-medium text-primary hover:underline">
            {t('requestNewLink')}
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">{t('resetPasswordTitle')}</CardTitle>
        <CardDescription>{t('resetPasswordDescription')}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new_password">{t('newPassword')}</Label>
            <Input
              id="new_password"
              type="password"
              placeholder={t('passwordPlaceholder')}
              {...register('new_password')}
              disabled={loading}
            />
            {errors.new_password && (
              <p className="text-sm text-red-500">{errors.new_password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">{t('confirmPassword')}</Label>
            <Input
              id="confirm_password"
              type="password"
              placeholder={t('passwordPlaceholder')}
              {...register('confirm_password')}
              disabled={loading}
            />
            {errors.confirm_password && (
              <p className="text-sm text-red-500">{errors.confirm_password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? t('resettingPassword') : t('resetPassword')}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
