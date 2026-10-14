'use client'

import { useTranslations } from 'next-intl'
import { ShieldAlert } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useCan } from '@/lib/auth/permissions'
import { ActivityTab } from '@/components/team/ActivityTab'
import { MembersTab } from '@/components/team/MembersTab'
import { RolesTab } from '@/components/team/RolesTab'

/** Team: the clinic's staff, the roles they hold, and the trail of changes. Seeing it needs `team.read`, changing it `team.manage`. */
export default function TeamPage() {
  const t = useTranslations('teamUi')
  const { can } = useCan()

  if (!can('team.read')) {
    return (
      <div className="flex flex-col items-center gap-3 py-24 text-center">
        <ShieldAlert className="h-10 w-10 text-amber-500" aria-hidden="true" />
        <p className="text-gray-600 dark:text-gray-400">{t('noAccess')}</p>
      </div>
    )
  }
  const canManage = can('team.manage')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">{canManage ? t('subtitleManage') : t('subtitleRead')}</p>
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
  )
}
