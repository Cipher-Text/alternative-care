'use client'

import { useSearchParams } from 'next/navigation'
import { VerifyEmailStatus } from '@/components/auth/VerifyEmailStatus'

export default function VerifyEmailPage() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  return <VerifyEmailStatus token={token} />
}
