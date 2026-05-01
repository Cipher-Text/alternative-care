'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { usePatient, useDeletePatient, usePatientTags, usePatientDiagnoses } from '@/lib/hooks/usePatients'
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
import {
  formatPatientName,
  calculateAge,
  formatPhone,
  formatGender,
  formatDate,
  formatBloodGroup,
} from '@/lib/utils/format'
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
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Patient Not Found</h2>
        <p className="text-muted-foreground mb-4">
          The patient you're looking for doesn't exist or has been removed.
        </p>
        <Link href="/patients">
          <Button>Back to Patients</Button>
        </Link>
      </div>
    )
  }

  const age = calculateAge(patient.date_of_birth)
  const fullName = formatPatientName(patient.first_name, patient.last_name)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/patients">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">{fullName}</h1>
            <p className="text-muted-foreground">{patient.patient_code}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Link href={`/patients/${id}/edit`}>
            <Button variant="outline">
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </Link>
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* Patient Profile */}
      <Card>
        <CardHeader>
          <CardTitle>Patient Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Name</p>
                <p className="font-medium">{fullName}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Age</p>
                <p className="font-medium">
                  {age} years ({formatDate(patient.date_of_birth)})
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Gender</p>
                <Badge variant="outline">{formatGender(patient.gender)}</Badge>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Phone className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Phone</p>
                <p className="font-medium">{formatPhone(patient.phone)}</p>
              </div>
            </div>

            {patient.email && (
              <div className="flex items-start gap-3">
                <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{patient.email}</p>
                </div>
              </div>
            )}

            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">Blood Group</p>
                <p className="font-medium">{formatBloodGroup(patient.blood_group)}</p>
              </div>
            </div>

            {patient.address && (
              <div className="flex items-start gap-3 md:col-span-2">
                <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm text-muted-foreground">Address</p>
                  <p className="font-medium">{patient.address}</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Emergency Contact */}
      {(patient.emergency_contact_name || patient.emergency_contact_phone) && (
        <Card>
          <CardHeader>
            <CardTitle>Emergency Contact</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {patient.emergency_contact_name && (
                <div className="flex items-start gap-3">
                  <User className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm text-muted-foreground">Contact Name</p>
                    <p className="font-medium">{patient.emergency_contact_name}</p>
                  </div>
                </div>
              )}
              {patient.emergency_contact_phone && (
                <div className="flex items-start gap-3">
                  <Phone className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm text-muted-foreground">Contact Phone</p>
                    <p className="font-medium">
                      {formatPhone(patient.emergency_contact_phone)}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      {tags && tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Tags</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Badge key={tag.id} variant="secondary">
                  {tag.tag}
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
            <CardTitle>Diagnoses History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {diagnoses.map((diagnosis) => (
                <div
                  key={diagnosis.id}
                  className="border-l-4 border-indigo-500 pl-4 py-2"
                >
                  <p className="font-medium">{diagnosis.diagnosis}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(diagnosis.diagnosed_at)}
                  </p>
                  {diagnosis.notes && (
                    <p className="text-sm mt-1">{diagnosis.notes}</p>
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
            <DialogTitle>Delete Patient</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {fullName}? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deletePatient.isLoading}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deletePatient.isLoading}
            >
              {deletePatient.isLoading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
