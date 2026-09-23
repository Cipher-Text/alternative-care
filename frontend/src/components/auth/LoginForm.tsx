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
import { GoogleSignInButton } from './GoogleSignInButton'
import { getErrorMessage } from '@/types/api'
import { stashGoogleIdToken } from '@/lib/auth/google-session'

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

type Pending2FA =
  | { kind: 'password'; email: string; password: string }
  | { kind: 'google'; idToken: string }

export function LoginForm() {
  const router = useRouter()
  const t = useTranslations('auth')
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loading, setLoading] = useState(false)
  const [pending2FA, setPending2FA] = useState<Pending2FA | null>(null)

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
        setPending2FA({ kind: 'password', email: data.email, password: data.password })
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

  const handleGoogleCredential = async (idToken: string) => {
    setLoading(true)
    try {
      const response = await authApi.googleLogin({ id_token: idToken })

      if (response.needs_registration) {
        stashGoogleIdToken(idToken)
        const params = new URLSearchParams({
          email: response.email ?? '',
          name: response.full_name ?? '',
        })
        router.push(`/register/google?${params.toString()}`)
        return
      }

      if (response.requires_2fa || !response.user || !response.tokens) {
        setPending2FA({ kind: 'google', idToken })
        setLoading(false)
        return
      }

      setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token)
      toast.success(t('loginSuccess'))
      router.push(getPostLoginPath(response.user))
    } catch (error) {
      toast.error(getErrorMessage(error, t('loginFailed')))
      setLoading(false)
    }
  }

  if (pending2FA) {
    return (
      <TwoFactorForm
        onBack={() => setPending2FA(null)}
        onSubmit={async (totpCode) => {
          const response =
            pending2FA.kind === 'password'
              ? await authApi.loginWith2FA({
                  email: pending2FA.email,
                  password: pending2FA.password,
                  totp_code: totpCode,
                })
              : await authApi.googleLogin({ id_token: pending2FA.idToken, totp_code: totpCode })

          if (!response.user || !response.tokens) {
            throw new Error(t('loginFailed'))
          }

          setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token)
          toast.success(t('loginSuccess'))
          router.push(getPostLoginPath(response.user))
        }}
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

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">{t('orContinueWith')}</span>
            </div>
          </div>

          <GoogleSignInButton onCredential={handleGoogleCredential} />

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
