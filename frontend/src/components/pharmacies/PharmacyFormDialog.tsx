'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { Loader2, LocateOff, MapPin } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useDivisions, useUpazilas } from '@/lib/hooks/usePatients'
import {
  useAllDistricts,
  useCreatePharmacy,
  usePharmacy,
  useUpdatePharmacy,
} from '@/lib/hooks/usePharmacies'
import {
  PHARMACY_DISCIPLINES,
  PHARMACY_TYPES,
  type PharmacyDiscipline,
  type PharmacyInput,
} from '@/types/pharmacy'

// Leaflet touches `window`, so the map is client-only
const MapPicker = dynamic(() => import('./MapPicker'), {
  ssr: false,
  loading: () => <div className="h-[280px] w-full animate-pulse rounded-lg bg-muted" />,
})

const NONE = 'none'

const emptyForm: PharmacyInput = {
  name_en: '',
  name_bn: null,
  pharmacy_type: 'retail',
  disciplines: [],
  notes_en: null,
  notes_bn: null,
  address: null,
  district_id: null,
  upazila_id: null,
  latitude: null,
  longitude: null,
  phone: null,
  whatsapp: null,
  email: null,
  website_url: null,
  opening_hours: null,
  delivers: false,
  source_url: null,
  is_active: true,
}

const clean = (value: string | null) => {
  const trimmed = (value ?? '').trim()
  return trimmed === '' ? null : trimmed
}

function parseCoordinate(text: string, limit: number): number | null {
  if (text.trim() === '') return null
  const n = Number(text)
  return Number.isFinite(n) && Math.abs(n) <= limit ? n : null
}

interface PharmacyFormProps {
  initial: PharmacyInput
  editingId: number | null
  onDone: () => void
}

