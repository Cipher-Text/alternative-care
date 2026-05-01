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

const twoFactorSchema = z.object({
  totp_code: z.string().length(6, 'Code must be 6 digits'),
})

type TwoFactorFormData = z.infer<typeof twoFactorSchema>

interface TwoFactorFormProps {
  email: string
  password: string
  onBack: () => void
}

export function TwoFactorForm({ email, password, onBack }: TwoFactorFormProps) {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFactorFormData>({
    resolver: zodResolver(twoFactorSchema),
  })

  const onSubmit = async (data: TwoFactorFormData) => {
    setLoading(true)
    try {
      const response = await authApi.loginWith2FA({
        email,
        password,
        totp_code: data.totp_code,
      })

      setAuth(response.user, response.access_token, response.refresh_token)
      toast.success('Login successful!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Invalid code')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Two-Factor Authentication</CardTitle>
        <CardDescription>
          Enter the 6-digit code from your authenticator app
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="totp_code">Authentication Code</Label>
            <Input
              id="totp_code"
              type="text"
              placeholder="000000"
              maxLength={6}
              {...register('totp_code')}
              disabled={loading}
              className="text-center text-2xl tracking-widest"
            />
            {errors.totp_code && (
              <p className="text-sm text-red-500">{errors.totp_code.message}</p>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={onBack}
              disabled={loading}
            >
              Back
            </Button>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
