'use client'

import { useTranslations } from 'next-intl'
import { Mail, MessageSquare } from 'lucide-react'
import { useMessagingStatus } from '@/lib/hooks/useBilling'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

/** Which platform messaging providers are configured. Skeleton while loading, hidden if the call fails. */
export function MessagingProvidersCard({ enabled }: { enabled: boolean }) {
  const t = useTranslations('billingUi.admin.providers')
  const tc = useTranslations('billingUi.channel')
  const { data, isLoading, isError } = useMessagingStatus(enabled)

  if (isError) return null

  const rows = data
    ? ([
        { channel: 'sms' as const, icon: MessageSquare, ...data.sms },
        { channel: 'email' as const, icon: Mail, ...data.email },
      ])
    : []

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('title')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <div className="space-y-2" aria-hidden="true">
            <div className="h-9 animate-pulse rounded bg-muted" />
            <div className="h-9 animate-pulse rounded bg-muted" />
          </div>
        ) : (
          <ul className="space-y-2">
            {rows.map(({ channel, icon: Icon, provider, configured }) => (
              <li key={channel} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3">
                <span className="flex items-center gap-2 font-medium">
                  <Icon className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                  {tc(channel)}
                  {provider && <span className="font-normal text-muted-foreground">{provider}</span>}
                </span>
                <Badge variant={configured ? 'default' : 'outline'}>
                  {configured ? t('configured') : t('notConfigured')}
                </Badge>
              </li>
            ))}
          </ul>
        )}
        <p className="text-sm text-muted-foreground">{t('hint')}</p>
      </CardContent>
    </Card>
  )
}
