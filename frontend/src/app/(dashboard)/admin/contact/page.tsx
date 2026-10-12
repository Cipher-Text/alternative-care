'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2, ShieldAlert } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useDateFormat } from '@/lib/i18n/date'
import { useContactMessages, useSetContactStatus } from '@/lib/hooks/useContactInbox'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { ContactTopic } from '@/types/contact'

const PAGE_SIZE = 20
const TOPIC_KEY: Record<ContactTopic, string> = {
  general: 'topicGeneral',
  enterprise: 'topicEnterprise',
  billing: 'topicBilling',
  report_profile: 'topicReportProfile',
  other: 'topicOther',
}

/** Platform admin: messages from the public contact form. Admin only. */
export default function AdminContactPage() {
  const t = useTranslations('publicContactUi.admin')
  const user = useAuthStore((s) => s.user)
  const { fmt } = useDateFormat()
  const [status, setStatus] = useState<'new' | 'handled'>('new')
  const pager = usePager(PAGE_SIZE, status)
  const messages = useContactMessages({ status, limit: PAGE_SIZE + 1, offset: pager.offset })
  const setMessageStatus = useSetContactStatus()
  const { items, hasNext } = serverPage(messages.data, PAGE_SIZE)

  if (user && user.role !== 'admin') {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 p-6">
          <ShieldAlert className="h-5 w-5 text-red-500" aria-hidden="true" />
          {t('adminOnly')}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>

      <Tabs value={status} onValueChange={(v) => setStatus(v as 'new' | 'handled')}>
        <TabsList>
          <TabsTrigger value="new">{t('tabNew')}</TabsTrigger>
          <TabsTrigger value="handled">{t('tabHandled')}</TabsTrigger>
        </TabsList>
      </Tabs>

      {messages.isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
        </div>
      ) : messages.error ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : items.length === 0 && pager.page === 1 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">{t('empty')}</p>
      ) : (
        <>
          <ul className="space-y-3">
            {items.map((m) => (
              <li key={m.id}>
                <Card>
                  <CardContent className="space-y-3 p-4">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <Badge variant="secondary">{t(TOPIC_KEY[m.topic])}</Badge>
                      <span className="font-medium text-gray-900 dark:text-white">{m.name}</span>
                      {m.email && <a href={`mailto:${m.email}`} className="text-sm text-emerald-700 underline dark:text-emerald-400">{m.email}</a>}
                      {m.phone && <a href={`tel:${m.phone}`} className="text-sm text-emerald-700 underline dark:text-emerald-400">{m.phone}</a>}
                      <span className="ml-auto text-xs text-muted-foreground">{fmt(m.created_at, 'MMM d, yyyy h:mm a')}</span>
                    </div>
                    {m.organisation && <p className="text-sm text-muted-foreground">{t('organisation', { name: m.organisation })}</p>}
                    <p className="whitespace-pre-line break-words text-sm text-gray-800 dark:text-gray-200">{m.message}</p>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={setMessageStatus.isLoading}
                      onClick={() => setMessageStatus.mutate({ id: m.id, status: m.status === 'new' ? 'handled' : 'new' })}
                    >
                      {m.status === 'new' ? t('markHandled') : t('reopen')}
                    </Button>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
          <Pager page={pager.page} pageSize={PAGE_SIZE} count={items.length} hasNext={hasNext} onPageChange={pager.setPage} isLoading={messages.isFetching} noun="messages" />
        </>
      )}
    </div>
  )
}
