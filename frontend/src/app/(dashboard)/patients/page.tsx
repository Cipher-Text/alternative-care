'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePatients } from '@/lib/hooks/usePatients'
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { PatientCard } from '@/components/patients/PatientCard'
import { useCan } from '@/lib/auth/permissions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PlusCircle, Search, Loader2 } from 'lucide-react'

export default function PatientsPage() {
  const can = useCan()
  const [search, setSearch] = useState('')
  const [gender, setGender] = useState<string>('')

  const debouncedSearch = useDebouncedValue(search)
  const pager = usePager(undefined, [debouncedSearch.trim()])

  // Search and paging run on the server; ask for one extra row to know whether a next page exists
  const { data, isLoading, error, isFetching } = usePatients({
    search: debouncedSearch.trim() || undefined,
    limit: pager.pageSize + 1,
    offset: pager.offset,
  })
  const { items: patients, hasNext } = serverPage(data, pager.pageSize)

  // Gender has no server filter yet, so it narrows the rows on the current page
  const filteredPatients = patients.filter((patient) => !gender || gender === 'all' || patient.gender === gender)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600 dark:text-emerald-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-600 dark:text-red-400 py-8">
        <p className="text-lg font-semibold">Failed to load patients</p>
        <p className="text-sm">Please try again later</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Patients</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your patient records and information
          </p>
        </div>
        {can.writeClinical && (
          <Link href="/patients/new">
            <Button className="bg-primary hover:bg-slate-950 dark:hover:bg-emerald-800 text-white shadow-lg shadow-slate-900/10">
              <PlusCircle className="mr-2 h-4 w-4" />
              Add Patient
            </Button>
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500 dark:text-gray-500" />
          <Input
            aria-label="Search by name, phone, or code"
 placeholder="Search by name, phone, or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder:text-gray-500"
          />
        </div>
        <Select value={gender} onValueChange={(value) => setGender(value === 'all' ? '' : value)}>
          <SelectTrigger aria-label="All Genders" className="w-[180px] bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
            <SelectValue placeholder="All Genders" />
          </SelectTrigger>
          <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700">
            <SelectItem value="all">All Genders</SelectItem>
            <SelectItem value="male">Male</SelectItem>
            <SelectItem value="female">Female</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-md dark:hover:shadow-emerald-500/10 transition-all duration-200">
          <p className="text-sm text-gray-600 dark:text-gray-400">On this page</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{patients.length}</p>
        </div>
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-md dark:hover:shadow-emerald-500/10 transition-all duration-200">
          <p className="text-sm text-gray-600 dark:text-gray-400">Male (this page)</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {patients.filter((p) => p.gender === 'male').length}
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-md dark:hover:shadow-emerald-500/10 transition-all duration-200">
          <p className="text-sm text-gray-600 dark:text-gray-400">Female (this page)</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {patients.filter((p) => p.gender === 'female').length}
          </p>
        </div>
      </div>

      {/* Patient Grid */}
      {filteredPatients.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPatients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-slate-800/50 rounded-lg border border-gray-200 dark:border-slate-700">
          <p className="text-gray-600 dark:text-gray-400">
            {search || gender
              ? 'No patients found matching your filters'
              : 'No patients yet. Add your first patient to get started.'}
          </p>
          {!search && !gender && can.writeClinical && (
            <Link href="/patients/new">
              <Button className="mt-4 bg-primary hover:bg-slate-950 dark:hover:bg-emerald-800 text-white">
                <PlusCircle className="mr-2 h-4 w-4" />
                Add First Patient
              </Button>
            </Link>
          )}
        </div>
      )}

      <Pager
        page={pager.page}
        pageSize={pager.pageSize}
        count={patients.length}
        hasNext={hasNext}
        onPageChange={pager.setPage}
        isLoading={isFetching}
        noun="patients"
      />
    </div>
  )
}
