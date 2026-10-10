'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface PendingApprovalNoticeProps {
  // 'submitted': just registered (email verification is still outstanding).
  // 'login': tried to log in before approval.
  variant: 'submitted' | 'login'
  email?: string
  onBack?: () => void
}

export function PendingApprovalNotice({ variant, email, onBack }: PendingApprovalNoticeProps) {
  const t = useTranslations('auth')
  const submitted = variant === 'submitted'

  const steps = [
    ...(submitted
      ? [t('pendingStepVerify', { email: email ? ` (${email})` : '' })]
      : []),
    t('pendingStepReview'),
    t('pendingStepApproved'),
  ]

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
          <Clock className="h-5 w-5" aria-hidden="true" />
        </div>
        <CardTitle className="text-2xl">
          {submitted ? t('pendingTitleSubmitted') : t('pendingTitleLogin')}
        </CardTitle>
        <CardDescription>
          {submitted ? t('pendingIntroSubmitted') : t('pendingIntroLogin')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-3 text-sm">
          {steps.map((step, index) => (
            <li key={step} className="flex items-start gap-3">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                {index + 1}
              </span>
              <span className="text-gray-700 dark:text-gray-300">{step}</span>
            </li>
          ))}
        </ol>
        <p className="text-xs text-gray-500 dark:text-gray-400">{t('pendingHelp')}</p>
        {onBack ? (
          <Button type="button" variant="outline" className="w-full" onClick={onBack}>
            {t('useAnotherAccount')}
          </Button>
        ) : (
          <Link href="/login" className="block text-center text-sm font-medium text-primary hover:underline">
            {t('backToLogin')}
          </Link>
        )}
      </CardContent>
    </Card>
  )
}
