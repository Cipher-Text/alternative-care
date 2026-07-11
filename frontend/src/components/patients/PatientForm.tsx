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
  full_name: z.string().min(1, 'Full name is required'),
  date_of_birth: z.string().optional(),
  gender: z.enum(['male', 'female', 'other']).optional(),
  phone: z.string().max(20).optional().or(z.literal('')),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  blood_group: z.string().optional(),
  address: z.string().optional(),
  division_id: z.string().optional(),
  district_id: z.string().optional(),
  upazila_id: z.string().optional(),
})

type PatientFormData = z.infer<typeof patientSchema>

interface PatientFormProps {
  patient?: Patient
  onSubmit: (data: PatientCreateRequest) => void
  isSubmitting?: boolean
}

export function PatientForm({ patient, onSubmit, isSubmitting }: PatientFormProps) {
  const [selectedDivision, setSelectedDivision] = useState<string>(
    patient?.division_id?.toString() || ''
  )
  const [selectedDistrict, setSelectedDistrict] = useState<string>(
    patient?.district_id?.toString() || ''
  )

  const { data: divisions } = useDivisions()
  const { data: districts } = useDistricts(selectedDivision ? Number(selectedDivision) : null)
  const { data: upazilas } = useUpazilas(selectedDistrict ? Number(selectedDistrict) : null)

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
          full_name: patient.full_name,
          date_of_birth: patient.date_of_birth || '',
          gender: patient.gender || undefined,
          phone: patient.phone || '',
          email: patient.email || '',
          blood_group: patient.blood_group || '',
          address: patient.address || '',
          division_id: patient.division_id?.toString() || '',
          district_id: patient.district_id?.toString() || '',
          upazila_id: patient.upazila_id?.toString() || '',
        }
      : {},
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

  const handleFormSubmit = async (data: PatientFormData) => {
    const payload: PatientCreateRequest = {
      full_name: data.full_name,
    }

    if (data.date_of_birth) payload.date_of_birth = data.date_of_birth
    if (data.gender) payload.gender = data.gender
    if (data.phone) payload.phone = data.phone
    if (data.email) payload.email = data.email
    if (data.blood_group) payload.blood_group = data.blood_group as PatientCreateRequest['blood_group']
    if (data.address) payload.address = data.address
    if (data.division_id) payload.division_id = Number(data.division_id)
    if (data.district_id) payload.district_id = Number(data.district_id)
    if (data.upazila_id) payload.upazila_id = Number(data.upazila_id)

    await onSubmit(payload)
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
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="full_name">Full Name *</Label>
              <Input
                id="full_name"
                placeholder="Patient's full name"
                {...register('full_name')}
                disabled={isSubmitting}
              />
              {errors.full_name && (
                <p className="text-sm text-red-500">{errors.full_name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="date_of_birth">Date of Birth</Label>
              <Input
                id="date_of_birth"
                type="date"
                {...register('date_of_birth')}
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="gender">Gender</Label>
              <Select
                value={watchedGender || ''}
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
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
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
                    <SelectItem key={division.id} value={division.id.toString()}>
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
                    <SelectItem key={district.id} value={district.id.toString()}>
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
                    <SelectItem key={upazila.id} value={upazila.id.toString()}>
                      {upazila.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Submit */}
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
