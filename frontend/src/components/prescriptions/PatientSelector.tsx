'use client'

import { useState, useEffect, useRef } from 'react'
import { usePatient, usePatients } from '@/lib/hooks/usePatients'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Search, User, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

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
  const { data: searchResults, isLoading } = usePatients(
    searchQuery.length >= 2 ? { search: searchQuery, limit: 20 } : undefined
  )

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

  const handleSelectPatient = (id: string) => {
    onChange(id)
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

  const getAge = (dob: string | null): string => {
    if (!dob) return 'Unknown age'
    const birthDate = new Date(dob)
    const today = new Date()
    let age = today.getFullYear() - birthDate.getFullYear()
    const monthDiff = today.getMonth() - birthDate.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) age--
    return `${age} years`
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
                <h4 className="font-semibold mb-1">{selectedPatient.full_name}</h4>
                <div className="text-sm text-muted-foreground space-y-0.5">
                  <p>
                    {getAge(selectedPatient.date_of_birth)}
                    {selectedPatient.gender
                      ? ` • ${selectedPatient.gender.charAt(0).toUpperCase() + selectedPatient.gender.slice(1)}`
                      : ''}
                  </p>
                  {selectedPatient.phone && <p>{selectedPatient.phone}</p>}
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
              placeholder="Search by name or phone..."
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

          {showDropdown && searchQuery.length >= 2 && (
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
                      onClick={() => handleSelectPatient(patient.id)}
                      className="w-full px-4 py-3 hover:bg-accent text-left transition-colors"
                    >
                      <p className="font-medium">{patient.full_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {getAge(patient.date_of_birth)}
                        {patient.gender
                          ? ` • ${patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)}`
                          : ''}
                        {patient.phone ? ` • ${patient.phone}` : ''}
                      </p>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center">
                  <User className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">
                    No patients found matching &quot;{searchQuery}&quot;
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
