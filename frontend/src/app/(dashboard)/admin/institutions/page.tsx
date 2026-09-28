'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  BadgeCheck,
  ExternalLink,
  GraduationCap,
  Loader2,
  Pencil,
  Plus,
  Search,
  ShieldAlert,
  Trash2,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import {
  useInstitutions,
  useCreateInstitution,
  useUpdateInstitution,
  useDeleteInstitution,
} from '@/lib/hooks/useInstitutions'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
import type { InstitutionCreate, InstitutionListItem, Discipline } from '@/types/institution'

const disciplines: Array<{ value: Discipline; label: string }> = [
  { value: 'homeopathy', label: 'Homeopathy' },
  { value: 'ayurveda', label: 'Ayurveda' },
  { value: 'unani', label: 'Unani' },
  { value: 'herbal', label: 'Herbal' },
]

const emptyForm: InstitutionCreate = {
  name_en: '',
  name_bn: null,
  institution_type: 'private',
  disciplines: [],
  courses_offered: null,
  location: null,
  district_id: null,
  website_url: null,
  registration_code: null,
  source_url: null,
  is_active: true,
}

function toFormState(institution: InstitutionListItem): InstitutionCreate {
  return {
    name_en: institution.name_en,
    name_bn: institution.name_bn,
    institution_type: institution.institution_type,
    disciplines: institution.disciplines as Discipline[],
    courses_offered: institution.courses_offered,
    location: institution.location,
    district_id: null,
    website_url: institution.website_url,
    registration_code: institution.registration_code,
    source_url: institution.source_url,
    is_active: institution.is_active,
  }
}

