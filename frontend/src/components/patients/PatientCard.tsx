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
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
              <User className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">{fullName}</h3>
              <p className="text-sm text-muted-foreground">{patient.patient_code}</p>
            </div>
          </div>
          <Badge variant="outline">{formatGender(patient.gender)}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Calendar className="h-4 w-4" />
          <span>{age} years old</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Phone className="h-4 w-4" />
          <span>{formatPhone(patient.phone)}</span>
        </div>
        {patient.address && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <MapPin className="h-4 w-4" />
            <span className="truncate">{patient.address}</span>
          </div>
        )}
        <div className="pt-2">
          <Link href={`/patients/${patient.id}`}>
            <Button variant="outline" className="w-full" size="sm">
              View Details
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
