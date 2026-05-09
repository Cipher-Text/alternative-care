'use client'

import { useState } from 'react'
import {
  useDoctorDegrees,
  useCreateDoctorDegree,
  useUpdateDoctorDegree,
  useDeleteDoctorDegree,
} from '@/lib/hooks/useDoctor'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import type { DoctorDegree, DoctorDegreeCreate } from '@/types/doctor'
import {
  GraduationCap,
  PlusCircle,
  Edit2,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react'

export function DegreesSection() {
  const { data: degrees, isLoading } = useDoctorDegrees()
  const createDegree = useCreateDoctorDegree()
  const updateDegree = useUpdateDoctorDegree()
  const deleteDegree = useDeleteDoctorDegree()

  const [showDialog, setShowDialog] = useState(false)
  const [editingDegree, setEditingDegree] = useState<DoctorDegree | null>(null)
  const [formData, setFormData] = useState<DoctorDegreeCreate>({
    degree_type: '',
    degree_name: '',
    institution_name: '',
    completion_year: new Date().getFullYear(),
  })

  const handleOpenDialog = (degree?: DoctorDegree) => {
    if (degree) {
      setEditingDegree(degree)
      setFormData({
        degree_type: degree.degree_type,
        degree_name: degree.degree_name,
        specialization: degree.specialization,
        institution_name: degree.institution_name,
        institution_location: degree.institution_location,
        start_year: degree.start_year || undefined,
        completion_year: degree.completion_year,
        certificate_url: degree.certificate_url,
        display_order: degree.display_order,
      })
    } else {
      setEditingDegree(null)
      setFormData({
        degree_type: '',
        degree_name: '',
        institution_name: '',
        completion_year: new Date().getFullYear(),
      })
    }
    setShowDialog(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editingDegree) {
      await updateDegree.mutateAsync({ id: editingDegree.id, data: formData })
    } else {
      await createDegree.mutateAsync(formData)
    }
    setShowDialog(false)
    setEditingDegree(null)
  }

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this degree?')) {
      await deleteDegree.mutateAsync(id)
    }
  }

  const isFormValid = formData.degree_type && formData.degree_name && formData.institution_name

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Academic Degrees</h2>
          <p className="text-muted-foreground">Manage your academic qualifications</p>
        </div>
        <Button onClick={() => handleOpenDialog()}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Degree
        </Button>
      </div>

      {degrees && degrees.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {degrees.map((degree) => (
            <Card key={degree.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="bg-indigo-100 dark:bg-indigo-900 p-2 rounded-lg">
                      <GraduationCap className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{degree.degree_name}</CardTitle>
                      <p className="text-sm text-muted-foreground">{degree.degree_type}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenDialog(degree)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(degree.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {degree.specialization && (
                  <div>
                    <p className="text-sm font-medium">Specialization</p>
                    <p className="text-sm text-muted-foreground">{degree.specialization}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium">Institution</p>
                  <p className="text-sm text-muted-foreground">{degree.institution_name}</p>
                  {degree.institution_location && (
                    <p className="text-xs text-muted-foreground">{degree.institution_location}</p>
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium">Year</p>
                  <p className="text-sm text-muted-foreground">
                    {degree.start_year && `${degree.start_year} - `}
                    {degree.completion_year}
                  </p>
                </div>
                {degree.is_verified ? (
                  <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Verified
                  </Badge>
                ) : (
                  <Badge variant="outline">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Pending Verification
                  </Badge>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-12 text-center">
          <GraduationCap className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
          <p className="text-lg font-semibold mb-2">No Degrees Added</p>
          <p className="text-muted-foreground mb-6">
            Add your academic qualifications to build your professional profile
          </p>
          <Button onClick={() => handleOpenDialog()}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Your First Degree
          </Button>
        </Card>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingDegree ? 'Edit Degree' : 'Add Degree'}</DialogTitle>
            <DialogDescription>
              {editingDegree
                ? 'Update your degree information'
                : 'Add a new academic degree to your profile'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="degree_type">
                  Degree Type <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="degree_type"
                  placeholder="e.g., Bachelor, Master, Doctorate"
                  value={formData.degree_type}
                  onChange={(e) => setFormData({ ...formData, degree_type: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="degree_name">
                  Degree Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="degree_name"
                  placeholder="e.g., BHMS, BAMS, MD"
                  value={formData.degree_name}
                  onChange={(e) => setFormData({ ...formData, degree_name: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="specialization">Specialization (Optional)</Label>
              <Input
                id="specialization"
                placeholder="e.g., Pediatrics, Dermatology"
                value={formData.specialization || ''}
                onChange={(e) =>
                  setFormData({ ...formData, specialization: e.target.value || null })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="institution_name">
                Institution Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="institution_name"
                placeholder="University or College name"
                value={formData.institution_name}
                onChange={(e) =>
                  setFormData({ ...formData, institution_name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="institution_location">Institution Location (Optional)</Label>
              <Input
                id="institution_location"
                placeholder="City, Country"
                value={formData.institution_location || ''}
                onChange={(e) =>
                  setFormData({ ...formData, institution_location: e.target.value || null })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_year">Start Year (Optional)</Label>
                <Input
                  id="start_year"
                  type="number"
                  min="1900"
                  max="2100"
                  placeholder="e.g., 2015"
                  value={formData.start_year || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      start_year: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="completion_year">
                  Completion Year <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="completion_year"
                  type="number"
                  min="1900"
                  max="2100"
                  placeholder="e.g., 2020"
                  value={formData.completion_year}
                  onChange={(e) =>
                    setFormData({ ...formData, completion_year: parseInt(e.target.value) })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="certificate_url">Certificate URL (Optional)</Label>
              <Input
                id="certificate_url"
                type="url"
                placeholder="https://..."
                value={formData.certificate_url || ''}
                onChange={(e) =>
                  setFormData({ ...formData, certificate_url: e.target.value || null })
                }
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!isFormValid || createDegree.isLoading || updateDegree.isLoading}
              >
                {createDegree.isLoading || updateDegree.isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>{editingDegree ? 'Update' : 'Add'} Degree</>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
