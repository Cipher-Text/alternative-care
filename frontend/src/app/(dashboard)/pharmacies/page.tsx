'use client'

import { useTranslations } from 'next-intl'
import { useState } from 'react'
import dynamic from 'next/dynamic'
import { List, Loader2, LocateFixed, Map as MapIcon, Search, Store, X } from 'lucide-react'
import { useDivisions } from '@/lib/hooks/usePatients'
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue'
import { NEAR_ME_MESSAGE_KEYS, useNearMe } from '@/lib/hooks/useNearMe'
import { useAllDistricts, usePharmacies } from '@/lib/hooks/usePharmacies'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { PharmacyCard } from '@/components/pharmacies/PharmacyCard'
import { PharmacyDetailDialog } from '@/components/pharmacies/PharmacyDetailDialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  PHARMACY_DISCIPLINES,
  PHARMACY_TYPES,
  type PharmacyDiscipline,
  type PharmacyType,
} from '@/types/pharmacy'

// Leaflet touches `window`, so the map is client-only
const PharmacyResultsMap = dynamic(() => import('@/components/pharmacies/PharmacyResultsMap'), {
  ssr: false,
  loading: () => <div className="h-[520px] w-full animate-pulse rounded-lg bg-muted" />,
})

const RADII_KM = [5, 10, 25, 50, 100]
/** The API's page maximum; the map shows up to this many pins at once. */
const MAP_LIMIT = 500

