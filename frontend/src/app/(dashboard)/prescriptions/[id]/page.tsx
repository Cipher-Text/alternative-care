'use client'

import { use, useState } from 'react'
import { useTranslations } from 'next-intl'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  usePrescription,
  useIssuePrescription,
  useVoidPrescription,
  useViewPrescriptionPdf,
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
import { useDateFormat } from '@/lib/i18n/date'
import type { PrescriptionStatus } from '@/types/prescription'
import { useCan } from '@/lib/auth/permissions'

const statusConfig: Record<
  PrescriptionStatus,
  { icon: any; color: string }
> = {
  draft: {
    icon: Edit,
    color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  },
  issued: {
    icon: CheckCircle,
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  },
  voided: {
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
  const t = useTranslations('rxDetailUi')
  const ts = useTranslations('rxUi.status')
  const { fmt } = useDateFormat()
  const { can } = useCan()
  const [showIssueDialog, setShowIssueDialog] = useState(false)
  const [showVoidDialog, setShowVoidDialog] = useState(false)

  const { data: prescription, isLoading, error } = usePrescription(id)
  const issuePrescription = useIssuePrescription()
  const voidPrescription = useVoidPrescription()
  const viewPdf = useViewPrescriptionPdf()
  const deleteItem = useDeletePrescriptionItem()

  const handleIssue = async () => {
    await issuePrescription.mutateAsync(id)
    setShowIssueDialog(false)
  }

  const handleVoid = async () => {
    await voidPrescription.mutateAsync(id)
    setShowVoidDialog(false)
  }

  const handleViewPdf = async () => {
    await viewPdf.mutateAsync(id)
  }

  const handleDeleteItem = async (itemId: number) => {
    if (confirm(t('confirmDeleteItem'))) {
      await deleteItem.mutateAsync({ prescriptionId: id, itemId })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (error || !prescription) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">{t('notFoundTitle')}</h2>
        <p className="text-muted-foreground mb-4">
          {t('notFoundBody')}
        </p>
        <Link href="/prescriptions">
          <Button>{t('backToList')}</Button>
        </Link>
      </div>
    )
  }

  const isDraft = prescription.status === 'draft'
  // Drafts can be edited by anyone who may write prescriptions; issuing and voiding are their own permissions
  const canEditRx = can('prescriptions.write') && isDraft
  const isIssued = prescription.status === 'issued'
  const isVoided = prescription.status === 'voided'
  const statusInfo = statusConfig[prescription.status]
  const StatusIcon = statusInfo.icon

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/prescriptions" aria-label={t('back')}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">{t('title')}</h1>
              <Badge className={statusInfo.color}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {ts(prescription.status)}
              </Badge>
              {isIssued && (
                <span title={t('immutableTitle')}>
                  <Lock className="h-5 w-5 text-muted-foreground" />
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground font-mono">{t('idLabel', { id: prescription.id })}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {canEditRx && (
            <>
              <Link href={`/prescriptions/${id}/edit`}>
                <Button variant="outline">
                  <Edit className="h-4 w-4 mr-2" />
                  {t('edit')}
                </Button>
              </Link>
              {can('prescriptions.issue') && (
                <Button onClick={() => setShowIssueDialog(true)}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  {t('issue')}
                </Button>
              )}
            </>
          )}
          {isIssued && (
            <>
              <Button
                variant="outline"
                onClick={handleViewPdf}
                disabled={viewPdf.isLoading}
              >
                {viewPdf.isLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                {t('viewPrintPdf')}
              </Button>
              {can('prescriptions.void') && (
                <Button variant="destructive" onClick={() => setShowVoidDialog(true)}>
                  <XCircle className="h-4 w-4 mr-2" />
                  {t('void')}
                </Button>
              )}
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
              {t('immutableBannerTitle')}
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              {t('immutableBannerBody')}
            </p>
          </div>
        </div>
      )}

      {/* Prescription Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t('patientInfo')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-sm text-muted-foreground">{t('patient')}</p>
              <Link href={`/patients/${prescription.patient_id}`} className="font-medium hover:underline">
                {prescription.patient_name || t('unknownPatient')}
              </Link>
            </div>
            {prescription.visit_id && (
              <div>
                <p className="text-sm text-muted-foreground">{t('visit')}</p>
                <Link href={`/consultations/${prescription.visit_id}`} className="hover:underline">
                  {prescription.visit_date ? fmt(prescription.visit_date, 'PPP') : t('visit')}
                  {prescription.visit_complaint ? ` · ${prescription.visit_complaint.slice(0, 80)}` : ''}
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('details')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-sm text-muted-foreground">{t('prescribedBy')}</p>
              <p>{prescription.prescribed_by_name || t('unknownDoctor')}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{t('created')}</p>
              <p>{fmt(prescription.created_at, 'PPP p')}</p>
            </div>
            {prescription.pdf_generated_at && (
              <div>
                <p className="text-sm text-muted-foreground">{t('pdfGenerated')}</p>
                <p>{fmt(prescription.pdf_generated_at, 'PPP p')}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Clinical Information */}
      <Card>
        <CardHeader>
          <CardTitle>{t('clinicalInfo')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {prescription.diagnosis && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">{t('diagnosis')}</p>
              <p className="mt-1">{prescription.diagnosis}</p>
            </div>
          )}
          {prescription.doctors_notes && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">{t('doctorsNotes')}</p>
              <p className="mt-1 whitespace-pre-wrap">{prescription.doctors_notes}</p>
            </div>
          )}
          {prescription.advice && (
            <div>
              <p className="text-sm font-medium text-muted-foreground">{t('advice')}</p>
              <p className="mt-1 whitespace-pre-wrap">{prescription.advice}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Prescription Items */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>{t('medicinesCount', { count: prescription.items.length })}</CardTitle>
            {canEditRx && (
              <Link href={`/prescriptions/${id}/edit`}>
                <Button variant="outline" size="sm">
                  {t('addMedicine')}
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
                  <TableHead>{t('colMedicine')}</TableHead>
                  <TableHead>{t('colDosage')}</TableHead>
                  <TableHead>{t('colFrequency')}</TableHead>
                  <TableHead>{t('colDuration')}</TableHead>
                  <TableHead>{t('colQuantity')}</TableHead>
                  <TableHead>{t('colInstructions')}</TableHead>
                  {canEditRx && <TableHead className="text-right">{t('colActions')}</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {prescription.items.map((item, index) => (
                  <TableRow key={item.id}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell className="font-medium">
                      {item.medicine_name || t('medicineIdFallback', { id: String(item.medicine_id) })}
                    </TableCell>
                    <TableCell>{item.dosage}</TableCell>
                    <TableCell>{item.frequency}</TableCell>
                    <TableCell>{item.duration || '-'}</TableCell>
                    <TableCell>{item.quantity || '-'}</TableCell>
                    <TableCell>{item.instructions || '-'}</TableCell>
                    {canEditRx && (
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
              <p>{t('noMedicines')}</p>
              {canEditRx && (
                <Link href={`/prescriptions/${id}/edit`}>
                  <Button variant="outline" className="mt-4" size="sm">
                    {t('addMedicines')}
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
            <DialogTitle>{t('issueDialogTitle')}</DialogTitle>
            <DialogDescription>
              {t('issueDialogBody')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowIssueDialog(false)}>
              {t('cancel')}
            </Button>
            <Button onClick={handleIssue} disabled={issuePrescription.isLoading}>
              {issuePrescription.isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('issuing')}
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  {t('issueDialogTitle')}
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
            <DialogTitle>{t('voidDialogTitle')}</DialogTitle>
            <DialogDescription>
              {t('voidDialogBody')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVoidDialog(false)}>
              {t('cancel')}
            </Button>
            <Button
              variant="destructive"
              onClick={handleVoid}
              disabled={voidPrescription.isLoading}
            >
              {voidPrescription.isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('voiding')}
                </>
              ) : (
                <>
                  <XCircle className="mr-2 h-4 w-4" />
                  {t('voidDialogTitle')}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
