'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { parseISO } from 'date-fns'
import { useDateFormat } from '@/lib/i18n/date'
import Link from 'next/link'
import { usePatient, useDeletePatient, usePatientTags, usePatientDiagnoses } from '@/lib/hooks/usePatients'
import { useCan } from '@/lib/auth/permissions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  Edit,
  Trash2,
  User,
  Phone,
  Mail,
  Calendar,
  MapPin,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { PatientIdentityCard } from '@/components/identity/PatientIdentityCard'
import { SafetyBanner } from '@/components/health/SafetyBanner'
import { HealthProfileCard } from '@/components/health/HealthProfileCard'
import { VisitsCard } from '@/components/health/VisitsCard'
import { calculateAge, formatPhone } from '@/lib/utils/format'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export default function PatientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const t = useTranslations('patientDetailUi')
  const tu = useTranslations('patientsUi')
  const { fmt } = useDateFormat()
  const formatDate = (d: string) => fmt(parseISO(d), 'MMM dd, yyyy')
  const can = useCan()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data: patient, isLoading, error } = usePatient(id)
  const { data: tags } = usePatientTags(id)
  const { data: diagnoses } = usePatientDiagnoses(id)
  const deletePatient = useDeletePatient()

  const handleDelete = async () => {
    await deletePatient.mutateAsync(id)
    setShowDeleteDialog(false)
    router.push('/patients')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">{t('notFoundTitle')}</h2>
        <p className="text-muted-foreground mb-4">
          {t('notFoundBody')}
        </p>
        <Link href="/patients">
          <Button>{t('backToPatients')}</Button>
        </Link>
      </div>
    )
  }

  const age = calculateAge(patient.date_of_birth)
  const fullName = patient.full_name?.trim() || tu('unknownPatient')
  const genderText = patient.gender
    ? tu.has(`gender.${patient.gender.toLowerCase()}`)
      ? tu(`gender.${patient.gender.toLowerCase()}`)
      : patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1).toLowerCase()
    : tu('notSpecified')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/patients" aria-label={tu('back')}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{fullName}</h1>
            <p className="text-muted-foreground">{patient.is_active ? t('active') : t('inactive')}</p>
          </div>
        </div>
        {can.writeClinical && (
        <div className="flex flex-wrap gap-2">
          <Link href={`/patients/${id}/edit`}>
            <Button variant="outline">
              <Edit className="mr-2 h-4 w-4" />
              {t('edit')}
            </Button>
          </Link>
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            {t('delete')}
          </Button>
        </div>
        )}
      </div>

      {/* Patient Profile */}
      <SafetyBanner patientId={id} />

      <Card>
        <CardHeader>
          <CardTitle>{t('information')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">{t('name')}</p>
                <p className="font-medium">{fullName}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">{t('age')}</p>
                <p className="font-medium">
                  {age !== null ? t('ageYears', { age }) : t('unknown')}
                  {patient.date_of_birth ? ` (${formatDate(patient.date_of_birth)})` : ''}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">{t('gender')}</p>
                <Badge variant="outline">{genderText}</Badge>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Phone className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">{t('phone')}</p>
                <p className="font-medium">{formatPhone(patient.phone)}</p>
              </div>
            </div>

            {patient.email && (
              <div className="flex items-start gap-3">
                <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">{t('email')}</p>
                  <p className="font-medium">{patient.email}</p>
                </div>
              </div>
            )}

            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">{t('bloodGroup')}</p>
                <p className="font-medium">{patient.blood_group ? patient.blood_group.toUpperCase() : tu('notSpecified')}</p>
              </div>
            </div>

            {patient.address && (
              <div className="flex items-start gap-3 md:col-span-2">
                <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">{t('address')}</p>
                  <p className="font-medium">{patient.address}</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <PatientIdentityCard patient={patient} />

      <HealthProfileCard patientId={id} canEdit={can.writeClinical} />

      <VisitsCard patientId={id} canEdit={can.writeClinical} />

      {/* Tags */}
      {tags && tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('tags')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Badge key={tag.id} variant="secondary">
                  {tag.tag_value}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Diagnoses */}
      {diagnoses && diagnoses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('diagnosesHistory')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {diagnoses.map((diagnosis) => (
                <div
                  key={diagnosis.id}
                  className="border-l-4 border-emerald-500 pl-4 py-2"
                >
                  <p className="font-medium">{diagnosis.description}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(diagnosis.diagnosed_at)}
                  </p>
                  {diagnosis.icd_code && (
                    <p className="text-sm mt-1 text-muted-foreground">{t('icd', { code: diagnosis.icd_code })}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('deleteTitle')}</DialogTitle>
            <DialogDescription>
              {t('deleteConfirm', { name: fullName })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deletePatient.isLoading}
            >
              {t('cancel')}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deletePatient.isLoading}
            >
              {deletePatient.isLoading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {t('delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
