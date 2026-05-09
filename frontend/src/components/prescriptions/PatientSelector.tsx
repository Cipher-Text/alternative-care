'use client'

import { useState, useEffect, useRef } from 'react'
import { usePatient, useSearchPatients } from '@/lib/hooks/usePatients'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Search, User, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { Patient } from '@/types/patient'
import { format } from 'date-fns'

interface PatientSelectorProps {
  value: string
  onChange: (patientId: string) => void
  disabled?: boolean
}

export function PatientSelector({ value, onChange, disabled = false }: PatientSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  const { data: selectedPatient } = usePatient(value)
  const { data: searchResults, isLoading } = useSearchPatients(searchQuery)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelectPatient = (patient: Patient) => {
    onChange(patient.id)
    setSearchQuery('')
    setShowDropdown(false)
  }

  const handleClearSelection = () => {
    onChange('')
    setSearchQuery('')
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
    setShowDropdown(true)
  }

  const getAge = (dob: string) => {
    const birthDate = new Date(dob)
    const today = new Date()
    let age = today.getFullYear() - birthDate.getFullYear()
    const monthDiff = today.getMonth() - birthDate.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--
    }
    return age
  }

  return (
    <div ref={wrapperRef} className="relative">
      {selectedPatient ? (
        <Card className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 flex-1">
              <div className="bg-indigo-100 dark:bg-indigo-900 p-2 rounded-full">
                <User className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold">
                    {selectedPatient.first_name} {selectedPatient.last_name}
                  </h4>
                  <Badge variant="outline" className="text-xs">
                    {selectedPatient.patient_code}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground space-y-0.5">
                  <p>
                    {getAge(selectedPatient.date_of_birth)} years old •{' '}
                    {selectedPatient.gender.charAt(0).toUpperCase() +
                      selectedPatient.gender.slice(1)}
                  </p>
                  <p>{selectedPatient.phone}</p>
                  {selectedPatient.email && <p>{selectedPatient.email}</p>}
                </div>
              </div>
            </div>
            {!disabled && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearSelection}
                className="flex-shrink-0"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, phone, or patient code..."
              value={searchQuery}
              onChange={handleInputChange}
              onFocus={() => setShowDropdown(true)}
              disabled={disabled}
              className="pl-10"
            />
            {isLoading && (
              <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>

          {showDropdown && searchQuery && (
            <Card className="absolute z-50 w-full mt-2 max-h-80 overflow-y-auto shadow-lg">
              {isLoading ? (
                <div className="p-8 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                  <p className="text-sm text-muted-foreground mt-2">Searching...</p>
                </div>
              ) : searchResults && searchResults.length > 0 ? (
                <div className="py-2">
                  {searchResults.map((patient) => (
                    <button
                      key={patient.id}
                      onClick={() => handleSelectPatient(patient)}
                      className="w-full px-4 py-3 hover:bg-accent text-left transition-colors"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium">
                              {patient.first_name} {patient.last_name}
                            </p>
                            <Badge variant="outline" className="text-xs">
                              {patient.patient_code}
                            </Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            <p>
                              {getAge(patient.date_of_birth)} years •{' '}
                              {patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)}{' '}
                              • {patient.phone}
                            </p>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center">
                  <User className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">
                    No patients found matching "{searchQuery}"
                  </p>
                </div>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  )
}
