'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { getErrorMessage } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

type ForgotPasswordFormData = {
  email: string
}

export function ForgotPasswordForm() {
  const t = useTranslations('auth')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  const schema = z.object({
    email: z.string().email({ message: t('invalidEmail') }),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setLoading(true)
    try {
      // Backend always returns the same generic message regardless of
      // whether the email is registered — don't branch UI on the response,
      // that's the enumeration protection. A thrown error here means the
      // request itself failed (network, rate limit), not that the account
      // doesn't exist, so it's shown as a real error, not treated as success.
      await authApi.forgotPassword(data)
      setSent(true)
    } catch (error) {
      toast.error(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">{t('checkYourEmail')}</CardTitle>
          <CardDescription>{t('resetLinkSentDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/login" className="text-sm font-medium text-primary hover:underline">
            {t('backToLogin')}
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">{t('forgotPasswordTitle')}</CardTitle>
        <CardDescription>{t('forgotPasswordDescription')}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">{t('email')}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t('emailPlaceholder')}
              {...register('email')}
              disabled={loading}
            />
            {errors.email && <p className="text-sm text-red-500">{errors.email.message}</p>}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? t('sendingResetLink') : t('sendResetLink')}
          </Button>

          <Link
            href="/login"
            className="block text-center text-sm font-medium text-primary hover:underline"
          >
            {t('backToLogin')}
          </Link>
        </form>
      </CardContent>
    </Card>
  )
}
