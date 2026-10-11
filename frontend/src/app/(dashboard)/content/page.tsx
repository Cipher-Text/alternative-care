'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Newspaper, Plus, Video } from 'lucide-react'
import { useArticles } from '@/lib/hooks/useArticles'
import { useAuthStore } from '@/store/authStore'
import { useDateFormat } from '@/lib/i18n/date'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { ArticleStatusBadge, OverdueBadge } from '@/components/content/ArticleStatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { ArticleStatus } from '@/types/article'

type Filter = 'all' | ArticleStatus
const FILTERS: Filter[] = ['all', 'draft', 'in_review', 'published']

export default function ContentPage() {
  const t = useTranslations('contentAdminUi')
  const locale = useLocale()
  const { fmt } = useDateFormat()
  const isAdmin = useAuthStore((s) => s.user?.role === 'admin')
  const [filter, setFilter] = useState<Filter>('all')
  const pager = usePager(undefined, filter)

  const { data, isLoading, isError } = useArticles({
    status: filter === 'all' ? undefined : filter,
    limit: pager.pageSize + 1, // one extra row tells us whether a next page exists
    offset: pager.offset,
  })
  const { items, hasNext } = serverPage(data, pager.pageSize)

  const titleOf = (a: { title_en: string | null; title_bn: string | null }) =>
    (locale === 'bn' ? a.title_bn || a.title_en : a.title_en || a.title_bn) || t('untitled')

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
          <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">
            {isAdmin ? t('subtitleAdmin') : t('subtitleDoctor')}
          </p>
        </div>
        <Button asChild className="h-10">
          <Link href="/content/new">
            <Plus className="mr-2 h-4 w-4" /> {t('newArticle')}
          </Link>
        </Button>
      </div>

      <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
        <TabsList className="h-auto flex-wrap">
          {FILTERS.map((f) => (
            <TabsTrigger key={f} value={f} className="min-h-9">
              {t(`filter.${f}`)}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-2" aria-busy="true">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : isError ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Newspaper className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
            <p className="text-muted-foreground">
              {filter === 'all' ? t('emptyAll') : t('emptyFiltered')}
            </p>
            {filter === 'all' && (
              <Button asChild>
                <Link href="/content/new">{t('newArticle')}</Link>
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('col.title')}</TableHead>
                  {isAdmin && <TableHead>{t('col.author')}</TableHead>}
                  <TableHead>{t('col.discipline')}</TableHead>
                  <TableHead>{t('col.status')}</TableHead>
                  <TableHead>{t('col.updated')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="max-w-[320px] font-medium">
                      <Link href={`/content/${a.id}`} className="flex items-center gap-2 hover:underline">
                        {a.kind === 'video' ? (
                          <Video className="h-4 w-4 shrink-0 text-muted-foreground" aria-label={t('kind.video')} />
                        ) : (
                          <Newspaper className="h-4 w-4 shrink-0 text-muted-foreground" aria-label={t('kind.article')} />
                        )}
                        <span className="truncate">{titleOf(a)}</span>
                      </Link>
                    </TableCell>
                    {isAdmin && <TableCell>{a.author_name}</TableCell>}
                    <TableCell>{t(`discipline.${a.discipline}`)}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        <ArticleStatusBadge status={a.status} />
                        {a.review_overdue && <OverdueBadge />}
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {fmt(a.updated_at || a.created_at, 'MMM d, yyyy')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Pager
        page={pager.page}
        pageSize={pager.pageSize}
        count={items.length}
        hasNext={hasNext}
        onPageChange={pager.setPage}
        isLoading={isLoading}
        noun={t('articlesNoun')}
      />
    </div>
  )
}
