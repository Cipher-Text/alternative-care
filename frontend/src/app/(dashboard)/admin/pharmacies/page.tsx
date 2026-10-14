'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { differenceInCalendarDays, format } from 'date-fns'
import {
  BadgeCheck,
  CalendarCheck,
  MapPin,
  MapPinOff,
  Pencil,
  Phone,
  Plus,
  RotateCcw,
  Search,
  ShieldAlert,
  Store,
  Trash2,
  Upload,
  Loader2,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useDivisions } from '@/lib/hooks/usePatients'
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue'
import {
  useAllDistricts,
  useDeactivatePharmacy,
  usePharmacies,
  useUpdatePharmacy,
} from '@/lib/hooks/usePharmacies'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { PharmacyFormDialog } from '@/components/pharmacies/PharmacyFormDialog'
import { PharmacyImportDialog } from '@/components/pharmacies/PharmacyImportDialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  PHARMACY_DISCIPLINES,
  PHARMACY_TYPES,
  STALE_AFTER_DAYS,
  type PharmacyDiscipline,
  type PharmacyListItem,
  type PharmacyType,
} from '@/types/pharmacy'
import { useCan } from '@/lib/auth/permissions'

const typeLabel = (type: string) => PHARMACY_TYPES.find((t) => t.value === type)?.label ?? type

function Freshness({ confirmedAt }: { confirmedAt: string | null }) {
  if (!confirmedAt) {
    return <Badge variant="outline" className="border-amber-400 text-amber-700 dark:text-amber-300">Never confirmed</Badge>
  }
  const days = differenceInCalendarDays(new Date(), new Date(confirmedAt))
  return (
    <div className="space-y-1">
      <div className="text-sm">{format(new Date(confirmedAt), 'MMM d, yyyy')}</div>
      {days > STALE_AFTER_DAYS && (
        <Badge variant="outline" className="border-amber-400 text-amber-700 dark:text-amber-300">
          Stale · {days} days
        </Badge>
      )}
    </div>
  )
}

