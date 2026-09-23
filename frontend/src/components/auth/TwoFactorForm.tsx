'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'react-hot-toast'
import { getErrorMessage } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const twoFactorSchema = z.object({
  totp_code: z.string().length(6, 'Code must be 6 digits'),
})

type TwoFactorFormData = z.infer<typeof twoFactorSchema>

interface TwoFactorFormProps {
  /**
   * Complete the login with this TOTP code — e.g. call authApi.loginWith2FA
   * or authApi.googleLogin(..., totp_code), then set auth state and
   * navigate on success. Throw to show an error and stay on this form.
   */
  onSubmit: (totpCode: string) => Promise<void>
  onBack: () => void
}

export function TwoFactorForm({ onSubmit, onBack }: TwoFactorFormProps) {
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFactorFormData>({
    resolver: zodResolver(twoFactorSchema),
  })

  const handleFormSubmit = async (data: TwoFactorFormData) => {
    setLoading(true)
    try {
      await onSubmit(data.totp_code)
    } catch (error) {
      toast.error(getErrorMessage(error, 'Invalid code'))
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
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
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
