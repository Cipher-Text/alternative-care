'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocale, useTranslations } from 'next-intl'
import { Search, Loader2, Pill } from 'lucide-react'
import { usePublicMedicines, usePublicMedicineSearch } from '@/lib/hooks/usePublicCatalog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Pager, clientPage, serverPage, usePager } from '@/components/shared/Pager'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { MedicalSystem, MedicineListItem, MedicineSearchResult } from '@/types/medicine'

const systems: MedicalSystem[] = ['homeopathy', 'ayurveda', 'unani', 'herbal']

const systemColor: Record<MedicalSystem, string> = {
  homeopathy: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  ayurveda: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  unani: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  herbal: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
}

function MedicinesDirectory() {
  const t = useTranslations('publicDirectoryUi')
  const locale = useLocale()
  const searchParams = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [debouncedQuery, setDebouncedQuery] = useState(query)
  const [system, setSystem] = useState<string>(searchParams.get('system') || 'all')

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  const systemFilter = system === 'all' ? undefined : (system as MedicalSystem)
  const isSearching = debouncedQuery.trim().length > 0
  const pager = usePager(12, [debouncedQuery, system])
  const searchResults = usePublicMedicineSearch(debouncedQuery, systemFilter)
  // Browsing pages on the server (one extra row tells us a next page exists); search results are
  // the top-ranked matches and are paged in the browser
  const browseResults = usePublicMedicines({
    system: systemFilter,
    limit: pager.pageSize + 1,
    offset: pager.offset,
  })
  const { isLoading } = isSearching ? searchResults : browseResults
  const searchPage = clientPage(isSearching ? searchResults.data : [], pager.page, pager.pageSize)
  const browsePage = serverPage(isSearching ? [] : browseResults.data, pager.pageSize)
  const medicines = useMemo<Array<MedicineListItem | MedicineSearchResult>>(
    () => (isSearching ? searchPage.items : browsePage.items),
    [isSearching, searchPage.items, browsePage.items]
  )
  const hasNext = isSearching ? searchPage.hasNext : browsePage.hasNext

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('medicines.title')}</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          {t('medicines.subtitle')}
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={t('medicines.searchLabel')}
            placeholder={t('medicines.searchPlaceholder')}
            className="pl-9"
          />
        </div>
        <Select value={system} onValueChange={setSystem}>
          <SelectTrigger aria-label={t('discipline')} className="sm:w-48">
            <SelectValue placeholder={t('discipline')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allDisciplines')}</SelectItem>
            {systems.map((s) => (
              <SelectItem key={s} value={s}>
                {t(`disciplines.${s}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </div>
      ) : medicines.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {medicines.map((medicine) => (
            <Card key={medicine.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">
                      {locale === 'bn' && medicine.name_bn ? medicine.name_bn : medicine.name_en}
                    </CardTitle>
                    {locale === 'bn'
                      ? medicine.name_bn && <CardDescription>{medicine.name_en}</CardDescription>
                      : medicine.name_bn && <CardDescription>{medicine.name_bn}</CardDescription>}
                  </div>
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center shrink-0">
                    <Pill className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className={systemColor[medicine.system]}>
                    {t(`disciplines.${medicine.system}`)}
                  </Badge>
                  {medicine.potency && <Badge variant="outline">{medicine.potency}</Badge>}
                  {medicine.category && (
                    <span className="text-xs text-muted-foreground">{medicine.category}</span>
                  )}
                </div>
                {'matched_alias' in medicine && medicine.matched_alias && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    {t('alsoKnownAs')} <span className="font-medium">{medicine.matched_alias}</span>
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Pill className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold">{t('medicines.emptyTitle')}</h3>
          <p className="text-muted-foreground mt-2">{t('medicines.emptyHint')}</p>
        </div>
      )}
      <Pager
        page={pager.page}
        pageSize={pager.pageSize}
        count={medicines.length}
        hasNext={hasNext}
        total={isSearching ? searchPage.total : undefined}
        onPageChange={pager.setPage}
        noun="medicines"
      />
    </div>
  )
}

export default function PublicMedicinesPage() {
  return (
    <Suspense fallback={null}>
      <MedicinesDirectory />
    </Suspense>
  )
}
