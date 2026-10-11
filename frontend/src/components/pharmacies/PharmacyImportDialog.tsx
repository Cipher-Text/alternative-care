'use client'

import { useRef, useState } from 'react'
import { CheckCircle2, Download, Loader2, Upload, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { apiErrorMessage, useImportPharmacies } from '@/lib/hooks/usePharmacies'
import type { PharmacyImportResult } from '@/types/pharmacy'

const TEMPLATE_HEADER =
  'name_en,name_bn,pharmacy_type,disciplines,address,district,latitude,longitude,phone,whatsapp,email,website_url,opening_hours,delivers,notes_en,notes_bn,source_url'
const TEMPLATE_EXAMPLE =
  'Example Homeo Hall,উদাহরণ হোমিও হল,retail,homeopathy;unani,"Mitford Road, Dhaka",Dhaka,23.7104,90.4074,01711000000,,,,Sat-Thu 10:00-21:00,yes,,,https://example.com/source'

function downloadTemplate() {
  // The BOM makes Excel read the Bengali example as UTF-8
  const blob = new Blob(['﻿' + TEMPLATE_HEADER + '\n' + TEMPLATE_EXAMPLE + '\n'], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'pharmacies-template.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

interface PharmacyImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PharmacyImportDialog({ open, onOpenChange }: PharmacyImportDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<PharmacyImportResult | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const importCsv = useImportPharmacies()

  const reset = () => {
    setFile(null)
    setResult(null)
    setFailure(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleOpenChange = (next: boolean) => {
    if (!next) reset()
    onOpenChange(next)
  }

  const handleUpload = () => {
    if (!file) return
    setResult(null)
    setFailure(null)
    importCsv.mutate(file, {
      onSuccess: setResult,
      onError: (error) => setFailure(apiErrorMessage(error, 'The import failed')),
    })
  }

  const hasErrors = (result?.errors.length ?? 0) > 0

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import pharmacies from CSV</DialogTitle>
          <DialogDescription>
            UTF-8 file with a header row, up to 1000 rows. It is all-or-nothing: if any row is
            invalid nothing is saved and every problem is listed. Rows that already exist (same name
            in the same district) are skipped, so re-uploading a fixed file is safe.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Button type="button" variant="outline" size="sm" onClick={downloadTemplate}>
            <Download className="mr-2 h-4 w-4" />
            Download template
          </Button>

          <div className="space-y-2">
            <label htmlFor="pharmacy-csv" className="text-sm font-medium">
              CSV file
            </label>
            <input
              ref={inputRef}
              id="pharmacy-csv"
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null)
                setResult(null)
                setFailure(null)
              }}
              className="block w-full text-sm file:mr-3 file:rounded-md file:border file:bg-background file:px-3 file:py-1.5 file:text-sm"
            />
          </div>

          {failure && (
            <p role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
              <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
              {failure}
            </p>
          )}

          {result && !hasErrors && (
            <p role="status" className="flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              Imported {result.created} pharmac{result.created === 1 ? 'y' : 'ies'}
              {result.skipped > 0 && `, skipped ${result.skipped} that already exist`}.
            </p>
          )}

          {hasErrors && result && (
            <div role="alert" className="space-y-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm dark:border-red-900 dark:bg-red-950">
              <p className="font-medium text-red-800 dark:text-red-200">
                Nothing was imported. Fix these {result.errors.length} row
                {result.errors.length === 1 ? '' : 's'} and upload again:
              </p>
              <ul className="max-h-56 space-y-1 overflow-y-auto text-red-700 dark:text-red-300">
                {result.errors.map((e) => (
                  <li key={e.row}>
                    <span className="font-mono">Line {e.row}:</span> {e.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-end gap-2 border-t pt-4">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              {result && !hasErrors ? 'Done' : 'Cancel'}
            </Button>
            <Button type="button" onClick={handleUpload} disabled={!file || importCsv.isLoading}>
              {importCsv.isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              Upload
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
