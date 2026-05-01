'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TwoFactorForm } from './TwoFactorForm'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginForm() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loading, setLoading] = useState(false)
  const [needs2FA, setNeeds2FA] = useState(false)
  const [credentials, setCredentials] = useState<LoginFormData | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true)
    try {
      const response = await authApi.login(data)

      if (response.user.two_factor_enabled) {
        // Show 2FA form
        setCredentials(data)
        setNeeds2FA(true)
        setLoading(false)
      } else {
        // Login successful
        setAuth(response.user, response.access_token, response.refresh_token)
        toast.success('Login successful!')
        router.push('/dashboard')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
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
        <CardTitle className="text-2xl">Login to AltCare</CardTitle>
        <CardDescription>
          Enter your email and password to access your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="doctor@clinic.com"
              {...register('email')}
              disabled={loading}
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              {...register('password')}
              disabled={loading}
            />
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
