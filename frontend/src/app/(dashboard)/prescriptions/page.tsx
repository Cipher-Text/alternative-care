'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePrescriptions } from '@/lib/hooks/usePrescriptions'
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
import { format } from 'date-fns'
import type { PrescriptionStatus } from '@/types/prescription'

const statusColors: Record<PrescriptionStatus, string> = {
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  issued: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  voided: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
}

export default function PrescriptionsPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string>('')

  const { data: prescriptions, isLoading, error } = usePrescriptions({
    status: (status || undefined) as PrescriptionStatus | undefined,
  })

  // Client-side filtering for search
  const filteredPrescriptions = prescriptions?.filter((prescription) =>
    `${prescription.id} ${prescription.patient_id} ${prescription.diagnosis || ''}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 py-8">
        <p className="text-lg font-semibold">Failed to load prescriptions</p>
        <p className="text-sm">Please try again later</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Prescriptions</h1>
          <p className="text-muted-foreground">
            Manage patient prescriptions and medical advice
          </p>
        </div>
        <Link href="/prescriptions/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Prescription
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by prescription ID, patient ID, or diagnosis..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="issued">Issued</SelectItem>
            <SelectItem value="voided">Voided</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Total</p>
          <p className="text-2xl font-bold">{prescriptions?.length || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Drafts</p>
          <p className="text-2xl font-bold">
            {prescriptions?.filter((p) => p.status === 'draft').length || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Issued</p>
          <p className="text-2xl font-bold">
            {prescriptions?.filter((p) => p.status === 'issued').length || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Voided</p>
          <p className="text-2xl font-bold">
            {prescriptions?.filter((p) => p.status === 'voided').length || 0}
          </p>
        </div>
      </div>

      {/* Prescriptions Table */}
      {filteredPrescriptions && filteredPrescriptions.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Prescription ID</TableHead>
                <TableHead>Patient ID</TableHead>
                <TableHead>Diagnosis</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>PDF</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPrescriptions.map((prescription) => (
                <TableRow key={prescription.id}>
                  <TableCell className="font-mono text-sm">
                    {prescription.id.substring(0, 8)}...
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {prescription.patient_id.substring(0, 8)}...
                  </TableCell>
                  <TableCell>
                    {prescription.diagnosis || (
                      <span className="text-muted-foreground italic">No diagnosis</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={statusColors[prescription.status]}>
                      {prescription.status.charAt(0).toUpperCase() + prescription.status.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {format(new Date(prescription.created_at), 'MMM d, yyyy')}
                  </TableCell>
                  <TableCell>
                    {prescription.pdf_url ? (
                      <a
                        href={prescription.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        <FileText className="h-4 w-4" />
                      </a>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link href={`/prescriptions/${prescription.id}`}>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4 mr-1" />
                        View
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
              ? 'No prescriptions found matching your filters'
              : 'No prescriptions yet. Create your first prescription to get started.'}
          </p>
          {!search && !status && (
            <Link href="/prescriptions/new">
              <Button className="mt-4">
                <PlusCircle className="mr-2 h-4 w-4" />
                Create First Prescription
              </Button>
            </Link>
          )}
        </div>
      )}
    </div>
  )
}
