'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useSetMemberRoles } from '@/lib/hooks/useTeam'
import { RoleChecklist } from './RoleChecklist'
import type { TeamMember, TeamRole } from '@/types/team'

/** Change which roles a staff member holds. Their permissions are the combination of all of them. */
export function MemberRolesDialog({ member, roles, onClose }: { member: TeamMember; roles: TeamRole[]; onClose: () => void }) {
  const t = useTranslations('teamUi')
  const save = useSetMemberRoles()
  const [roleIds, setRoleIds] = useState<string[]>(member.roles.map((r) => r.id))

  const submit = async () => {
    try {
      await save.mutateAsync({ id: member.id, roleIds })
      onClose()
    } catch {
      // the hook shows the error
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t('memberRoles.title', { name: member.full_name })}</DialogTitle>
          <DialogDescription>{t('memberRoles.description')}</DialogDescription>
        </DialogHeader>
        <RoleChecklist roles={roles} selected={roleIds} onChange={setRoleIds} />
        {roleIds.length === 0 && <p className="text-xs text-amber-700">{t('memberRoles.atLeastOne')}</p>}
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t('cancel')}
          </Button>
          <Button onClick={submit} disabled={roleIds.length === 0 || save.isLoading}>
            {save.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {t('save')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
