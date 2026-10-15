'use client'

import { useTranslations } from 'next-intl'
import { useState } from 'react'
import Link from 'next/link'
import { usePrescriptions, useViewPrescriptionPdf } from '@/lib/hooks/usePrescriptions'
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { PlusCircle, Search, Loader2, FileText, Eye } from 'lucide-react'
import { useDateFormat } from '@/lib/i18n/date'
import type { PrescriptionStatus } from '@/types/prescription'
import { useCan } from '@/lib/auth/permissions'

const statusColors: Record<PrescriptionStatus, string> = {
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  issued: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  voided: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
}

export default function PrescriptionsPage() {
  const tp = useTranslations('pages')
  const t = useTranslations('rxUi')
  const { fmt } = useDateFormat()
  const { can } = useCan()
  const viewPdf = useViewPrescriptionPdf()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string>('')

  const debouncedSearch = useDebouncedValue(search)
  const pager = usePager(undefined, [debouncedSearch.trim(), status])

  // Status, search and paging all run on the server; one extra row tells us a next page exists
  const { data, isLoading, error, isFetching } = usePrescriptions({
    status: (status || undefined) as PrescriptionStatus | undefined,
    search: debouncedSearch.trim() || undefined,
    limit: pager.pageSize + 1,
    offset: pager.offset,
  })
  const { items: prescriptions, hasNext } = serverPage(data, pager.pageSize)
  const filteredPrescriptions = prescriptions

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 py-8">
        <p className="text-lg font-semibold">{t('failedTitle')}</p>
        <p className="text-sm">{t('failedBody')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-3xl font-bold">{tp('prescriptionsTitle')}</h1>
          <p className="text-muted-foreground">
            {tp('prescriptionsSubtitle')}
          </p>
        </div>
        {can('prescriptions.write') && (
        <Link href="/prescriptions/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            {tp('newPrescription')}
          </Button>
        </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            aria-label={t('searchAria')}
 placeholder={t('searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          value={status || 'all'}
          onValueChange={(value) => setStatus(value === 'all' ? '' : value)}
        >
          <SelectTrigger aria-label={t('allStatuses')} className="w-[180px]">
            <SelectValue placeholder={t('allStatuses')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allStatuses')}</SelectItem>
            <SelectItem value="draft">{t('status.draft')}</SelectItem>
            <SelectItem value="issued">{t('status.issued')}</SelectItem>
            <SelectItem value="voided">{t('status.voided')}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">{t('statOnPage')}</p>
          <p className="text-2xl font-bold">{prescriptions.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">{t('statDrafts')}</p>
          <p className="text-2xl font-bold">
            {prescriptions.filter((p) => p.status === 'draft').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">{t('statIssued')}</p>
          <p className="text-2xl font-bold">
            {prescriptions.filter((p) => p.status === 'issued').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">{t('statVoided')}</p>
          <p className="text-2xl font-bold">
            {prescriptions.filter((p) => p.status === 'voided').length}
          </p>
        </div>
      </div>

      {/* Prescriptions Table */}
      {filteredPrescriptions.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('colPatientId')}</TableHead>
                <TableHead>{t('colDiagnosis')}</TableHead>
                <TableHead>{t('colStatus')}</TableHead>
                <TableHead>{t('colCreated')}</TableHead>
                <TableHead>{t('colPdf')}</TableHead>
                <TableHead className="text-right">{t('colActions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPrescriptions.map((prescription) => (
                <TableRow key={prescription.id}>
                  <TableCell>
                    <Link href={`/patients/${prescription.patient_id}`} className="font-medium hover:underline">
                      {prescription.patient_name || t('unknownPatient')}
                    </Link>
                    <p className="font-mono text-xs text-muted-foreground">#{prescription.id.substring(0, 8)}</p>
                  </TableCell>
                  <TableCell>
                    {prescription.diagnosis || (
                      <span className="text-muted-foreground italic">{t('noDiagnosis')}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={statusColors[prescription.status]}>
                      {t(`status.${prescription.status}`)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {fmt(prescription.created_at, 'MMM d, yyyy')}
                  </TableCell>
                  <TableCell>
                    {prescription.status !== 'draft' ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label={t('viewPrintPdf')}
                        onClick={() => viewPdf.mutate(prescription.id)}
                        disabled={viewPdf.isLoading}
                        className="text-emerald-600 hover:text-emerald-800"
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link href={`/prescriptions/${prescription.id}`}>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4 mr-1" />
                        {t('view')}
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
          <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            {search || status
              ? t('emptyFiltered')
              : t('emptyNone')}
          </p>
          {!search && !status && can('prescriptions.write') && (
            <Link href="/prescriptions/new">
              <Button className="mt-4">
                <PlusCircle className="mr-2 h-4 w-4" />
                {t('createFirst')}
              </Button>
            </Link>
          )}
        </div>
      )}

      <Pager
        page={pager.page}
        pageSize={pager.pageSize}
        count={prescriptions.length}
        hasNext={hasNext}
        onPageChange={pager.setPage}
        isLoading={isFetching}
        noun="prescriptions"
      />
    </div>
  )
}
