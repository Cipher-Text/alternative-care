'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useTeamAudit } from '@/lib/hooks/useTeam'
import { useTeamArea } from '@/lib/team/area'
import type { AuditLevel, TeamAuditItem } from '@/types/team'

const PAGE = 20
const KNOWN = ['role_created', 'role_updated', 'role_deleted', 'roles_assigned', 'member_invited', 'member_deactivated', 'member_activated']

function list(value: unknown): string {
  return Array.isArray(value) ? value.join(', ') : ''
}

/** Who changed which role or access, and when: the clinic's own audit trail. */
export function ActivityTab() {
  const t = useTranslations('teamUi')
  const locale = useLocale()
  const { kind, byPlatform } = useTeamArea()
  const [offset, setOffset] = useState(0)
  const [level, setLevel] = useState<AuditLevel>('all')
  const audit = useTeamAudit({ limit: PAGE, offset, level: kind === 'platform' ? level : undefined })

  if (audit.isLoading) {
    return (
      <div className="flex justify-center py-12" role="status" aria-label={t('loading')}>
        <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
      </div>
    )
  }
  if (audit.isError) return <p className="py-8 text-center text-sm text-red-600">{t('loadFailed')}</p>

  const items = audit.data?.items ?? []
  const total = audit.data?.total ?? 0

  const describe = (a: TeamAuditItem): string => {
    const key = KNOWN.includes(a.action) ? a.action : 'other'
    return t(`activity.actions.${key}`, {
      actor: a.actor_name ?? t('activity.someone'),
      member: a.member_name ?? '',
      role: a.role_name ?? '',
    })
  }

  const detail = (a: TeamAuditItem): string | null => {
    if (a.action === 'roles_assigned') return `${list(a.before?.roles)} → ${list(a.after?.roles)}`
    if (a.action === 'role_updated' && a.before && a.after) {
      const before = new Set((a.before.permissions as string[]) ?? [])
      const after = new Set((a.after.permissions as string[]) ?? [])
      const added = [...after].filter((k) => !before.has(k))
      const removed = [...before].filter((k) => !after.has(k))
      const parts = []
      if (added.length) parts.push(`+ ${added.join(', ')}`)
      if (removed.length) parts.push(`− ${removed.join(', ')}`)
      return parts.join('   ') || null
    }
    return null
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">{byPlatform ? t('byPlatform.activityIntro') : kind === 'platform' ? t('platform.activityIntro') : t('activity.intro')}</p>
        {kind === 'platform' && (
          <select
            aria-label={t('activity.levelAll')}
            className="h-9 rounded-md border bg-background px-3 text-sm"
            value={level}
            onChange={(e) => {
              setLevel(e.target.value as AuditLevel)
              setOffset(0)
            }}
          >
            <option value="all">{t('activity.levelAll')}</option>
            <option value="platform">{t('activity.levelPlatform')}</option>
            <option value="clinic">{t('activity.levelClinic')}</option>
          </select>
        )}
      </div>
      <Card>
        <CardContent className="divide-y p-0">
          {items.length === 0 && <p className="p-6 text-center text-sm text-muted-foreground">{t('activity.empty')}</p>}
          {items.map((a) => (
            <div key={a.id} className="px-4 py-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="text-sm font-medium">
                  {describe(a)}
                  {a.clinic_name && <span className="ml-1 font-normal text-muted-foreground">{t('activity.inClinic', { clinic: a.clinic_name })}</span>}
                </span>
                <time className="text-xs text-muted-foreground" dateTime={a.created_at}>
                  {new Date(a.created_at).toLocaleString(locale === 'bn' ? 'bn-BD' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' })}
                </time>
              </div>
              {detail(a) && <p className="mt-1 break-words font-mono text-xs text-muted-foreground">{detail(a)}</p>}
            </div>
          ))}
        </CardContent>
      </Card>
      {total > PAGE && (
        <div className="flex items-center justify-between">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
            {t('activity.newer')}
          </Button>
          <span className="text-xs text-muted-foreground">
            {offset + 1}–{Math.min(offset + PAGE, total)} / {total}
          </span>
          <Button variant="outline" size="sm" disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>
            {t('activity.older')}
          </Button>
        </div>
      )}
    </div>
  )
}
