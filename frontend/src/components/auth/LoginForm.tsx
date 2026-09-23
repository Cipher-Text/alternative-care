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
import { getPostLoginPath } from '@/lib/auth/redirects'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TwoFactorForm } from './TwoFactorForm'
import { getErrorMessage } from '@/types/api'

type LoginFormData = {
  email: string
  password: string
}

// Dev quick users - only loaded in development mode
// SECURITY: Never include credentials in production builds
const getDevQuickUsers = (): Array<{ label: string; email: string; password: string }> => {
  if (process.env.NODE_ENV === 'production') {
    return []
  }

  // Load from environment or use defaults (dev only)
  const devUsers = process.env.NEXT_PUBLIC_DEV_USERS
  if (devUsers) {
    try {
      return JSON.parse(devUsers)
    } catch {
      console.warn('Failed to parse NEXT_PUBLIC_DEV_USERS')
    }
  }

  // Fallback dev credentials (only in development)
  return [
    { label: 'Admin', email: 'admin@altcare.com', password: 'Admin@1234' },
    { label: 'Operator', email: 'operator@altcare.com', password: 'Operator@1234' },
    { label: 'Dr. Rahman', email: 'dr.rahman@example.com', password: 'Test@1234' },
    { label: 'Receptionist', email: 'receptionist.dhanmondi@example.com', password: 'Test@1234' },
    { label: 'Dr. Karim', email: 'dr.karim@example.com', password: 'Test@1234' },
    { label: 'Dr. Ahmed', email: 'dr.ahmed@example.com', password: 'Test@1234' },
  ]
}

const DEV_QUICK_USERS = getDevQuickUsers()

export function LoginForm() {
  const router = useRouter()
  const t = useTranslations('auth')
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loading, setLoading] = useState(false)
  const [needs2FA, setNeeds2FA] = useState(false)
  const [credentials, setCredentials] = useState<LoginFormData | null>(null)

  const loginSchema = z.object({
    email: z.string().email({ message: t('invalidEmail') }),
    password: z.string().min(6, t('passwordMinLength')),
  })

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true)
    try {
      const response = await authApi.login(data)

      if (response.requires_2fa || !response.user || !response.tokens) {
        // Show 2FA form
        setCredentials(data)
        setNeeds2FA(true)
        setLoading(false)
      } else {
        // Login successful
        setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token)
        toast.success(t('loginSuccess'))
        router.push(getPostLoginPath(response.user))
      }
    } catch (error) {
      toast.error(getErrorMessage(error, t('loginFailed')))
      setLoading(false)
    }
  }

  if (needs2FA && credentials) {
    return (
      <TwoFactorForm
        email={credentials.email}
        password={credentials.password}
        onBack={() => setNeeds2FA(false)}
      />
    )
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">{t('loginTitle')}</CardTitle>
        <CardDescription>
          {t('loginDescription')}
        </CardDescription>
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
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">{t('password')}</Label>
            <Input
              id="password"
              type="password"
              placeholder={t('passwordPlaceholder')}
              {...register('password')}
              disabled={loading}
            />
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password.message}</p>
            )}
            <Link
              href="/forgot-password"
              className="block text-right text-sm font-medium text-primary hover:underline"
            >
              {t('forgotPassword')}
            </Link>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? t('loggingIn') : t('login')}
          </Button>

          {process.env.NODE_ENV !== 'production' && (
            <div className="space-y-2 border-t pt-4">
              <p className="text-xs font-medium text-muted-foreground">Dev quick users</p>
              <div className="grid grid-cols-1 gap-2">
                {DEV_QUICK_USERS.map((user) => (
                  <button
                    key={user.email}
                    type="button"
                    className="rounded-md border px-3 py-2 text-left text-xs hover:bg-muted"
                    onClick={() => {
                      setValue('email', user.email, { shouldValidate: true })
                      setValue('password', user.password, { shouldValidate: true })
                    }}
                    disabled={loading}
                  >
                    {user.label}: {user.email}
                  </button>
                ))}
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