export default function AdminInstitutionsPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  // GET /institutions only requires an authenticated user on the backend
  // (app/modules/institution/routes.py) — admin and operator ("moderator") can
  // both view the directory. Write endpoints (create/update/delete) are
  // admin-only there, so canEdit gates the mutating UI separately.
  const isPlatformRole = user?.role === 'admin' || user?.role === 'operator'
  const canEdit = user?.role === 'admin'

  const [searchTerm, setSearchTerm] = useState('')
  const [disciplineFilter, setDisciplineFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<InstitutionCreate>(emptyForm)

  const institutions = useInstitutions({
    discipline: disciplineFilter === 'all' ? undefined : (disciplineFilter as Discipline),
    institution_type: typeFilter === 'all' ? undefined : (typeFilter as 'government' | 'private'),
    limit: 500,
  })
  const createInstitution = useCreateInstitution({ onSuccess: () => setDialogOpen(false) })
  const updateInstitution = useUpdateInstitution({ onSuccess: () => setDialogOpen(false) })
  const deleteInstitution = useDeleteInstitution()

  const filtered = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    if (!term) return institutions.data || []

    return (institutions.data || []).filter((institution) =>
      [
        institution.name_en,
        institution.name_bn || '',
        institution.location || '',
        institution.registration_code || '',
      ].some((value) => value.toLowerCase().includes(term))
    )
  }, [institutions.data, searchTerm])

  const updateForm = <K extends keyof InstitutionCreate>(key: K, value: InstitutionCreate[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const toggleDiscipline = (discipline: Discipline) => {
    setForm((current) => {
      const exists = current.disciplines.includes(discipline)
      return {
        ...current,
        disciplines: exists
          ? current.disciplines.filter((d) => d !== discipline)
          : [...current.disciplines, discipline],
      }
    })
  }

  const openCreateDialog = () => {
    setEditingId(null)
    setForm(emptyForm)
    setDialogOpen(true)
  }

  const openEditDialog = (institution: InstitutionListItem) => {
    setEditingId(institution.id)
    setForm(toFormState(institution))
    setDialogOpen(true)
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.name_en.trim() || form.disciplines.length === 0) return

    if (editingId) {
      await updateInstitution.mutateAsync({ id: editingId, data: form })
    } else {
      await createInstitution.mutateAsync(form)
    }
  }

  const handleVerify = (institution: InstitutionListItem) => {
    updateInstitution.mutate({ id: institution.id, data: { is_verified: true } })
  }

  const handleDeactivate = (institution: InstitutionListItem) => {
    if (!confirm(`Deactivate "${institution.name_en}"?`)) return
    deleteInstitution.mutate(institution.id)
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
              The institution directory is available only to platform administrators.
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Institutions</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Educational institutions teaching Homeopathy, Ayurveda, Unani, and Herbal Medicine.
            Every listing is admin-curated and shown publicly; mark it Verified once cross-checked
            against the issuing board&apos;s own register.
          </p>
        </div>
        {canEdit && (
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Institution
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Institution Directory</CardTitle>
          <CardDescription>
            {institutions.data?.length ?? 0} institution{institutions.data?.length === 1 ? '' : 's'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search name, location, or registration code"
                className="pl-9"
              />
            </div>
            <Select value={disciplineFilter} onValueChange={setDisciplineFilter}>
              <SelectTrigger className="md:w-48">
                <SelectValue placeholder="Discipline" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All disciplines</SelectItem>
                {disciplines.map((d) => (
                  <SelectItem key={d.value} value={d.value}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="md:w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Government + Private</SelectItem>
                <SelectItem value="government">Government</SelectItem>
                <SelectItem value="private">Private</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {institutions.isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
          ) : filtered.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Institution</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Disciplines</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((institution) => (
                  <TableRow key={institution.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{institution.name_en}</p>
                        {institution.registration_code && (
                          <p className="text-sm text-muted-foreground">
                            Code: {institution.registration_code}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {institution.institution_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {institution.disciplines.map((d) => (
                          <Badge key={d} variant="secondary" className="capitalize">
                            {d}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[220px]">
                      <span className="text-sm">{institution.location || '—'}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant={institution.is_verified ? 'default' : 'outline'}>
                          {institution.is_verified ? 'Verified' : 'Unverified'}
                        </Badge>
                        {!institution.is_active && <Badge variant="destructive">Inactive</Badge>}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {institution.source_url && (
                          <Button asChild size="sm" variant="ghost">
                            <a href={institution.source_url} target="_blank" rel="noreferrer">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        )}
                        {canEdit && !institution.is_verified && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleVerify(institution)}
                            disabled={updateInstitution.isLoading}
                          >
                            <BadgeCheck className="h-4 w-4 mr-1" />
                            Verify
                          </Button>
                        )}
                        {canEdit && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openEditDialog(institution)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                        )}
                        {canEdit && institution.is_active && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeactivate(institution)}
                            disabled={deleteInstitution.isLoading}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <GraduationCap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No institutions found</h3>
              <p className="text-muted-foreground mt-2">
                Add one, or adjust your search and filters.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>{editingId ? 'Edit Institution' : 'Add Institution'}</DialogTitle>
              <DialogDescription>
                Institutions are shown on the public directory once active. Mark Verified only
                after cross-checking against the issuing board&apos;s own register.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name_en">Name (English) *</Label>
                <Input
                  id="name_en"
                  value={form.name_en}
                  onChange={(event) => updateForm('name_en', event.target.value)}
                  placeholder="Government Homeopathic Medical College & Hospital"
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
                  <Label>Type</Label>
                  <Select
                    value={form.institution_type}
                    onValueChange={(value) =>
                      updateForm('institution_type', value as 'government' | 'private')
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="government">Government</SelectItem>
                      <SelectItem value="private">Private</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="registration_code">Registration Code</Label>
                  <Input
                    id="registration_code"
                    value={form.registration_code || ''}
                    onChange={(event) => updateForm('registration_code', event.target.value || null)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Disciplines *</Label>
                <div className="grid grid-cols-4 gap-2">
                  {disciplines.map((d) => (
                    <Button
                      key={d.value}
                      type="button"
                      size="sm"
                      variant={form.disciplines.includes(d.value) ? 'default' : 'outline'}
                      onClick={() => toggleDiscipline(d.value)}
                      className="justify-center"
                    >
                      {d.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="courses_offered">Courses Offered</Label>
                <Input
                  id="courses_offered"
                  value={form.courses_offered || ''}
                  onChange={(event) => updateForm('courses_offered', event.target.value || null)}
                  placeholder="e.g. DHMS, BUMS, DAMS"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  value={form.location || ''}
                  onChange={(event) => updateForm('location', event.target.value || null)}
                  placeholder="e.g. Mirpur-14, Dhaka-1216"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="website_url">Website</Label>
                  <Input
                    id="website_url"
                    value={form.website_url || ''}
                    onChange={(event) => updateForm('website_url', event.target.value || null)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="source_url">Source URL</Label>
                  <Input
                    id="source_url"
                    value={form.source_url || ''}
                    onChange={(event) => updateForm('source_url', event.target.value || null)}
                  />
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={
                  createInstitution.isLoading ||
                  updateInstitution.isLoading ||
                  !form.name_en.trim() ||
                  form.disciplines.length === 0
                }
              >
                {(createInstitution.isLoading || updateInstitution.isLoading) && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                {editingId ? 'Save Changes' : 'Add Institution'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
