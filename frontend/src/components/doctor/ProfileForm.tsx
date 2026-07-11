'use client'

import { useState, useEffect } from 'react'
import { useUpdateDoctorProfile } from '@/lib/hooks/useDoctor'
import { useDivisions, useDistricts, useUpazilas } from '@/lib/hooks/usePatients'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { DoctorProfile, DoctorProfileUpdate } from '@/types/doctor'
import { Save, X, Loader2 } from 'lucide-react'

interface ProfileFormProps {
  profile: DoctorProfile
  isEditing: boolean
  onCancel: () => void
  onSuccess: () => void
}

export function ProfileForm({ profile, isEditing, onCancel, onSuccess }: ProfileFormProps) {
  const updateProfile = useUpdateDoctorProfile()
  const { data: divisions } = useDivisions()
  const [selectedDivision, setSelectedDivision] = useState<string>(
    profile.division_id?.toString() || ''
  )
  const [selectedDistrict, setSelectedDistrict] = useState<string>(
    profile.district_id?.toString() || ''
  )
  const { data: districts } = useDistricts(selectedDivision ? parseInt(selectedDivision) : null)
  const { data: upazilas } = useUpazilas(selectedDistrict ? parseInt(selectedDistrict) : null)

  const [formData, setFormData] = useState<DoctorProfileUpdate>({
    full_name: profile.full_name,
    phone: profile.phone || '',
    language: profile.language,
    clinic_name: profile.clinic_name || '',
    clinic_address: profile.clinic_address || '',
    division_id: profile.division_id || undefined,
    district_id: profile.district_id || undefined,
    upazila_id: profile.upazila_id || undefined,
    license_number: profile.license_number || '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await updateProfile.mutateAsync(formData)
    onSuccess()
  }

  if (!isEditing) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Full Name</p>
              <p className="font-medium">{profile.full_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Email</p>
              <p className="font-medium">{profile.email}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Phone</p>
              <p className="font-medium">{profile.phone || 'Not provided'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Language</p>
              <p className="font-medium capitalize">{profile.language === 'en' ? 'English' : 'Bengali'}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Clinic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Clinic Name</p>
              <p className="font-medium">{profile.clinic_name || 'Not provided'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Address</p>
              <p className="font-medium">{profile.clinic_address || 'Not provided'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">License Number</p>
              <p className="font-medium">{profile.license_number || 'Not provided'}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email (Read-only)</Label>
              <Input id="email" value={profile.email} disabled />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                placeholder="+880..."
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <Select
                value={formData.language}
                onValueChange={(value) =>
                  setFormData({ ...formData, language: value as 'en' | 'bn' })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="bn">Bengali</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Clinic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="clinic_name">Clinic Name</Label>
              <Input
                id="clinic_name"
                placeholder="Your clinic name"
                value={formData.clinic_name}
                onChange={(e) => setFormData({ ...formData, clinic_name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="clinic_address">Clinic Address</Label>
              <Textarea
                id="clinic_address"
                placeholder="Full clinic address"
                value={formData.clinic_address}
                onChange={(e) =>
                  setFormData({ ...formData, clinic_address: e.target.value })
                }
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="division">Division</Label>
              <Select
                value={selectedDivision}
                onValueChange={(value) => {
                  setSelectedDivision(value)
                  setFormData({ ...formData, division_id: parseInt(value) })
                }}
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
              <Label htmlFor="district">District</Label>
              <Select
                value={selectedDistrict}
                onValueChange={(value) => {
                  setSelectedDistrict(value)
                  setFormData({ ...formData, district_id: parseInt(value) })
                }}
                disabled={!selectedDivision}
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
              <Label htmlFor="upazila">Upazila</Label>
              <Select
                value={formData.upazila_id?.toString() || ''}
                onValueChange={(value) =>
                  setFormData({ ...formData, upazila_id: parseInt(value) })
                }
                disabled={!selectedDistrict}
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

            <div className="space-y-2">
              <Label htmlFor="license_number">License Number</Label>
              <Input
                id="license_number"
                placeholder="Professional license number"
                value={formData.license_number}
                onChange={(e) =>
                  setFormData({ ...formData, license_number: e.target.value })
                }
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end gap-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          <X className="mr-2 h-4 w-4" />
          Cancel
        </Button>
        <Button type="submit" disabled={updateProfile.isLoading}>
          {updateProfile.isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </form>
  )
}
