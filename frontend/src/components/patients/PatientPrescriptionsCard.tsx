'use client'

import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { FileText, Loader2, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { usePrescriptions } from '@/lib/hooks/usePrescriptions'
import { useCan } from '@/lib/auth/permissions'

/** The patient's prescriptions, newest first, with a button to write a new one (patient already chosen). */
export function PatientPrescriptionsCard({ patientId }: { patientId: string }) {
  const t = useTranslations('patientRxCardUi')
  const locale = useLocale()
  const { can } = useCan()
  const { data: prescriptions, isLoading } = usePrescriptions({ patient_id: patientId, limit: 20 })
  const date = (iso: string) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(iso))

  if (!can('prescriptions.read')) return null

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              {t('title')}
            </CardTitle>
            <CardDescription>{t('description')}</CardDescription>
          </div>
          {can('prescriptions.write') && (
            <Button asChild>
              <Link href={`/prescriptions/new?patient=${patientId}`}>
                <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                {t('new')}
              </Link>
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && <Loader2 className="h-5 w-5 animate-spin text-emerald-600" aria-hidden="true" />}
        {prescriptions && prescriptions.length === 0 && <p className="text-sm text-muted-foreground">{t('empty')}</p>}
        {prescriptions?.map((p) => (
          <Link key={p.id} href={`/prescriptions/${p.id}`} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 hover:bg-accent">
            <span>
              <span className="font-medium">{date(p.created_at)}</span>
              <span className="ml-2 text-sm text-muted-foreground">{p.diagnosis || t('noDiagnosis')}</span>
            </span>
            <Badge variant={p.status === 'issued' ? 'default' : 'secondary'}>{t(`status.${p.status}`)}</Badge>
          </Link>
        ))}
      </CardContent>
    </Card>
  )
}
