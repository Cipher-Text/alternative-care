'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Search, Loader2, Stethoscope } from 'lucide-react'
import { usePublicSymptoms, usePublicSymptomSearch } from '@/lib/hooks/usePublicCatalog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

interface SymptomCardData {
  id: number
  name_en: string
  name_bn: string | null
  category: string | null
  matchedTerm?: string
}

function SymptomsDirectory() {
  const searchParams = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [debouncedQuery, setDebouncedQuery] = useState(query)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  const searchResults = usePublicSymptomSearch(debouncedQuery)
  const browseResults = usePublicSymptoms({ limit: 100 })

  const isSearching = debouncedQuery.trim().length > 0
  const { data, isLoading } = isSearching ? searchResults : browseResults

  const symptoms: SymptomCardData[] = useMemo(() => {
    if (!data) return []
    if (isSearching) {
      return (data as NonNullable<typeof searchResults.data>).map((result) => ({
        id: result.symptom.id,
        name_en: result.symptom.name_en,
        name_bn: result.symptom.name_bn,
        category: result.symptom.category,
        matchedTerm:
          result.matched_term !== result.symptom.name_en ? result.matched_term : undefined,
      }))
    }
    return (data as NonNullable<typeof browseResults.data>).map((item) => ({
      id: item.id,
      name_en: item.name_en,
      name_bn: item.name_bn,
      category: item.category,
    }))
  }, [data, isSearching])

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Symptom Directory</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          The global, admin-curated symptom catalog — search by name or common alias.
        </p>
      </div>

      <div className="relative max-w-lg mb-8">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search symptoms by name..."
          className="pl-9"
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </div>
      ) : symptoms.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {symptoms.map((symptom) => (
            <Card key={symptom.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">{symptom.name_en}</CardTitle>
                    {symptom.name_bn && <CardDescription>{symptom.name_bn}</CardDescription>}
                  </div>
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center shrink-0">
                    <Stethoscope className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {symptom.category && (
                  <Badge variant="outline" className="capitalize">
                    {symptom.category.replace(/_/g, ' ')}
                  </Badge>
                )}
                {symptom.matchedTerm && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    Also known as: <span className="font-medium">{symptom.matchedTerm}</span>
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Stethoscope className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold">No symptoms found</h3>
          <p className="text-muted-foreground mt-2">Try a different search term.</p>
        </div>
      )}
    </div>
  )
}

export default function PublicSymptomsPage() {
  return (
    <Suspense fallback={null}>
      <SymptomsDirectory />
    </Suspense>
  )
}