function PharmacyForm({ initial, editingId, onDone }: PharmacyFormProps) {
  const [form, setForm] = useState<PharmacyInput>(initial)
  const [latText, setLatText] = useState(initial.latitude?.toString() ?? '')
  const [lonText, setLonText] = useState(initial.longitude?.toString() ?? '')

  const { data: divisions } = useDivisions()
  const { districts } = useAllDistricts(divisions)
  const { data: upazilas } = useUpazilas(form.district_id)

  const create = useCreatePharmacy({ onSuccess: onDone })
  const update = useUpdatePharmacy({ onSuccess: onDone })
  const saving = create.isLoading || update.isLoading

  const set = <K extends keyof PharmacyInput>(key: K, value: PharmacyInput[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  const setPin = (lat: number | null, lon: number | null) => {
    setForm((current) => ({ ...current, latitude: lat, longitude: lon }))
    setLatText(lat === null ? '' : String(lat))
    setLonText(lon === null ? '' : String(lon))
  }

  const toggleDiscipline = (discipline: PharmacyDiscipline) =>
    set(
      'disciplines',
      form.disciplines.includes(discipline)
        ? form.disciplines.filter((d) => d !== discipline)
        : [...form.disciplines, discipline]
    )

  const district = districts.find((d) => d.id === form.district_id)
  const upazila = upazilas?.find((u) => u.id === form.upazila_id)
  const focus = upazila ?? district
  const fallbackCenter: [number, number] | null =
    focus?.latitude != null && focus?.longitude != null ? [focus.latitude, focus.longitude] : null

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.name_en.trim()) return toast.error('Enter the pharmacy name')
    if (form.disciplines.length === 0) return toast.error('Choose at least one discipline')
    if ((form.latitude === null) !== (form.longitude === null)) {
      return toast.error('Set both latitude and longitude, or clear both')
    }

    const payload: PharmacyInput = {
      ...form,
      name_en: form.name_en.trim(),
      name_bn: clean(form.name_bn),
      notes_en: clean(form.notes_en),
      notes_bn: clean(form.notes_bn),
      address: clean(form.address),
      phone: clean(form.phone),
      whatsapp: clean(form.whatsapp),
      email: clean(form.email),
      website_url: clean(form.website_url),
      opening_hours: clean(form.opening_hours),
      source_url: clean(form.source_url),
    }
    if (editingId !== null) update.mutate({ id: editingId, data: payload })
    else create.mutate(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="ph-name-en">Name (English) *</Label>
          <Input id="ph-name-en" value={form.name_en} onChange={(e) => set('name_en', e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ph-name-bn">Name (Bengali)</Label>
          <Input id="ph-name-bn" value={form.name_bn ?? ''} onChange={(e) => set('name_bn', e.target.value)} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="ph-type">Type *</Label>
          <Select value={form.pharmacy_type} onValueChange={(v) => set('pharmacy_type', v as PharmacyInput['pharmacy_type'])}>
            <SelectTrigger id="ph-type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PHARMACY_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Stocks *</legend>
          <div className="flex flex-wrap gap-x-4 gap-y-2 pt-1">
            {PHARMACY_DISCIPLINES.map((d) => (
              <label key={d.value} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4"
                  checked={form.disciplines.includes(d.value)}
                  onChange={() => toggleDiscipline(d.value)}
                />
                {d.label}
              </label>
            ))}
          </div>
        </fieldset>
      </div>

      <div className="space-y-4 rounded-lg border p-4">
        <h3 className="text-sm font-semibold">Location</h3>
        <div className="space-y-2">
          <Label htmlFor="ph-address">Address</Label>
          <Input id="ph-address" value={form.address ?? ''} onChange={(e) => set('address', e.target.value)} placeholder="House / road / area" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="ph-district">District</Label>
            <Select
              value={form.district_id ? String(form.district_id) : NONE}
              onValueChange={(v) => {
                set('district_id', v === NONE ? null : Number(v))
                set('upazila_id', null)
              }}
            >
              <SelectTrigger id="ph-district">
                <SelectValue placeholder="Select district" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>Not set</SelectItem>
                {districts.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    {d.name_en}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="ph-upazila">Upazila</Label>
            <Select
              value={form.upazila_id ? String(form.upazila_id) : NONE}
              onValueChange={(v) => set('upazila_id', v === NONE ? null : Number(v))}
              disabled={!form.district_id}
            >
              <SelectTrigger id="ph-upazila">
                <SelectValue placeholder="Select upazila" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>Not set</SelectItem>
                {(upazilas ?? []).map((u) => (
                  <SelectItem key={u.id} value={String(u.id)}>
                    {u.name_en}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <p className="mb-2 flex items-center gap-1.5 text-sm text-muted-foreground">
            <MapPin className="h-4 w-4" /> Click the map to drop the pin, then drag it to fine-tune.
            Choosing a district moves the map there.
          </p>
          <MapPicker
            latitude={form.latitude}
            longitude={form.longitude}
            onChange={setPin}
            fallbackCenter={fallbackCenter}
          />
        </div>

        <div className="grid items-end gap-4 sm:grid-cols-[1fr_1fr_auto]">
          <div className="space-y-2">
            <Label htmlFor="ph-lat">Latitude</Label>
            <Input
              id="ph-lat"
              inputMode="decimal"
              value={latText}
              onChange={(e) => {
                setLatText(e.target.value)
                set('latitude', parseCoordinate(e.target.value, 90))
              }}
              placeholder="23.7808"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ph-lon">Longitude</Label>
            <Input
              id="ph-lon"
              inputMode="decimal"
              value={lonText}
              onChange={(e) => {
                setLonText(e.target.value)
                set('longitude', parseCoordinate(e.target.value, 180))
              }}
              placeholder="90.4167"
            />
          </div>
          <Button type="button" variant="outline" onClick={() => setPin(null, null)} disabled={latText === '' && lonText === ''}>
            <LocateOff className="mr-2 h-4 w-4" />
            Clear pin
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Listings without a pin still appear in lists but not on the map or in &quot;near me&quot;.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="ph-phone">Phone</Label>
          <Input id="ph-phone" type="tel" value={form.phone ?? ''} onChange={(e) => set('phone', e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ph-whatsapp">WhatsApp</Label>
          <Input id="ph-whatsapp" type="tel" value={form.whatsapp ?? ''} onChange={(e) => set('whatsapp', e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ph-email">Email</Label>
          <Input id="ph-email" type="email" value={form.email ?? ''} onChange={(e) => set('email', e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ph-website">Website</Label>
          <Input id="ph-website" type="url" value={form.website_url ?? ''} onChange={(e) => set('website_url', e.target.value)} placeholder="https://" />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="ph-hours">Opening hours</Label>
          <Input id="ph-hours" value={form.opening_hours ?? ''} onChange={(e) => set('opening_hours', e.target.value)} placeholder="Sat–Thu 10:00–21:00, Fri closed" />
        </div>
        <label className="flex items-center gap-2 text-sm sm:col-span-2">
          <input type="checkbox" className="h-4 w-4" checked={form.delivers} onChange={(e) => set('delivers', e.target.checked)} />
          Delivers / sends by courier
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="ph-notes-en">Notes (English)</Label>
          <Textarea id="ph-notes-en" rows={3} value={form.notes_en ?? ''} onChange={(e) => set('notes_en', e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ph-notes-bn">Notes (Bengali)</Label>
          <Textarea id="ph-notes-bn" rows={3} value={form.notes_bn ?? ''} onChange={(e) => set('notes_bn', e.target.value)} />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="ph-source">Source URL</Label>
          <Input id="ph-source" value={form.source_url ?? ''} onChange={(e) => set('source_url', e.target.value)} placeholder="Where this information came from" />
        </div>
        {editingId !== null && (
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input type="checkbox" className="h-4 w-4" checked={form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
            Active (inactive listings are hidden from practitioners)
          </label>
        )}
      </div>

      <div className="flex justify-end gap-2 border-t pt-4">
        <Button type="button" variant="outline" onClick={onDone} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" disabled={saving}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId !== null ? 'Save changes' : 'Add pharmacy'}
        </Button>
      </div>
    </form>
  )
}

interface PharmacyFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null = add a new pharmacy */
  pharmacyId: number | null
}

export function PharmacyFormDialog({ open, onOpenChange, pharmacyId }: PharmacyFormDialogProps) {
  const detail = usePharmacy(pharmacyId, open)
  const initial: PharmacyInput | null =
    pharmacyId === null ? emptyForm : (detail.data ?? null)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{pharmacyId === null ? 'Add pharmacy' : 'Edit pharmacy'}</DialogTitle>
          <DialogDescription>
            Shared directory entry — visible to every practitioner. Add the source so it can be re-checked later.
          </DialogDescription>
        </DialogHeader>
        {initial === null ? (
          <div className="flex justify-center py-12">
            {detail.isError ? (
              <p className="text-sm text-red-600">Could not load this pharmacy.</p>
            ) : (
              <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            )}
          </div>
        ) : (
          // keyed so the form's state resets for each pharmacy / each opening
          <PharmacyForm
            key={pharmacyId ?? 'new'}
            initial={initial}
            editingId={pharmacyId}
            onDone={() => onOpenChange(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
