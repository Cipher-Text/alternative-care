'use client'

import { useMemo, useState } from 'react'
import { BadgeCheck, ExternalLink, GraduationCap, Loader2, Search } from 'lucide-react'
import { usePublicInstitutions } from '@/lib/hooks/usePublicCatalog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Discipline } from '@/types/institution'

const disciplines: Array<{ value: Discipline; label: string }> = [
  { value: 'homeopathy', label: 'Homeopathy' },
  { value: 'ayurveda', label: 'Ayurveda' },
  { value: 'unani', label: 'Unani' },
  { value: 'herbal', label: 'Herbal' },
]

export default function PublicInstitutionsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [disciplineFilter, setDisciplineFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const { data: institutions, isLoading } = usePublicInstitutions({
    discipline: disciplineFilter === 'all' ? undefined : (disciplineFilter as Discipline),
    institution_type: typeFilter === 'all' ? undefined : (typeFilter as 'government' | 'private'),
    limit: 500,
  })

  const filtered = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    if (!term) return institutions || []

    return (institutions || []).filter((institution) =>
      [institution.name_en, institution.name_bn || '', institution.location || '']
        .some((value) => value.toLowerCase().includes(term))
    )
  }, [institutions, searchTerm])

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Institution Directory
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Colleges and institutes teaching Homeopathy, Ayurveda, Unani, and Herbal Medicine.
          Admin-curated and cross-checked against issuing boards where possible.
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-3 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search name or location"
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

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((institution) => (
            <Card key={institution.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center shrink-0">
                    <GraduationCap className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-base leading-snug">{institution.name_en}</CardTitle>
                    {institution.location && (
                      <CardDescription>{institution.location}</CardDescription>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline" className="capitalize">
                    {institution.institution_type}
                  </Badge>
                  {institution.disciplines.map((d) => (
                    <Badge key={d} variant="secondary" className="capitalize">
                      {d}
                    </Badge>
                  ))}
                  {institution.is_verified && (
                    <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      <BadgeCheck className="h-3 w-3 mr-1" />
                      Verified
                    </Badge>
                  )}
                </div>
                {institution.courses_offered && (
                  <p className="text-sm text-muted-foreground">
                    Courses: {institution.courses_offered}
                  </p>
                )}
                {institution.source_url && (
                  <Button asChild size="sm" variant="ghost" className="px-0">
                    <a href={institution.source_url} target="_blank" rel="noreferrer">
                      Source <ExternalLink className="h-3.5 w-3.5 ml-1" />
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <GraduationCap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold">No institutions found</h3>
          <p className="text-muted-foreground mt-2">Try a different search or filter.</p>
        </div>
      )}
    </div>
  )
}
