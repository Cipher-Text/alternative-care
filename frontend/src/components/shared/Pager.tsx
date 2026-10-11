'use client'

import { useCallback, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/button'

export const DEFAULT_PAGE_SIZE = 20

/**
 * Page state for a list. Pass `resetKey` (e.g. the active filters and search text): whenever it
 * changes the list goes back to page 1, with no effect or manual reset calls needed.
 */
export function usePager(pageSize: number = DEFAULT_PAGE_SIZE, resetKey: unknown = '') {
  const key = JSON.stringify(resetKey)
  const [state, setState] = useState({ key, page: 1 })
  const page = state.key === key ? state.page : 1
  const setPage = useCallback((next: number) => setState({ key, page: Math.max(1, next) }), [key])
  const reset = useCallback(() => setState({ key, page: 1 }), [key])
  return { page, setPage, reset, pageSize, offset: (page - 1) * pageSize }
}

/**
 * Server-side paging helper. Ask the API for `pageSize + 1` rows (`fetchLimit`); the extra row only
 * tells us whether a next page exists, so no total count is needed.
 */
export function serverPage<T>(rows: T[] | undefined, pageSize: number) {
  const all = rows ?? []
  return { items: all.slice(0, pageSize), hasNext: all.length > pageSize }
}

/** Client-side paging helper for lists that are already fully loaded. */
export function clientPage<T>(rows: T[] | undefined, page: number, pageSize: number) {
  const all = rows ?? []
  const start = (page - 1) * pageSize
  return {
    items: all.slice(start, start + pageSize),
    hasNext: all.length > start + pageSize,
    total: all.length,
  }
}

interface PagerProps {
  page: number
  pageSize: number
  /** Rows shown on this page */
  count: number
  hasNext: boolean
  onPageChange: (page: number) => void
  /** Known only for client-side lists; enables "of N" */
  total?: number
  isLoading?: boolean
  noun?: string
}

/** Previous / Next controls with a "Showing a–b" summary. Hidden when everything fits on one page. */
export function Pager({
  page,
  pageSize,
  count,
  hasNext,
  onPageChange,
  total,
  isLoading,
  noun = 'results',
}: PagerProps) {
  const t = useTranslations('pager')
  if (page === 1 && !hasNext) return null

  // `noun` is an English plural ("patients", "pending tenants"); translate it when there is a key
  const nounKey = noun.replace(/\s+/g, '_')
  const nounText = t.has(`nouns.${nounKey}`) ? t(`nouns.${nounKey}`) : noun

  const from = count === 0 ? 0 : (page - 1) * pageSize + 1
  const to = (page - 1) * pageSize + count

  return (
    <nav
      aria-label={t('navLabel')}
      className="flex flex-wrap items-center justify-between gap-3 pt-4"
    >
      <p className="text-sm text-muted-foreground" aria-live="polite">
        {count === 0
          ? t('noMore', { noun: nounText })
          : total !== undefined
            ? t('showingOf', { from, to, total, noun: nounText })
            : t('showing', { from, to, noun: nounText })}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-10 sm:h-8" // thumb-sized on phones
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1 || isLoading}
        >
          <ChevronLeft className="mr-1 h-4 w-4" />
          {t('previous')}
        </Button>
        <span className="px-1 text-sm text-muted-foreground">{t('page', { page })}</span>
        <Button
          variant="outline"
          size="sm"
          className="h-10 sm:h-8"
          onClick={() => onPageChange(page + 1)}
          disabled={!hasNext || isLoading}
        >
          {t('next')}
          <ChevronRight className="ml-1 h-4 w-4" />
        </Button>
      </div>
    </nav>
  )
}
