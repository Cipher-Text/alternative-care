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

  const { data: patients, isLoading, error } = usePatients({ gender: gender || undefined })

  // Client-side filtering for search
  const filteredPatients = patients?.filter((patient) =>
    `${patient.first_name} ${patient.last_name} ${patient.phone} ${patient.patient_code}`
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
          <h1 className="text-3xl font-bold">Patients</h1>
          <p className="text-muted-foreground">
            Manage your patient records and information
          </p>
        </div>
        <Link href="/patients/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Patient
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, phone, or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={gender} onValueChange={setGender}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Genders" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Genders</SelectItem>
            <SelectItem value="male">Male</SelectItem>
            <SelectItem value="female">Female</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Total Patients</p>
          <p className="text-2xl font-bold">{patients?.length || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Male</p>
          <p className="text-2xl font-bold">
            {patients?.filter((p) => p.gender === 'male').length || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
          <p className="text-sm text-muted-foreground">Female</p>
          <p className="text-2xl font-bold">
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
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
          <p className="text-muted-foreground">
            {search || gender
              ? 'No patients found matching your filters'
              : 'No patients yet. Add your first patient to get started.'}
          </p>
          {!search && !gender && (
            <Link href="/patients/new">
              <Button className="mt-4">
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
