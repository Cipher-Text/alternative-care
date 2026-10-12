'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Phone } from 'lucide-react'
import { useDirectoryRequests, useUpdateRequestStatus } from '@/lib/hooks/useDirectory'
import { useDateFormat } from '@/lib/i18n/date'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { RequestStatus } from '@/types/directory'

type Filter = 'all' | RequestStatus
const FILTERS: Filter[] = ['all', 'new', 'contacted', 'closed']

/** Patients' call-back requests. Personal data: shown one page at a time, no export. */
export function RequestsInbox() {
  const t = useTranslations('directoryAdminUi')
  const { fmt } = useDateFormat()
  const [filter, setFilter] = useState<Filter>('all')
  const pager = usePager(undefined, filter)
  const update = useUpdateRequestStatus()

  const { data, isLoading, isError } = useDirectoryRequests({
    status: filter === 'all' ? undefined : filter,
    limit: pager.pageSize + 1, // one extra row tells us whether a next page exists
    offset: pager.offset,
  })
  const { items, hasNext } = serverPage(data, pager.pageSize)

  const actionButton = (id: string, status: RequestStatus, label: string, variant: 'default' | 'outline' = 'outline') => (
    <Button
      size="sm"
      variant={variant}
      className="h-9"
      disabled={update.isLoading}
      onClick={() => update.mutate({ id, status })}
    >
      {label}
    </Button>
  )

  return (
    <section aria-labelledby="dir-requests-title" className="space-y-4">
      <div>
        <h2 id="dir-requests-title" className="text-lg font-semibold text-gray-900 dark:text-white">
          {t('requests.title')}
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t('requests.subtitle')}</p>
      </div>

      <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
        <TabsList className="h-auto flex-wrap">
          {FILTERS.map((f) => (
            <TabsTrigger key={f} value={f} className="min-h-9">{t(`requests.filter.${f}`)}</TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-2" aria-busy="true">
          {[0, 1, 2].map((i) => <div key={i} className="h-14 animate-pulse rounded-lg bg-muted" />)}
        </div>
      ) : isError ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            {filter === 'all' ? t('requests.emptyAll') : t('requests.emptyFiltered')}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('requests.col.patient')}</TableHead>
                  <TableHead>{t('requests.col.phone')}</TableHead>
                  <TableHead>{t('requests.col.preferred')}</TableHead>
                  <TableHead>{t('requests.col.message')}</TableHead>
                  <TableHead>{t('requests.col.received')}</TableHead>
                  <TableHead>{t('requests.col.status')}</TableHead>
                  <TableHead>{t('requests.col.action')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.patient_name}</TableCell>
                    <TableCell className="whitespace-nowrap">
                      <a
                        href={`tel:${r.patient_phone}`}
                        aria-label={t('requests.callPatient', { name: r.patient_name })}
                        className="inline-flex items-center gap-1.5 text-primary underline"
                      >
                        <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                        {r.patient_phone}
                      </a>
                    </TableCell>
                    <TableCell>{r.preferred_time || <span className="text-muted-foreground">{t('requests.noPreferred')}</span>}</TableCell>
                    <TableCell className="max-w-[280px] whitespace-pre-wrap break-words">
                      {r.message || <span className="text-muted-foreground">{t('requests.noMessage')}</span>}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {fmt(r.created_at, 'MMM d, yyyy h:mm a')}
                    </TableCell>
                    <TableCell>
                      <Badge variant={r.status === 'new' ? 'default' : 'outline'}>{t(`requests.status.${r.status}`)}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        {r.status === 'new' && actionButton(r.id, 'contacted', t('requests.markContacted'), 'default')}
                        {r.status !== 'closed' && actionButton(r.id, 'closed', t('requests.markClosed'))}
                        {r.status === 'closed' && actionButton(r.id, 'new', t('requests.reopen'))}
                      </div>
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
        noun={t('requests.noun')}
      />
    </section>
  )
}
