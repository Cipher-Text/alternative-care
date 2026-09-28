'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Loader2,
  Pencil,
  Plus,
  Search,
  ShieldAlert,
  Stethoscope,
  Trash2,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import {
  useSymptoms,
  useSymptom,
  useCreateSymptom,
  useUpdateSymptom,
  useDeleteSymptom,
} from '@/lib/hooks/useSymptoms'
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
import type { Symptom, SymptomCategory, SymptomCreate, SymptomListItem } from '@/types/symptom'

const symptomCategories: SymptomCategory[] = [
  'general',
  'respiratory',
  'digestive',
  'neurological',
  'mental',
  'musculoskeletal',
  'skin',
  'immune',
  'cardiovascular',
  'metabolic',
  'reproductive',
  'ear_nose_throat',
]

const emptyForm: SymptomCreate = {
  name_en: '',
  name_bn: null,
  description_en: null,
  description_bn: null,
  category: null,
  is_global: true,
  is_active: true,
}

function toFormState(symptom: Symptom): SymptomCreate {
  return {
    name_en: symptom.name_en,
    name_bn: symptom.name_bn,
    description_en: symptom.description_en,
    description_bn: symptom.description_bn,
    category: symptom.category,
    is_global: symptom.is_global,
    is_active: symptom.is_active,
  }
}

function SymptomFormDialog({
  initial,
  isEditing,
  isSaving,
  onCancel,
  onSubmit,
}: {
  initial: SymptomCreate
  isEditing: boolean
  isSaving: boolean
  onCancel: () => void
  onSubmit: (data: SymptomCreate) => void
}) {
  const [form, setForm] = useState<SymptomCreate>(initial)

  const updateForm = <K extends keyof SymptomCreate>(key: K, value: SymptomCreate[K]) => {
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
        <DialogTitle>{isEditing ? 'Edit Symptom' : 'Add Symptom'}</DialogTitle>
        <DialogDescription>
          Global symptoms are visible to every clinic on the platform.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <Label htmlFor="name_en">Name (English) *</Label>
          <Input
            id="name_en"
            value={form.name_en}
            onChange={(event) => updateForm('name_en', event.target.value)}
            placeholder="Sudden fever"
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

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Category</Label>
            <Select
              value={form.category || 'none'}
              onValueChange={(value) => updateForm('category', value === 'none' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="No category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No category</SelectItem>
                {symptomCategories.map((c) => (
                  <SelectItem key={c} value={c} className="capitalize">
                    {c.replace(/_/g, ' ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {isEditing && (
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={form.is_active ? 'active' : 'inactive'}
                onValueChange={(value) => updateForm('is_active', value === 'active')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description_en">Description</Label>
          <Textarea
            id="description_en"
            value={form.description_en || ''}
            onChange={(event) => updateForm('description_en', event.target.value || null)}
            rows={3}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description_bn">Description (Bengali)</Label>
          <Textarea
            id="description_bn"
            value={form.description_bn || ''}
            onChange={(event) => updateForm('description_bn', event.target.value || null)}
            rows={3}
          />
        </div>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving || !form.name_en.trim()}>
          {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          {isEditing ? 'Save Changes' : 'Add Symptom'}
        </Button>
      </DialogFooter>
    </form>
  )
}

export default function AdminSymptomsPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  // GET /symptoms is visible to any authenticated user, and for a platform
  // caller (tenant_id=null) it narrows to global-only rows automatically —
  // this page is the global catalog, curated by admins, viewable by operators.
  const isPlatformRole = user?.role === 'admin' || user?.role === 'operator'
  const canEdit = user?.role === 'admin'

  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<'active' | 'inactive'>('active')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const symptoms = useSymptoms(
    {
      category: categoryFilter === 'all' ? undefined : categoryFilter,
      is_global: true,
      is_active: statusFilter === 'active',
      limit: 500,
    },
    { enabled: isPlatformRole }
  )
  const editingSymptom = useSymptom(editingId ?? 0, { enabled: editingId !== null })
  const createSymptom = useCreateSymptom({ onSuccess: () => setDialogOpen(false) })
  const updateSymptom = useUpdateSymptom({ onSuccess: () => setDialogOpen(false) })
  const deleteSymptom = useDeleteSymptom()

  const filtered = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    if (!term) return symptoms.data || []

    return (symptoms.data || []).filter((symptom) =>
      [symptom.name_en, symptom.name_bn || '', symptom.category || '']
        .some((value) => value.toLowerCase().includes(term))
    )
  }, [symptoms.data, searchTerm])

  const openCreateDialog = () => {
    setEditingId(null)
    setDialogOpen(true)
  }

  const openEditDialog = (symptom: SymptomListItem) => {
    setEditingId(symptom.id)
    setDialogOpen(true)
  }

  const handleSubmit = async (data: SymptomCreate) => {
    if (editingId) {
      await updateSymptom.mutateAsync({
        id: editingId,
        data: {
          name_en: data.name_en,
          name_bn: data.name_bn,
          description_en: data.description_en,
          description_bn: data.description_bn,
          category: data.category,
          is_active: data.is_active,
        },
      })
    } else {
      await createSymptom.mutateAsync({ ...data, is_global: true })
    }
  }

  const handleDeactivate = (symptom: SymptomListItem) => {
    if (!confirm(`Deactivate "${symptom.name_en}"?`)) return
    deleteSymptom.mutate(symptom.id)
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
              The global symptom catalog is available only to platform staff.
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

  const isDetailLoading = editingId !== null && editingSymptom.isLoading
  const isFormReady = editingId === null || (!isDetailLoading && !!editingSymptom.data)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Symptoms</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {canEdit
              ? 'Curate the global symptom catalog shared across every clinic.'
              : 'View the global symptom catalog shared across every clinic.'}
          </p>
        </div>
        {canEdit && (
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Symptom
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Global Catalog</CardTitle>
          <CardDescription>
            {symptoms.data?.length ?? 0} symptom{symptoms.data?.length === 1 ? '' : 's'}
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
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="md:w-52">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {symptomCategories.map((c) => (
                  <SelectItem key={c} value={c} className="capitalize">
                    {c.replace(/_/g, ' ')}
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

          {symptoms.isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
          ) : filtered.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symptom</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((symptom) => (
                  <TableRow key={symptom.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{symptom.name_en}</p>
                        {symptom.name_bn && (
                          <p className="text-sm text-muted-foreground">{symptom.name_bn}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {symptom.category ? (
                        <Badge variant="outline" className="capitalize">
                          {symptom.category.replace(/_/g, ' ')}
                        </Badge>
                      ) : (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={symptom.is_active ? 'default' : 'outline'}>
                        {symptom.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {canEdit ? (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openEditDialog(symptom)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          {symptom.is_active && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeactivate(symptom)}
                              disabled={deleteSymptom.isLoading}
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
              <Stethoscope className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No symptoms found</h3>
              <p className="text-muted-foreground mt-2">
                {canEdit ? 'Add one, or adjust your search and filters.' : 'Adjust your search and filters.'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          {isFormReady ? (
            <SymptomFormDialog
              key={editingId ?? 'new'}
              initial={editingId && editingSymptom.data ? toFormState(editingSymptom.data) : emptyForm}
              isEditing={!!editingId}
              isSaving={createSymptom.isLoading || updateSymptom.isLoading}
              onCancel={() => setDialogOpen(false)}
              onSubmit={handleSubmit}
            />
          ) : (
            <>
              <DialogTitle className="sr-only">Loading symptom</DialogTitle>
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
