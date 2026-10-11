'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { User, Phone, Calendar, MapPin } from 'lucide-react'
import type { PatientListItem } from '@/types/patient'
import { calculateAge, formatPhone } from '@/lib/utils/format'

interface PatientCardProps {
  patient: PatientListItem
}

export function PatientCard({ patient }: PatientCardProps) {
  const t = useTranslations('patientCardUi')
  const age = calculateAge(patient.date_of_birth)
  const fullName = patient.full_name?.trim() || t('unknownPatient')
  const gender = patient.gender
    ? t.has(`gender.${patient.gender.toLowerCase()}`)
      ? t(`gender.${patient.gender.toLowerCase()}`)
      : patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1).toLowerCase()
    : t('notSpecified')

  return (
    <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700 hover:shadow-md dark:hover:shadow-emerald-500/10 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-900/50 border-2 border-emerald-200 dark:border-emerald-800 flex items-center justify-center">
              <User className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900 dark:text-white">{fullName}</h3>
            </div>
          </div>
          <Badge
            variant="outline"
            className="bg-gray-100 dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300"
          >
            {gender}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Calendar className="h-4 w-4" />
          <span>{age !== null ? t('ageOld', { age }) : t('ageUnknown')}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Phone className="h-4 w-4" />
          <span>{formatPhone(patient.phone)}</span>
        </div>
        {patient.next_visit_date && (
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <MapPin className="h-4 w-4" />
            <span>{t('nextVisit', { date: patient.next_visit_date })}</span>
          </div>
        )}
        <div className="pt-2 border-t border-gray-200 dark:border-slate-700">
          <Link href={`/patients/${patient.id}`}>
            <Button
              variant="outline"
              className="w-full bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 hover:text-emerald-700 dark:hover:text-emerald-300 hover:border-emerald-300 dark:hover:border-emerald-700"
              size="sm"
            >
              {t('viewDetails')}
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
