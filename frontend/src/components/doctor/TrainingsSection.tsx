'use client'

import { useState } from 'react'
import {
  useDoctorTrainings,
  useCreateDoctorTraining,
  useUpdateDoctorTraining,
  useDeleteDoctorTraining,
} from '@/lib/hooks/useDoctor'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import type { DoctorTraining, DoctorTrainingCreate } from '@/types/doctor'
import {
  Award,
  PlusCircle,
  Edit2,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
  Calendar,
} from 'lucide-react'
import { format } from 'date-fns'

export function TrainingsSection() {
  const [activeOnly, setActiveOnly] = useState(false)
  const { data: trainings, isLoading } = useDoctorTrainings(activeOnly)
  const createTraining = useCreateDoctorTraining()
  const updateTraining = useUpdateDoctorTraining()
  const deleteTraining = useDeleteDoctorTraining()

  const [showDialog, setShowDialog] = useState(false)
  const [editingTraining, setEditingTraining] = useState<DoctorTraining | null>(null)
  const [formData, setFormData] = useState<DoctorTrainingCreate>({
    training_type: '',
    title: '',
    provider: '',
    completion_date: format(new Date(), 'yyyy-MM-dd'),
  })

  const handleOpenDialog = (training?: DoctorTraining) => {
    if (training) {
      setEditingTraining(training)
      setFormData({
        training_type: training.training_type,
        title: training.title,
        provider: training.provider,
        description: training.description,
        skills: training.skills,
        start_date: training.start_date || undefined,
        completion_date: training.completion_date,
        expiry_date: training.expiry_date,
        certificate_url: training.certificate_url,
        credential_id: training.credential_id,
        display_order: training.display_order,
      })
    } else {
      setEditingTraining(null)
      setFormData({
        training_type: '',
        title: '',
        provider: '',
        completion_date: format(new Date(), 'yyyy-MM-dd'),
      })
    }
    setShowDialog(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editingTraining) {
      await updateTraining.mutateAsync({ id: editingTraining.id, data: formData })
    } else {
      await createTraining.mutateAsync(formData)
    }
    setShowDialog(false)
    setEditingTraining(null)
  }

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this training?')) {
      await deleteTraining.mutateAsync(id)
    }
  }

  const isExpired = (expiryDate: string | null) => {
    if (!expiryDate) return false
    return new Date(expiryDate) < new Date()
  }

  const isFormValid = formData.training_type && formData.title && formData.provider

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
          <h2 className="text-2xl font-bold">Trainings & Certifications</h2>
          <p className="text-muted-foreground">Manage your professional development</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant={activeOnly ? 'default' : 'outline'}
            onClick={() => setActiveOnly(!activeOnly)}
          >
            {activeOnly ? 'Show All' : 'Active Only'}
          </Button>
          <Button onClick={() => handleOpenDialog()}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Training
          </Button>
        </div>
      </div>

      {trainings && trainings.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {trainings.map((training) => (
            <Card key={training.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="bg-indigo-100 dark:bg-indigo-900 p-2 rounded-lg">
                      <Award className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <CardTitle className="text-lg">{training.title}</CardTitle>
                        {training.is_verified ? (
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Verified
                          </Badge>
                        ) : (
                          <Badge variant="outline">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Pending
                          </Badge>
                        )}
                        {training.expiry_date &&
                          (isExpired(training.expiry_date) ? (
                            <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                              Expired
                            </Badge>
                          ) : (
                            <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                              Active
                            </Badge>
                          ))}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {training.training_type} • {training.provider}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenDialog(training)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(training.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {training.description && (
                  <div>
                    <p className="text-sm font-medium">Description</p>
                    <p className="text-sm text-muted-foreground">{training.description}</p>
                  </div>
                )}
                {training.skills && (
                  <div>
                    <p className="text-sm font-medium mb-1">Skills</p>
                    <div className="flex flex-wrap gap-1">
                      {training.skills.split(',').map((skill, index) => (
                        <Badge key={index} variant="outline">
                          {skill.trim()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                <div className="flex flex-wrap gap-4 text-sm">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>
                      {training.start_date &&
                        `${format(new Date(training.start_date), 'MMM yyyy')} - `}
                      {format(new Date(training.completion_date), 'MMM yyyy')}
                    </span>
                  </div>
                  {training.expiry_date && (
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <span>Expires: {format(new Date(training.expiry_date), 'MMM yyyy')}</span>
                    </div>
                  )}
                  {training.credential_id && (
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <span>ID: {training.credential_id}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-12 text-center">
          <Award className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
          <p className="text-lg font-semibold mb-2">
            {activeOnly ? 'No Active Trainings' : 'No Trainings Added'}
          </p>
          <p className="text-muted-foreground mb-6">
            {activeOnly
              ? 'You have no active certifications. Try viewing all trainings.'
              : 'Add your certifications and professional development courses'}
          </p>
          <Button onClick={() => handleOpenDialog()}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Your First Training
          </Button>
        </Card>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingTraining ? 'Edit Training' : 'Add Training'}
            </DialogTitle>
            <DialogDescription>
              {editingTraining
                ? 'Update your training information'
                : 'Add a new certification or training to your profile'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="training_type">
                  Training Type <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="training_type"
                  placeholder="e.g., Certification, Workshop"
                  value={formData.training_type}
                  onChange={(e) =>
                    setFormData({ ...formData, training_type: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="provider">
                  Provider <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="provider"
                  placeholder="Issuing organization"
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">
                Title <span className="text-red-500">*</span>
              </Label>
              <Input
                id="title"
                placeholder="Training or certification title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="Brief description of what you learned"
                value={formData.description || ''}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value || null })
                }
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="skills">Skills (Optional)</Label>
              <Input
                id="skills"
                placeholder="Comma-separated skills gained"
                value={formData.skills || ''}
                onChange={(e) => setFormData({ ...formData, skills: e.target.value || null })}
              />
              <p className="text-xs text-muted-foreground">
                Separate skills with commas (e.g., Acupuncture, Nutrition, Herbal Medicine)
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date (Optional)</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, start_date: e.target.value || undefined })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="completion_date">
                  Completion Date <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="completion_date"
                  type="date"
                  value={formData.completion_date}
                  onChange={(e) =>
                    setFormData({ ...formData, completion_date: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="expiry_date">Expiry Date (Optional)</Label>
                <Input
                  id="expiry_date"
                  type="date"
                  value={formData.expiry_date || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, expiry_date: e.target.value || null })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="credential_id">Credential ID (Optional)</Label>
              <Input
                id="credential_id"
                placeholder="Unique credential ID from issuer"
                value={formData.credential_id || ''}
                onChange={(e) =>
                  setFormData({ ...formData, credential_id: e.target.value || null })
                }
              />
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
                disabled={
                  !isFormValid || createTraining.isLoading || updateTraining.isLoading
                }
              >
                {createTraining.isLoading || updateTraining.isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>{editingTraining ? 'Update' : 'Add'} Training</>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
