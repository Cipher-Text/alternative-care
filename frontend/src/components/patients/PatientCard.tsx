'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { User, Phone, Calendar, MapPin } from 'lucide-react'
import type { Patient } from '@/types/patient'
import { formatPatientName, calculateAge, formatPhone, formatGender } from '@/lib/utils/format'

interface PatientCardProps {
  patient: Patient
}

export function PatientCard({ patient }: PatientCardProps) {
  const age = calculateAge(patient.date_of_birth)
  const fullName = formatPatientName(patient.first_name, patient.last_name)

  return (
    <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-indigo-500/10 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-200 dark:border-indigo-800 flex items-center justify-center">
              <User className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900 dark:text-white">{fullName}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{patient.patient_code}</p>
            </div>
          </div>
          <Badge
            variant="outline"
            className="bg-gray-100 dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300"
          >
            {formatGender(patient.gender)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Calendar className="h-4 w-4" />
          <span>{age} years old</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Phone className="h-4 w-4" />
          <span>{formatPhone(patient.phone)}</span>
        </div>
        {patient.address && (
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <MapPin className="h-4 w-4" />
            <span className="truncate">{patient.address}</span>
          </div>
        )}
        <div className="pt-2 border-t border-gray-200 dark:border-slate-700">
          <Link href={`/patients/${patient.id}`}>
            <Button
              variant="outline"
              className="w-full bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 hover:text-indigo-700 dark:hover:text-indigo-300 hover:border-indigo-300 dark:hover:border-indigo-700"
              size="sm"
            >
              View Details
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
