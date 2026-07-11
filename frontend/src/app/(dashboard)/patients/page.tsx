'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePatients } from '@/lib/hooks/usePatients'
import { PatientCard } from '@/components/patients/PatientCard'
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
  const [search, setSearch] = useState('')
  const [gender, setGender] = useState<string>('')

  const { data: patients, isLoading, error } = usePatients()

  // Client-side filtering
  const filteredPatients = patients?.filter((patient) => {
    const matchesSearch = `${patient.full_name} ${patient.phone ?? ''}`
      .toLowerCase()
      .includes(search.toLowerCase())
    const matchesGender = !gender || patient.gender === gender
    return matchesSearch && matchesGender
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400" />
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Patients</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your patient records and information
          </p>
        </div>
        <Link href="/patients/new">
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/50">
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Patient
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500 dark:text-gray-500" />
          <Input
            placeholder="Search by name, phone, or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder:text-gray-500"
          />
        </div>
        <Select value={gender} onValueChange={setGender}>
          <SelectTrigger className="w-[180px] bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
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
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-indigo-500/10 transition-all duration-200">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Patients</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{patients?.length || 0}</p>
        </div>
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-indigo-500/10 transition-all duration-200">
          <p className="text-sm text-gray-600 dark:text-gray-400">Male</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {patients?.filter((p) => p.gender === 'male').length || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-indigo-500/10 transition-all duration-200">
          <p className="text-sm text-gray-600 dark:text-gray-400">Female</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {patients?.filter((p) => p.gender === 'female').length || 0}
          </p>
        </div>
      </div>

      {/* Patient Grid */}
      {filteredPatients && filteredPatients.length > 0 ? (
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
          {!search && !gender && (
            <Link href="/patients/new">
              <Button className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white">
                <PlusCircle className="mr-2 h-4 w-4" />
                Add First Patient
              </Button>
            </Link>
          )}
        </div>
      )}
    </div>
  )
}
