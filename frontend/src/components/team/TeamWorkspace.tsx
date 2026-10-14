'use client'

import { useTranslations } from 'next-intl'
import { ShieldAlert } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TeamAreaProvider, type TeamArea } from '@/lib/team/area'
import { ActivityTab } from './ActivityTab'
import { MembersTab } from './MembersTab'
import { RolesTab } from './RolesTab'

/** Staff, roles and the trail of changes, for a clinic's team or the platform's. The caller says who may look and who may change. */
export function TeamWorkspace({ area, canView, canManage }: { area: TeamArea; canView: boolean; canManage: boolean }) {
  const t = useTranslations('teamUi')
  const platform = area.kind === 'platform'

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 py-24 text-center">
        <ShieldAlert className="h-10 w-10 text-amber-500" aria-hidden="true" />
        <p className="text-gray-600 dark:text-gray-400">{platform ? t('platform.noAccess') : t('noAccess')}</p>
      </div>
    )
  }

  // A clinic cannot change its own team: it asks AltCare. Only the platform side (admin) carries the management actions.
  const subtitle = platform
    ? canManage ? t('platform.subtitleManage') : t('platform.subtitleRead')
    : area.byPlatform
      ? canManage ? t('byPlatform.subtitleManage') : t('byPlatform.subtitleRead')
      : t('subtitleRead')

  return (
    <TeamAreaProvider value={area}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{platform ? t('platform.title') : t('title')}</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">{subtitle}</p>
        </div>

        <Tabs defaultValue="members">
          <TabsList>
            <TabsTrigger value="members">{t('tabs.members')}</TabsTrigger>
            <TabsTrigger value="roles">{t('tabs.roles')}</TabsTrigger>
            <TabsTrigger value="activity">{t('tabs.activity')}</TabsTrigger>
          </TabsList>
          <TabsContent value="members" className="mt-4">
            <MembersTab canManage={canManage} />
          </TabsContent>
          <TabsContent value="roles" className="mt-4">
            <RolesTab canManage={canManage} />
          </TabsContent>
          <TabsContent value="activity" className="mt-4">
            <ActivityTab />
          </TabsContent>
        </Tabs>
      </div>
    </TeamAreaProvider>
  )
}
