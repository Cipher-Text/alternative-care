'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Loader2,
  Pencil,
  Pill,
  Plus,
  Search,
  ShieldAlert,
  Trash2,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import {
  useMedicines,
  useMedicine,
  useCreateMedicine,
  useUpdateMedicine,
  useDeleteMedicine,
} from '@/lib/hooks/useMedicines'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { MedicalSystem, Medicine, MedicineCreate, MedicineListItem } from '@/types/medicine'

const medicalSystems: Array<{ value: MedicalSystem; label: string }> = [
  { value: 'homeopathy', label: 'Homeopathy' },
  { value: 'ayurveda', label: 'Ayurveda' },
  { value: 'unani', label: 'Unani' },
  { value: 'herbal', label: 'Herbal' },
]

const emptyForm: MedicineCreate = {
  name_en: '',
  name_bn: null,
  system: 'homeopathy',
  category: null,
  description_en: null,
  description_bn: null,
  potency: null,
  dosage_guidance_en: null,
  dosage_guidance_bn: null,
  indications_en: null,
  indications_bn: null,
  contraindications_en: null,
  contraindications_bn: null,
  is_global: true,
  is_active: true,
}

function toFormState(medicine: Medicine): MedicineCreate {
  return {
    name_en: medicine.name_en,
    name_bn: medicine.name_bn,
    system: medicine.system,
    category: medicine.category,
    description_en: medicine.description_en,
    description_bn: medicine.description_bn,
    potency: medicine.potency,
    dosage_guidance_en: medicine.dosage_guidance_en,
    dosage_guidance_bn: medicine.dosage_guidance_bn,
    indications_en: medicine.indications_en,
    indications_bn: medicine.indications_bn,
    contraindications_en: medicine.contraindications_en,
    contraindications_bn: medicine.contraindications_bn,
    is_global: medicine.is_global,
    is_active: medicine.is_active,
  }
}

