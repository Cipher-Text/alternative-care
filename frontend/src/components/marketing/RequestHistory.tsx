'use client'

import { useTranslations } from 'next-intl'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useDateFormat } from '@/lib/i18n/date'
import { FbStatusBadge } from './FbStatusBadge'
import { PostLink } from './PostLink'
import type { FacebookRequest } from '@/types/marketing'

/** Past requests. The API returns the most recent 20 only, so there is no pager here. */
export function RequestHistory({ history }: { history: FacebookRequest[] }) {
  const t = useTranslations('marketingUi.history')
  const { fmt } = useDateFormat()

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{t('title')}</CardTitle>
      </CardHeader>
      <CardContent>
        {history.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">{t('empty')}</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('date')}</TableHead>
                  <TableHead>{t('status')}</TableHead>
                  <TableHead>{t('post')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="whitespace-nowrap">{fmt(r.created_at, 'MMM d, yyyy')}</TableCell>
                    <TableCell><FbStatusBadge status={r.status} /></TableCell>
                    <TableCell>
                      {r.post_url ? (
                        <PostLink url={r.post_url} />
                      ) : r.status === 'rejected' && r.reject_reason ? (
                        <span className="text-sm text-muted-foreground">{r.reject_reason}</span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {history.length >= 20 && <p className="pt-3 text-xs text-muted-foreground">{t("capNote")}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
