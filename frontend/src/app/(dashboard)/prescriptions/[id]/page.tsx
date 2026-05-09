'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  usePrescription,
  useIssuePrescription,
  useVoidPrescription,
  useGeneratePrescriptionPDF,
  useDeletePrescriptionItem,
} from '@/lib/hooks/usePrescriptions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  ArrowLeft,
  Edit,
  FileText,
  Lock,
  CheckCircle,
  XCircle,
  Download,
  Loader2,
  AlertCircle,
  Trash2,
} from 'lucide-react'
import { format } from 'date-fns'
import type { PrescriptionStatus } from '@/types/prescription'

const statusConfig: Record<
  PrescriptionStatus,
  { label: string; icon: any; color: string }
> = {
  draft: {
    label: 'Draft',
    icon: Edit,
    color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  },
  issued: {
    label: 'Issued',
    icon: CheckCircle,
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  },
  voided: {
    label: 'Voided',
    icon: XCircle,
    color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  },
}

export default function PrescriptionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const [showIssueDialog, setShowIssueDialog] = useState(false)
  const [showVoidDialog, setShowVoidDialog] = useState(false)

  const { data: prescription, isLoading, error } = usePrescription(id)
  const issuePrescription = useIssuePrescription()
  const voidPrescription = useVoidPrescription()
  const generatePDF = useGeneratePrescriptionPDF()
  const deleteItem = useDeletePrescriptionItem()

  const handleIssue = async () => {
    await issuePrescription.mutateAsync(id)
    setShowIssueDialog(false)
  }

  const handleVoid = async () => {
    await voidPrescription.mutateAsync(id)
    setShowVoidDialog(false)
  }

  const handleGeneratePDF = async () => {
    await generatePDF.mutateAsync(id)
  }

  const handleDeleteItem = async (itemId: number) => {
    if (confirm('Are you sure you want to delete this item?')) {
      await deleteItem.mutateAsync({ prescriptionId: id, itemId })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error || !prescription) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Prescription Not Found</h2>
        <p className="text-muted-foreground mb-4">
          The prescription you're looking for doesn't exist or has been removed.
        </p>
        <Link href="/prescriptions">
          <Button>Back to Prescriptions</Button>
        </Link>
      </div>
    )
  }

  const isDraft = prescription.status === 'draft'
  const isIssued = prescription.status === 'issued'
  const isVoided = prescription.status === 'voided'
  const statusInfo = statusConfig[prescription.status]
  const StatusIcon = statusInfo.icon

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/prescriptions">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">Prescription</h1>
              <Badge className={statusInfo.color}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {statusInfo.label}
              </Badge>
              {isIssued && (
                <span title="Immutable">
                  <Lock className="h-5 w-5 text-muted-foreground" />
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground font-mono">ID: {prescription.id}</p>
          </div>
        </div>

        <div className="flex gap-2">
          {isDraft && (
            <>
              <Link href={`/prescriptions/${id}/edit`}>
                <Button variant="outline">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              </Link>
              <Button onClick={() => setShowIssueDialog(true)}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Issue
              </Button>
            </>
          )}
          {isIssued && (
            <>
              <Button
                variant="outline"
                onClick={handleGeneratePDF}
                disabled={generatePDF.isLoading}
              >
                {generatePDF.isLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Download PDF
              </Button>
              <Button variant="destructive" onClick={() => setShowVoidDialog(true)}>
                <XCircle className="h-4 w-4 mr-2" />
                Void
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Immutability Warning */}
      {isIssued && (
        <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3">
          <Lock className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900 dark:text-blue-100">
              This prescription is immutable
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Issued prescriptions cannot be edited. You can only void them if needed.
            </p>
          </div>
        </div>
      )}

      {/* Prescription Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Patient Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-sm text-muted-foreground">Patient ID</p>
              <p className="font-mono">{prescription.patient_id}</p>
            </div>
            {prescription.visit_id && (
              <div>
                <p className="text-sm text-muted-foreground">Visit ID</p>
                <p className="font-mono">{prescription.visit_id}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prescription Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-sm text-muted-foreground">Prescribed By</p>
              <p className="font-mono">{prescription.prescribed_by}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p>{format(new Date(prescription.created_at), 'PPP p')}</p>
            </div>
            {prescription.pdf_generated_at && (
              <div>
                <p className="text-sm text-muted-foreground">PDF Generated</p>
                <p>{format(new Date(prescription.pdf_generated_at), 'PPP p')}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Clinical Information */}
      <Card>
        <CardHeader>
          <CardTitle>Clinical Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {prescription.diagnosis && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">Diagnosis</p>
              <p className="mt-1">{prescription.diagnosis}</p>
            </div>
          )}
          {prescription.doctors_notes && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">Doctor's Notes</p>
              <p className="mt-1 whitespace-pre-wrap">{prescription.doctors_notes}</p>
            </div>
          )}
          {prescription.advice && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">Advice</p>
              <p className="mt-1 whitespace-pre-wrap">{prescription.advice}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Prescription Items */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Medicines ({prescription.items.length})</CardTitle>
            {isDraft && (
              <Link href={`/prescriptions/${id}/edit`}>
                <Button variant="outline" size="sm">
                  Add Medicine
                </Button>
              </Link>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {prescription.items.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Medicine</TableHead>
                  <TableHead>Dosage</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Quantity</TableHead>
                  <TableHead>Instructions</TableHead>
                  {isDraft && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {prescription.items.map((item, index) => (
                  <TableRow key={item.id}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell className="font-medium">
                      {item.medicine_name || `Medicine ID: ${item.medicine_id}`}
                    </TableCell>
                    <TableCell>{item.dosage}</TableCell>
                    <TableCell>{item.frequency}</TableCell>
                    <TableCell>{item.duration || '-'}</TableCell>
                    <TableCell>{item.quantity || '-'}</TableCell>
                    <TableCell>{item.instructions || '-'}</TableCell>
                    {isDraft && (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteItem(item.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No medicines added yet</p>
              {isDraft && (
                <Link href={`/prescriptions/${id}/edit`}>
                  <Button variant="outline" className="mt-4" size="sm">
                    Add Medicines
                  </Button>
                </Link>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Issue Dialog */}
      <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Issue Prescription</DialogTitle>
            <DialogDescription>
              Are you sure you want to issue this prescription? Once issued, it cannot be edited.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowIssueDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleIssue} disabled={issuePrescription.isLoading}>
              {issuePrescription.isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Issuing...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Issue Prescription
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Void Dialog */}
      <Dialog open={showVoidDialog} onOpenChange={setShowVoidDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Void Prescription</DialogTitle>
            <DialogDescription>
              Are you sure you want to void this prescription? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVoidDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleVoid}
              disabled={voidPrescription.isLoading}
            >
              {voidPrescription.isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Voiding...
                </>
              ) : (
                <>
                  <XCircle className="mr-2 h-4 w-4" />
                  Void Prescription
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