export default function PharmaciesPage() {
  const tp = useTranslations('pages')
  const t = useTranslations('pharmUi')
  const [view, setView] = useState<'list' | 'map'>('list')
  const [searchTerm, setSearchTerm] = useState('')
  const [discipline, setDiscipline] = useState('all')
  const [type, setType] = useState('all')
  const [districtId, setDistrictId] = useState('all')
  const [delivers, setDelivers] = useState(false)
  const [radiusKm, setRadiusKm] = useState(10)
  const [detailId, setDetailId] = useState<number | null>(null)

  const nearMe = useNearMe()
  const debouncedSearch = useDebouncedValue(searchTerm.trim())
  const pager = usePager(undefined, [
    debouncedSearch, discipline, type, districtId, delivers, radiusKm, nearMe.coords,
  ])

  const { data: divisions } = useDivisions()
  const { districts } = useAllDistricts(divisions)
  const districtName = (id: number | null) => districts.find((d) => d.id === id)?.name_en

  const isMap = view === 'map'
  const filters = {
    search: debouncedSearch || undefined,
    discipline: discipline === 'all' ? undefined : (discipline as PharmacyDiscipline),
    pharmacy_type: type === 'all' ? undefined : (type as PharmacyType),
    district_id: districtId === 'all' ? undefined : Number(districtId),
    delivers: delivers || undefined,
    ...(nearMe.coords
      ? { lat: nearMe.coords.lat, lon: nearMe.coords.lon, radius_km: radiusKm }
      : {}),
    // List: one page at a time (+1 row to learn whether a next page exists). Map: every pin.
    limit: isMap ? MAP_LIMIT : pager.pageSize + 1,
    offset: isMap ? 0 : pager.offset,
  }
  const pharmacies = usePharmacies(filters)
  const { items, hasNext } = isMap
    ? { items: pharmacies.data ?? [], hasNext: false }
    : serverPage(pharmacies.data, pager.pageSize)

  const unpinned = isMap ? items.filter((p) => p.latitude === null).length : 0
  const hasFilters =
    Boolean(debouncedSearch) || discipline !== 'all' || type !== 'all' || districtId !== 'all' || delivers

  const nearMeMessageKey = NEAR_ME_MESSAGE_KEYS[nearMe.status]
  const nearMeMessage = nearMeMessageKey ? t(`nearMe.${nearMeMessageKey}`) : undefined
  const distanceOf = (id: number | null) => items.find((p) => p.id === id)?.distance_km ?? null

  const clearFilters = () => {
    setSearchTerm('')
    setDiscipline('all')
    setType('all')
    setDistrictId('all')
    setDelivers(false)
  }

  return (
    <div className="space-y-6">
      <PharmacyDetailDialog
        pharmacyId={detailId}
        onClose={() => setDetailId(null)}
        districtName={districtName(items.find((p) => p.id === detailId)?.district_id ?? null)}
        distanceKm={distanceOf(detailId)}
      />

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{tp('pharmaciesTitle')}</h1>
          <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">
            {tp('pharmaciesSubtitle')}
          </p>
        </div>
        <div className="flex gap-2" role="group" aria-label={t('view')}>
          <Button variant={view === 'list' ? 'default' : 'outline'} className="h-10" onClick={() => setView('list')} aria-pressed={view === 'list'}>
            <List className="mr-2 h-4 w-4" /> {t('list')}
          </Button>
          <Button variant={view === 'map' ? 'default' : 'outline'} className="h-10" onClick={() => setView('map')} aria-pressed={view === 'map'}>
            <MapIcon className="mr-2 h-4 w-4" /> {t('map')}
          </Button>
        </div>
      </div>

      <div className="space-y-3 rounded-lg border bg-card p-4">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <div className="relative md:col-span-2 lg:col-span-4">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label={t('searchPlaceholder')}
              placeholder={t('searchPlaceholder')}
              className="h-10 pl-9"
            />
          </div>

          <Select value={discipline} onValueChange={setDiscipline}>
            <SelectTrigger aria-label={t('discipline')} className="h-10">
              <SelectValue placeholder={t('discipline')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('allDisciplines')}</SelectItem>
              {PHARMACY_DISCIPLINES.map((d) => (
                <SelectItem key={d.value} value={d.value}>{t(`disciplines.${d.value}`)}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={type} onValueChange={setType}>
            <SelectTrigger aria-label={t('type')} className="h-10">
              <SelectValue placeholder={t('type')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('allTypes')}</SelectItem>
              {PHARMACY_TYPES.map((pt) => (
                <SelectItem key={pt.value} value={pt.value}>{t(`types.${pt.value}`)}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={districtId} onValueChange={setDistrictId}>
            <SelectTrigger aria-label={t('district')} className="h-10">
              <SelectValue placeholder={t('district')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('allDistricts')}</SelectItem>
              {districts.map((d) => (
                <SelectItem key={d.id} value={String(d.id)}>{d.name_en}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <label className="flex h-10 items-center gap-2 rounded-md border px-3 text-sm">
            <input type="checkbox" className="h-4 w-4" checked={delivers} onChange={(e) => setDelivers(e.target.checked)} />
            {t('deliversOnly')}
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2 border-t pt-3">
          {nearMe.coords ? (
            <>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1.5 text-sm text-blue-800 dark:bg-blue-950 dark:text-blue-200">
                <LocateFixed className="h-4 w-4" /> {t('within')}
              </span>
              <Select value={String(radiusKm)} onValueChange={(v) => setRadiusKm(Number(v))}>
                <SelectTrigger aria-label={t('searchRadius')} className="h-10 w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RADII_KM.map((r) => (
                    <SelectItem key={r} value={String(r)}>{t('radiusKm', { km: r })}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="ghost" className="h-10" onClick={nearMe.clear}>
                <X className="mr-1.5 h-4 w-4" /> {t('stopNearMe')}
              </Button>
            </>
          ) : (
            <Button variant="outline" className="h-10" onClick={nearMe.locate} disabled={nearMe.status === 'locating'}>
              {nearMe.status === 'locating' ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <LocateFixed className="mr-2 h-4 w-4" />
              )}
              {t('nearMeButton')}
            </Button>
          )}
          {hasFilters && (
            <Button variant="ghost" className="h-10" onClick={clearFilters}>
              {t('clearFilters')}
            </Button>
          )}
        </div>
        {nearMeMessage && (
          <p role="alert" className="text-sm text-amber-700 dark:text-amber-400">{nearMeMessage}</p>
        )}
        {nearMe.coords && (
          <p className="text-xs text-muted-foreground">
            {t('privacyNote')}
          </p>
        )}
      </div>

      {pharmacies.isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </div>
      ) : pharmacies.isError ? (
        <p className="py-12 text-center text-red-600">{t('loadError')}</p>
      ) : items.length === 0 ? (
        <div className="rounded-lg border bg-card py-14 text-center">
          <Store className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-lg font-semibold">{t('noneFound')}</h2>
          <p className="mx-auto mt-2 max-w-md text-muted-foreground">
            {nearMe.coords
              ? t('emptyNear', { km: radiusKm })
              : hasFilters
                ? t('emptyFiltered')
                : t('emptyDirectory')}
          </p>
        </div>
      ) : isMap ? (
        <div className="space-y-2">
          <PharmacyResultsMap pharmacies={items} you={nearMe.coords} onOpenDetails={setDetailId} />
          <p className="text-sm text-muted-foreground" aria-live="polite">
            {t('onTheMap', { count: items.length - unpinned })}
            {unpinned > 0 && ` · ${t('withoutPin', { count: unpinned })}`}
            {items.length >= MAP_LIMIT && ` · ${t('showingFirst', { count: MAP_LIMIT })}`}
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {items.map((pharmacy) => (
              <PharmacyCard
                key={pharmacy.id}
                pharmacy={pharmacy}
                districtName={districtName(pharmacy.district_id)}
                onOpenDetails={setDetailId}
              />
            ))}
          </div>
          <Pager
            page={pager.page}
            pageSize={pager.pageSize}
            count={items.length}
            hasNext={hasNext}
            onPageChange={pager.setPage}
            isLoading={pharmacies.isFetching}
            noun="pharmacies"
          />
        </>
      )}
    </div>
  )
}
