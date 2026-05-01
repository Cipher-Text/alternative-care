'use client'

import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useDivisions, useDistricts, useUpazilas } from '@/lib/hooks/usePatients'
import type { Patient, PatientCreateRequest } from '@/types/patient'
import { Loader2 } from 'lucide-react'

const patientSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  date_of_birth: z.string().min(1, 'Date of birth is required'),
  gender: z.enum(['male', 'female', 'other']),
  phone: z.string().min(11, 'Valid phone number is required'),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  address: z.string().optional(),
  division_id: z.string().optional(),
  district_id: z.string().optional(),
  upazila_id: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_phone: z.string().optional(),
  blood_group: z.string().optional(),
})

type PatientFormData = z.infer<typeof patientSchema>

interface PatientFormProps {
  patient?: Patient
  onSubmit: (data: PatientCreateRequest) => void
  isSubmitting?: boolean
}

export function PatientForm({ patient, onSubmit, isSubmitting }: PatientFormProps) {
  const [selectedDivision, setSelectedDivision] = useState<string>(
    patient?.division_id || ''
  )
  const [selectedDistrict, setSelectedDistrict] = useState<string>(
    patient?.district_id || ''
  )

  const { data: divisions } = useDivisions()
  const { data: districts } = useDistricts(selectedDivision)
  const { data: upazilas } = useUpazilas(selectedDistrict)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: patient
      ? {
          first_name: patient.first_name,
          last_name: patient.last_name,
          date_of_birth: patient.date_of_birth,
          gender: patient.gender,
          phone: patient.phone,
          email: patient.email || '',
          address: patient.address || '',
          division_id: patient.division_id || '',
          district_id: patient.district_id || '',
          upazila_id: patient.upazila_id || '',
          emergency_contact_name: patient.emergency_contact_name || '',
          emergency_contact_phone: patient.emergency_contact_phone || '',
          blood_group: patient.blood_group || '',
        }
      : {
          gender: 'male',
        },
  })

  const watchedGender = watch('gender')
  const watchedDivision = watch('division_id')
  const watchedDistrict = watch('district_id')
  const watchedUpazila = watch('upazila_id')

  // Reset district when division changes
  useEffect(() => {
    if (watchedDivision !== selectedDivision) {
      setSelectedDivision(watchedDivision || '')
      setValue('district_id', '')
      setValue('upazila_id', '')
      setSelectedDistrict('')
    }
  }, [watchedDivision, selectedDivision, setValue])

  // Reset upazila when district changes
  useEffect(() => {
    if (watchedDistrict !== selectedDistrict) {
      setSelectedDistrict(watchedDistrict || '')
      setValue('upazila_id', '')
    }
  }, [watchedDistrict, selectedDistrict, setValue])

  const handleFormSubmit = (data: PatientFormData) => {
    // Remove empty strings
    const cleanedData = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== '') {
        acc[key as keyof PatientCreateRequest] = value as any
      }
      return acc
    }, {} as PatientCreateRequest)

    onSubmit(cleanedData)
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="first_name">First Name *</Label>
              <Input
                id="first_name"
                {...register('first_name')}
                disabled={isSubmitting}
              />
              {errors.first_name && (
                <p className="text-sm text-red-500">{errors.first_name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="last_name">Last Name *</Label>
              <Input
                id="last_name"
                {...register('last_name')}
                disabled={isSubmitting}
              />
              {errors.last_name && (
                <p className="text-sm text-red-500">{errors.last_name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="date_of_birth">Date of Birth *</Label>
              <Input
                id="date_of_birth"
                type="date"
                {...register('date_of_birth')}
                disabled={isSubmitting}
              />
              {errors.date_of_birth && (
                <p className="text-sm text-red-500">{errors.date_of_birth.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="gender">Gender *</Label>
              <Select
                value={watchedGender}
                onValueChange={(value) =>
                  setValue('gender', value as 'male' | 'female' | 'other')
                }
                disabled={isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
              {errors.gender && (
                <p className="text-sm text-red-500">{errors.gender.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone *</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="01XXXXXXXXX"
                {...register('phone')}
                disabled={isSubmitting}
              />
              {errors.phone && (
                <p className="text-sm text-red-500">{errors.phone.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="patient@example.com"
                {...register('email')}
                disabled={isSubmitting}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="blood_group">Blood Group</Label>
              <Select
                value={watch('blood_group') || ''}
                onValueChange={(value) => setValue('blood_group', value)}
                disabled={isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select blood group" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="A+">A+</SelectItem>
                  <SelectItem value="A-">A-</SelectItem>
                  <SelectItem value="B+">B+</SelectItem>
                  <SelectItem value="B-">B-</SelectItem>
                  <SelectItem value="O+">O+</SelectItem>
                  <SelectItem value="O-">O-</SelectItem>
                  <SelectItem value="AB+">AB+</SelectItem>
                  <SelectItem value="AB-">AB-</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Address Information */}
      <Card>
        <CardHeader>
          <CardTitle>Address Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              placeholder="House/Road/Area"
              {...register('address')}
              disabled={isSubmitting}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="division_id">Division</Label>
              <Select
                value={watchedDivision || ''}
                onValueChange={(value) => setValue('division_id', value)}
                disabled={isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select division" />
                </SelectTrigger>
                <SelectContent>
                  {divisions?.map((division) => (
                    <SelectItem key={division.id} value={division.id}>
                      {division.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="district_id">District</Label>
              <Select
                value={watchedDistrict || ''}
                onValueChange={(value) => setValue('district_id', value)}
                disabled={!selectedDivision || isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select district" />
                </SelectTrigger>
                <SelectContent>
                  {districts?.map((district) => (
                    <SelectItem key={district.id} value={district.id}>
                      {district.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="upazila_id">Upazila</Label>
              <Select
                value={watchedUpazila || ''}
                onValueChange={(value) => setValue('upazila_id', value)}
                disabled={!selectedDistrict || isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select upazila" />
                </SelectTrigger>
                <SelectContent>
                  {upazilas?.map((upazila) => (
                    <SelectItem key={upazila.id} value={upazila.id}>
                      {upazila.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Emergency Contact */}
      <Card>
        <CardHeader>
          <CardTitle>Emergency Contact</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="emergency_contact_name">Contact Name</Label>
              <Input
                id="emergency_contact_name"
                placeholder="Guardian/Relative name"
                {...register('emergency_contact_name')}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergency_contact_phone">Contact Phone</Label>
              <Input
                id="emergency_contact_phone"
                type="tel"
                placeholder="01XXXXXXXXX"
                {...register('emergency_contact_phone')}
                disabled={isSubmitting}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Submit Button */}
      <div className="flex justify-end gap-4">
        <Button type="button" variant="outline" disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {patient ? 'Update Patient' : 'Create Patient'}
        </Button>
      </div>
    </form>
  )
}
