'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { CheckCircle2, Circle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface OnboardingChecklistProps {
  totalPatients: number
  totalAppointments: number
  totalPrescriptions: number
}

/** First-run guide for a clinic with no data yet; disappears once all three steps are done. */
export function OnboardingChecklist({
  totalPatients,
  totalAppointments,
  totalPrescriptions,
}: OnboardingChecklistProps) {
  const t = useTranslations('onboardingUi')
  const steps = [
    { key: 'stepPatient', href: '/patients/new', done: totalPatients > 0 },
    { key: 'stepAppointment', href: '/appointments/new', done: totalAppointments > 0 },
    { key: 'stepPrescription', href: '/prescriptions/new', done: totalPrescriptions > 0 },
  ] as const
  const doneCount = steps.filter((s) => s.done).length
  if (doneCount === steps.length) return null

  return (
    <Card className="border-emerald-200 dark:border-emerald-900">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{t('title')}</CardTitle>
        <CardDescription>
          {t('subtitle')} · {t('progress', { done: doneCount, total: steps.length })}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {steps.map((step) => (
            <li key={step.key} className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-2 text-sm">
                {step.done ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden="true" />
                ) : (
                  <Circle className="h-5 w-5 text-gray-400" aria-hidden="true" />
                )}
                <span className={step.done ? 'text-muted-foreground line-through' : ''}>
                  {t(step.key)}
                </span>
              </span>
              {step.done ? (
                <span className="text-xs text-muted-foreground">{t('done')}</span>
              ) : (
                <Button asChild size="sm" variant="outline">
                  <Link href={step.href}>{t('start')}</Link>
                </Button>
              )}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