export default function AdminPharmaciesPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  // Reading is open to every authenticated user; writes are admin-only on the backend, so
  // operators see the directory but not the editing controls.
  const { can } = useCan()
  const isPlatformRole = !user?.tenant_id
  const canEdit = can('pharmacies.manage')

  const [searchTerm, setSearchTerm] = useState('')
  const [disciplineFilter, setDisciplineFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<'active' | 'inactive'>('active')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const debouncedSearch = useDebouncedValue(searchTerm.trim())
  const pager = usePager(undefined, [debouncedSearch, disciplineFilter, typeFilter, statusFilter])

  // Search, filters and paging all run on the server; one extra row tells us a next page exists
  const pharmacies = usePharmacies(
    {
      search: debouncedSearch || undefined,
      discipline: disciplineFilter === 'all' ? undefined : (disciplineFilter as PharmacyDiscipline),
      pharmacy_type: typeFilter === 'all' ? undefined : (typeFilter as PharmacyType),
      is_active: statusFilter === 'active',
      limit: pager.pageSize + 1,
      offset: pager.offset,
    },
    isPlatformRole
  )
  const { items, hasNext } = serverPage(pharmacies.data, pager.pageSize)

  const { data: divisions } = useDivisions()
  const { districts } = useAllDistricts(divisions)
  const districtName = (id: number | null) => districts.find((d) => d.id === id)?.name_en

  const update = useUpdatePharmacy({ quiet: true })
  const deactivate = useDeactivatePharmacy()

  const openCreate = () => {
    setEditingId(null)
    setDialogOpen(true)
  }
  const openEdit = (pharmacy: PharmacyListItem) => {
    setEditingId(pharmacy.id)
    setDialogOpen(true)
  }

  const confirmToday = (pharmacy: PharmacyListItem) =>
    update.mutate({ id: pharmacy.id, data: { mark_confirmed: true } })
  const verify = (pharmacy: PharmacyListItem) =>
    update.mutate({ id: pharmacy.id, data: { is_verified: true } })
  const reactivate = (pharmacy: PharmacyListItem) =>
    update.mutate({ id: pharmacy.id, data: { is_active: true } })
  const handleDeactivate = (pharmacy: PharmacyListItem) => {
    if (!confirm(`Deactivate "${pharmacy.name_en}"? It will be hidden from practitioners.`)) return
    deactivate.mutate(pharmacy.id)
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
            <CardDescription>The pharmacy directory is managed by platform staff.</CardDescription>
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
      <PharmacyFormDialog open={dialogOpen} onOpenChange={setDialogOpen} pharmacyId={editingId} />
      <PharmacyImportDialog open={importOpen} onOpenChange={setImportOpen} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Pharmacies</h1>
          <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">
            Pharmacies, wholesalers and depots where practitioners buy stock. Shared with every
            practitioner, so accuracy is on you: record the source, mark listings Verified once
            cross-checked, and use “Confirmed today” whenever you re-check one.
          </p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setImportOpen(true)}>
              <Upload className="mr-2 h-4 w-4" />
              Import CSV
            </Button>
            <Button onClick={openCreate}>
              <Plus className="mr-2 h-4 w-4" />
              Add pharmacy
            </Button>
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Store className="h-5 w-5 text-emerald-600" />
            Directory
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 md:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                aria-label="Search name or address"
                placeholder="Search name or address"
                className="pl-9"
              />
            </div>
            <Select value={disciplineFilter} onValueChange={setDisciplineFilter}>
              <SelectTrigger aria-label="Discipline" className="md:w-44">
                <SelectValue placeholder="Discipline" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All disciplines</SelectItem>
                {PHARMACY_DISCIPLINES.map((d) => (
                  <SelectItem key={d.value} value={d.value}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger aria-label="Type" className="md:w-44">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                {PHARMACY_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as 'active' | 'inactive')}>
              <SelectTrigger aria-label="Status" className="md:w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {pharmacies.isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
          ) : pharmacies.isError ? (
            <p className="py-8 text-center text-red-600">Could not load pharmacies. Please try again.</p>
          ) : items.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pharmacy</TableHead>
                  <TableHead>Stocks</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last confirmed</TableHead>
                  {canEdit && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((pharmacy) => (
                  <TableRow key={pharmacy.id}>
                    <TableCell>
                      <div className="font-medium">{pharmacy.name_en}</div>
                      {pharmacy.name_bn && <div className="text-sm text-muted-foreground">{pharmacy.name_bn}</div>}
                      <div className="text-xs text-muted-foreground">{typeLabel(pharmacy.pharmacy_type)}</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {pharmacy.disciplines.map((d) => (
                          <Badge key={d} variant="outline" className="capitalize">
                            {d}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[16rem]">
                      <div className="text-sm">{pharmacy.address || '—'}</div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        {districtName(pharmacy.district_id) && <span>{districtName(pharmacy.district_id)}</span>}
                        {pharmacy.latitude !== null ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
                            <MapPin className="h-3.5 w-3.5" /> Pinned
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-700 dark:text-amber-400">
                            <MapPinOff className="h-3.5 w-3.5" /> No pin
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {pharmacy.phone ? (
                        <a href={`tel:${pharmacy.phone}`} className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:underline dark:text-emerald-400">
                          <Phone className="h-3.5 w-3.5" />
                          {pharmacy.phone}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                      {pharmacy.delivers && <div className="mt-1 text-xs text-muted-foreground">Delivers</div>}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {pharmacy.is_verified ? (
                          <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">
                            <BadgeCheck className="mr-1 h-3.5 w-3.5" /> Verified
                          </Badge>
                        ) : (
                          <Badge variant="outline">Unverified</Badge>
                        )}
                        {!pharmacy.is_active && <Badge variant="secondary">Inactive</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Freshness confirmedAt={pharmacy.last_confirmed_at} />
                    </TableCell>
                    {canEdit && (
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" aria-label={`Edit ${pharmacy.name_en}`} title="Edit" onClick={() => openEdit(pharmacy)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" aria-label={`Mark ${pharmacy.name_en} confirmed today`} title="Confirmed today" onClick={() => confirmToday(pharmacy)} disabled={update.isLoading}>
                            <CalendarCheck className="h-4 w-4" />
                          </Button>
                          {!pharmacy.is_verified && (
                            <Button variant="ghost" size="icon" aria-label={`Verify ${pharmacy.name_en}`} title="Mark verified" onClick={() => verify(pharmacy)} disabled={update.isLoading}>
                              <BadgeCheck className="h-4 w-4" />
                            </Button>
                          )}
                          {pharmacy.is_active ? (
                            <Button variant="ghost" size="icon" aria-label={`Deactivate ${pharmacy.name_en}`} title="Deactivate" onClick={() => handleDeactivate(pharmacy)} disabled={deactivate.isLoading}>
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          ) : (
                            <Button variant="ghost" size="icon" aria-label={`Reactivate ${pharmacy.name_en}`} title="Reactivate" onClick={() => reactivate(pharmacy)} disabled={update.isLoading}>
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-12 text-center">
              <Store className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="text-lg font-semibold">No pharmacies found</h3>
              <p className="mt-2 text-muted-foreground">
                {canEdit ? 'Add one or import a CSV, or adjust your search and filters.' : 'Adjust your search and filters.'}
              </p>
            </div>
          )}

          <Pager
            page={pager.page}
            pageSize={pager.pageSize}
            count={items.length}
            hasNext={hasNext}
            onPageChange={pager.setPage}
            isLoading={pharmacies.isFetching}
            noun="pharmacies"
          />
        </CardContent>
      </Card>
    </div>
  )
}
