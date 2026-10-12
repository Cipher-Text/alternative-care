'use client'

import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { AlertTriangle, CalendarClock, CalendarPlus, CheckCircle2, ClipboardList, Loader2, Receipt } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useTodayOverview } from '@/lib/hooks/useDashboard'
import { useCodeLabel } from '@/components/health/useCodeLabel'
import type { TodayOverview } from '@/types/dashboardToday'

/** The first thing a practitioner sees: today's list, then what needs action. */
export function TodayPanel() {
  const t = useTranslations('homeUi.today')
  const { data, isLoading, isError } = useTodayOverview()

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center" aria-busy="true">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
      </div>
    )
  }
  if (isError || !data) return null // the rest of the dashboard still works without it

  return (
    <section aria-labelledby="today-heading" className="space-y-4">
      <div>
        <h2 id="today-heading" className="text-xl font-semibold text-gray-900 dark:text-white">{t('title')}</h2>
        <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
      </div>
      <PlanNotice plan={data.plan} />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <ScheduleCard appointments={data.appointments} className="lg:col-span-3" />
        <AttentionCard data={data} className="lg:col-span-2" />
      </div>
    </section>
  )
}

function PlanNotice({ plan }: { plan: TodayOverview['plan'] }) {
  const t = useTranslations('homeUi.today')
  const ending = !plan.expired && plan.days_left !== null && plan.days_left <= 14
  if (!plan.expired && !ending) return null
  return (
    <div role="status" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
      <span className="flex items-center gap-2">
        <Receipt className="h-4 w-4 shrink-0" aria-hidden="true" />
        {plan.expired ? t('planExpired') : t('planEnding', { plan: plan.plan, days: plan.days_left ?? 0 })}
      </span>
      <Button asChild size="sm" variant="outline">
        <Link href="/billing">{t('renew')}</Link>
      </Button>
    </div>
  )
}

function ScheduleCard({ appointments, className }: { appointments: TodayOverview['appointments']; className?: string }) {
  const t = useTranslations('homeUi.today')
  const locale = useLocale()
  const timeLabel = (hhmmss: string) => {
    const [h, m] = hhmmss.split(':').map(Number)
    return new Intl.DateTimeFormat(locale, { hour: 'numeric', minute: '2-digit' }).format(new Date(2000, 0, 1, h, m))
  }
  const statusLabel = (s: string) => (t.has(`status.${s}`) ? t(`status.${s}`) : s)

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
        <CardTitle className="flex items-center gap-2 text-lg">
          <CalendarClock className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('scheduleTitle')}
        </CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/appointments">{t('viewAll')}</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {appointments.length === 0 ? (
          <div className="flex flex-col items-start gap-3 py-2">
            <p className="text-sm text-muted-foreground">{t('noAppointments')}</p>
            <Button asChild variant="outline" size="sm">
              <Link href="/appointments/new"><CalendarPlus className="mr-2 h-4 w-4" aria-hidden="true" />{t('scheduleOne')}</Link>
            </Button>
          </div>
        ) : (
          <ul className="divide-y">
            {appointments.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
                <span className="w-20 shrink-0 text-sm font-semibold tabular-nums">{timeLabel(a.appointment_time)}</span>
                <div className="min-w-0 flex-1">
                  <Link href={`/patients/${a.patient_id}`} className="font-medium hover:underline">{a.patient_name}</Link>
                  <p className="truncate text-sm text-muted-foreground">
                    {[a.reason, t('minutes', { count: a.duration_minutes })].filter(Boolean).join(' · ')}
                  </p>
                </div>
                <Badge variant="outline">{statusLabel(a.status)}</Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function AttentionCard({ data, className }: { data: TodayOverview; className?: string }) {
  const t = useTranslations('homeUi.today')
  const flagLabel = useCodeLabel('redFlag')
  const { requests_waiting: requests, alerts, follow_ups_due: followUps } = data
  const nothing = requests === 0 && alerts.length === 0 && followUps.length === 0

  const dueLabel = (days: number) => (days > 0 ? t('overdue', { days }) : days === 0 ? t('dueToday') : t('dueIn', { days: -days }))

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">{t('attentionTitle')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {nothing && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
            {t('allClear')}
          </p>
        )}

        {requests > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-emerald-50 p-3 text-sm dark:bg-emerald-950/40">
            <span className="flex items-center gap-2 font-medium">
              <ClipboardList className="h-4 w-4 text-emerald-600" aria-hidden="true" />
              {t('requestsWaiting', { count: requests })}
            </span>
            <Button asChild size="sm" variant="outline">
              <Link href="/appointment-requests">{t('openRequests')}</Link>
            </Button>
          </div>
        )}

        {alerts.length > 0 && (
          <div className="space-y-2">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-red-700 dark:text-red-300">
              <AlertTriangle className="h-4 w-4" aria-hidden="true" />
              {t('alertsTitle')}
            </h3>
            <ul className="space-y-2">
              {alerts.map((a) => (
                <li key={a.patient_id} className="text-sm">
                  <Link href={`/patients/${a.patient_id}`} className="font-medium hover:underline">{a.patient_name}</Link>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {a.referral_urgency && (a.referral_urgency === 'urgent' || a.referral_urgency === 'emergency') && (
                      <Badge className="bg-red-600 text-white hover:bg-red-600">{t(`referral.${a.referral_urgency}`)}</Badge>
                    )}
                    {a.red_flags.map((f) => (
                      <Badge key={f} className="bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-200">{flagLabel(f)}</Badge>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {followUps.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold">{t('followUpsTitle')}</h3>
            <ul className="space-y-2">
              {followUps.map((f) => (
                <li key={f.patient_id} className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
                  <span className="min-w-0">
                    <Link href={`/patients/${f.patient_id}`} className="font-medium hover:underline">{f.patient_name}</Link>
                    {f.follow_up_notes && <span className="block truncate text-muted-foreground">{f.follow_up_notes}</span>}
                  </span>
                  <span className={f.days_overdue > 0 ? 'font-medium text-amber-700 dark:text-amber-300' : 'text-muted-foreground'}>{dueLabel(f.days_overdue)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