function MedicineFormDialog({
  initial,
  isEditing,
  isSaving,
  onCancel,
  onSubmit,
}: {
  initial: MedicineCreate
  isEditing: boolean
  isSaving: boolean
  onCancel: () => void
  onSubmit: (data: MedicineCreate) => void
}) {
  const [form, setForm] = useState<MedicineCreate>(initial)

  const updateForm = <K extends keyof MedicineCreate>(key: K, value: MedicineCreate[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.name_en.trim()) return
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit}>
      <DialogHeader>
        <DialogTitle>{isEditing ? 'Edit Medicine' : 'Add Medicine'}</DialogTitle>
        <DialogDescription>
          Global medicines are visible to every clinic on the platform.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4 py-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name_en">Name (English) *</Label>
            <Input
              id="name_en"
              value={form.name_en}
              onChange={(event) => updateForm('name_en', event.target.value)}
              placeholder="Arnica Montana"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="name_bn">Name (Bengali)</Label>
            <Input
              id="name_bn"
              value={form.name_bn || ''}
              onChange={(event) => updateForm('name_bn', event.target.value || null)}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>System *</Label>
            <Select
              value={form.system}
              onValueChange={(value) => updateForm('system', value as MedicalSystem)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {medicalSystems.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Input
              id="category"
              value={form.category || ''}
              onChange={(event) => updateForm('category', event.target.value || null)}
              placeholder="e.g. Mother Tincture"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="potency">Potency</Label>
            <Input
              id="potency"
              value={form.potency || ''}
              onChange={(event) => updateForm('potency', event.target.value || null)}
              placeholder="e.g. 30C"
            />
          </div>
        </div>

        {isEditing && (
          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={form.is_active ? 'active' : 'inactive'}
              onValueChange={(value) => updateForm('is_active', value === 'active')}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="description_en">Description</Label>
          <Textarea
            id="description_en"
            value={form.description_en || ''}
            onChange={(event) => updateForm('description_en', event.target.value || null)}
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="dosage_guidance_en">Dosage Guidance</Label>
          <Textarea
            id="dosage_guidance_en"
            value={form.dosage_guidance_en || ''}
            onChange={(event) => updateForm('dosage_guidance_en', event.target.value || null)}
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="indications_en">Indications</Label>
          <Textarea
            id="indications_en"
            value={form.indications_en || ''}
            onChange={(event) => updateForm('indications_en', event.target.value || null)}
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="contraindications_en">Contraindications</Label>
          <Textarea
            id="contraindications_en"
            value={form.contraindications_en || ''}
            onChange={(event) => updateForm('contraindications_en', event.target.value || null)}
            rows={2}
          />
        </div>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving || !form.name_en.trim()}>
          {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          {isEditing ? 'Save Changes' : 'Add Medicine'}
        </Button>
      </DialogFooter>
    </form>
  )
}

export default function AdminMedicinesPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  // GET /medicines is visible to any authenticated user, and for a platform
  // caller (tenant_id=null) it narrows to global-only rows automatically —
  // this page is the global catalog, curated by admins, viewable by operators.
  const isPlatformRole = user?.role === 'admin' || user?.role === 'operator'
  const canEdit = user?.role === 'admin'

  const [searchTerm, setSearchTerm] = useState('')
  const [systemFilter, setSystemFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<'active' | 'inactive'>('active')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const medicines = useMedicines(
    {
      system: systemFilter === 'all' ? undefined : (systemFilter as MedicalSystem),
      is_global: true,
      is_active: statusFilter === 'active',
      limit: 500,
    },
    { enabled: isPlatformRole }
  )
  const editingMedicine = useMedicine(editingId ?? 0, { enabled: editingId !== null })
  const createMedicine = useCreateMedicine({ onSuccess: () => setDialogOpen(false) })
  const updateMedicine = useUpdateMedicine({ onSuccess: () => setDialogOpen(false) })
  const deleteMedicine = useDeleteMedicine()

  const filtered = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    if (!term) return medicines.data || []

    return (medicines.data || []).filter((medicine) =>
      [medicine.name_en, medicine.name_bn || '', medicine.category || '']
        .some((value) => value.toLowerCase().includes(term))
    )
  }, [medicines.data, searchTerm])

  const openCreateDialog = () => {
    setEditingId(null)
    setDialogOpen(true)
  }

  const openEditDialog = (medicine: MedicineListItem) => {
    setEditingId(medicine.id)
    setDialogOpen(true)
  }

  const handleSubmit = async (data: MedicineCreate) => {
    if (editingId) {
      await updateMedicine.mutateAsync({
        id: editingId,
        data: {
          name_en: data.name_en,
          name_bn: data.name_bn,
          system: data.system,
          category: data.category,
          description_en: data.description_en,
          description_bn: data.description_bn,
          potency: data.potency,
          dosage_guidance_en: data.dosage_guidance_en,
          dosage_guidance_bn: data.dosage_guidance_bn,
          indications_en: data.indications_en,
          indications_bn: data.indications_bn,
          contraindications_en: data.contraindications_en,
          contraindications_bn: data.contraindications_bn,
          is_active: data.is_active,
        },
      })
    } else {
      await createMedicine.mutateAsync({ ...data, is_global: true })
    }
  }

  const handleDeactivate = (medicine: MedicineListItem) => {
    if (!confirm(`Deactivate "${medicine.name_en}"?`)) return
    deleteMedicine.mutate(medicine.id)
  }

  if (!isPlatformRole) {
    return (
      <div className="flex min-h-[420px] items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-600" />
              Admin Access Required
            </CardTitle>
            <CardDescription>
              The global medicine catalog is available only to platform staff.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const isDetailLoading = editingId !== null && editingMedicine.isLoading
  const isFormReady = editingId === null || (!isDetailLoading && !!editingMedicine.data)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Medicines</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {canEdit
              ? 'Curate the global medicine catalog shared across every clinic.'
              : 'View the global medicine catalog shared across every clinic.'}
          </p>
        </div>
        {canEdit && (
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Medicine
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Global Catalog</CardTitle>
          <CardDescription>
            {medicines.data?.length ?? 0} medicine{medicines.data?.length === 1 ? '' : 's'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search name or category"
                className="pl-9"
              />
            </div>
            <Select value={systemFilter} onValueChange={setSystemFilter}>
              <SelectTrigger className="md:w-48">
                <SelectValue placeholder="System" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All systems</SelectItem>
                {medicalSystems.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as 'active' | 'inactive')}
            >
              <SelectTrigger className="md:w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {medicines.isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
          ) : filtered.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Medicine</TableHead>
                  <TableHead>System</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Potency</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((medicine) => (
                  <TableRow key={medicine.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{medicine.name_en}</p>
                        {medicine.name_bn && (
                          <p className="text-sm text-muted-foreground">{medicine.name_bn}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {medicine.system}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{medicine.category || '—'}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{medicine.potency || '—'}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={medicine.is_active ? 'default' : 'outline'}>
                        {medicine.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {canEdit ? (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openEditDialog(medicine)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          {medicine.is_active && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeactivate(medicine)}
                              disabled={deleteMedicine.isLoading}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">Read only</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <Pill className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No medicines found</h3>
              <p className="text-muted-foreground mt-2">
                {canEdit ? 'Add one, or adjust your search and filters.' : 'Adjust your search and filters.'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {isFormReady ? (
            <MedicineFormDialog
              key={editingId ?? 'new'}
              initial={editingId && editingMedicine.data ? toFormState(editingMedicine.data) : emptyForm}
              isEditing={!!editingId}
              isSaving={createMedicine.isLoading || updateMedicine.isLoading}
              onCancel={() => setDialogOpen(false)}
              onSubmit={handleSubmit}
            />
          ) : (
            <>
              <DialogTitle className="sr-only">Loading medicine</DialogTitle>
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
