'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useHealthProfile } from '@/lib/hooks/useHealth'
import { useCodeLabel } from './useCodeLabel'

/** Warnings to read before prescribing: allergies, pregnancy, age, other medicines, long-term conditions.
 * Shown on the patient page and in the prescription builder. Renders nothing while loading or on error. */
export function SafetyBanner({ patientId, linkToPatient = false }: { patientId: string; linkToPatient?: boolean }) {
  const t = useTranslations('healthUi.banner')
  const { data: profile } = useHealthProfile(patientId)
  const flagLabel = useCodeLabel('flag')
  const conditionLabel = useCodeLabel('chronic')
  const allergyTypeLabel = useCodeLabel('allergyType')
  if (!profile) return null

  const warnings = profile.safety_flags.length > 0 || profile.chronic_conditions.length > 0
  if (!profile.exists && !warnings) {
    return linkToPatient ? (
      <p className="text-sm text-muted-foreground">
        {t('noProfile')}{' '}
        <Link href={`/patients/${patientId}`} className="underline">{t('open')}</Link>
      </p>
    ) : null
  }
  if (!warnings) return null

  return (
    <div role="alert" className="space-y-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
      <p className="flex items-center gap-2 font-semibold">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        {t('title')}
      </p>
      {profile.safety_flags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {profile.safety_flags.map((flag) => (
            <Badge key={flag} variant="outline" className="border-amber-500 bg-white text-amber-900 dark:bg-transparent dark:text-amber-100">
              {flagLabel(flag)}
            </Badge>
          ))}
        </div>
      )}
      {profile.allergies.length > 0 && (
        <p>
          <span className="font-medium">{t('allergies')}</span>{' '}
          {profile.allergies.map((a) => `${a.substance} (${allergyTypeLabel(a.type)})`).join(', ')}
        </p>
      )}
      {profile.chronic_conditions.length > 0 && (
        <p>
          <span className="font-medium">{t('conditions')}</span>{' '}
          {profile.chronic_conditions.map(conditionLabel).join(', ')}
        </p>
      )}
    </div>
  )
}
