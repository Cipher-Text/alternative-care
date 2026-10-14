'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Loader2, UserPlus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useSetMemberActive, useTeamMembers, useTeamRoles } from '@/lib/hooks/useTeam'
import { InviteMemberDialog } from './InviteMemberDialog'
import { MemberRolesDialog } from './MemberRolesDialog'
import { roleName } from './roleNames'
import type { TeamMember } from '@/types/team'

/** The clinic's staff: who they are, what roles they hold, and (for people who can manage the team) changing that. */
export function MembersTab({ canManage }: { canManage: boolean }) {
  const t = useTranslations('teamUi')
  const locale = useLocale()
  const members = useTeamMembers()
  const roles = useTeamRoles()
  const setActive = useSetMemberActive()
  const [inviting, setInviting] = useState(false)
  const [editing, setEditing] = useState<TeamMember | null>(null)

  if (members.isLoading || roles.isLoading) {
    return (
      <div className="flex justify-center py-12" role="status" aria-label={t('loading')}>
        <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
      </div>
    )
  }
  if (members.isError || roles.isError) {
    return <p className="py-8 text-center text-sm text-red-600">{t('loadFailed')}</p>
  }

  const list = members.data ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">{t('members.intro')}</p>
        {canManage && (
          <Button onClick={() => setInviting(true)} className="shrink-0">
            <UserPlus className="mr-2 h-4 w-4" aria-hidden="true" />
            {t('members.add')}
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('members.person')}</TableHead>
                <TableHead>{t('members.roles')}</TableHead>
                <TableHead>{t('members.status')}</TableHead>
                {canManage && <TableHead className="text-right">{t('members.actions')}</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {list.map((m) => (
                <TableRow key={m.id} className={m.is_active ? undefined : 'opacity-60'}>
                  <TableCell>
                    <div className="font-medium">
                      {m.full_name}
                      {m.is_you && (
                        <Badge variant="outline" className="ml-2">
                          {t('members.you')}
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">{m.email}</div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {m.roles.map((r) => (
                        <Badge key={r.id} variant={r.is_system ? 'secondary' : 'outline'}>
                          {roleName(r, locale)}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={m.is_active ? 'default' : 'secondary'}>
                      {m.is_active ? t('members.active') : t('members.inactive')}
                    </Badge>
                    {m.is_active && !m.is_email_verified && !m.last_login_at && (
                      <div className="mt-1 text-xs text-muted-foreground">{t('members.invitePending')}</div>
                    )}
                  </TableCell>
                  {canManage && (
                    <TableCell className="text-right">
                      {m.can_manage ? (
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="sm" onClick={() => setEditing(m)}>
                            {t('members.editRoles')}
                          </Button>
                          {!m.is_you && (
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={setActive.isLoading}
                              onClick={() => setActive.mutate({ id: m.id, active: !m.is_active })}
                            >
                              {m.is_active ? t('members.deactivate') : t('members.activate')}
                            </Button>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">{t('members.cannotManage')}</span>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {inviting && <InviteMemberDialog roles={roles.data ?? []} onClose={() => setInviting(false)} />}
      {editing && <MemberRolesDialog member={editing} roles={roles.data ?? []} onClose={() => setEditing(null)} />}
    </div>
  )
}
