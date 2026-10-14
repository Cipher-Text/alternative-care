'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useInviteMember } from '@/lib/hooks/useTeam'
import { useTeamArea } from '@/lib/team/area'
import { RoleChecklist } from './RoleChecklist'
import type { TeamRole } from '@/types/team'

/** Add a staff member: they get an email with a link to set their own password. */
export function InviteMemberDialog({ roles, onClose }: { roles: TeamRole[]; onClose: () => void }) {
  const t = useTranslations('teamUi')
  const locale = useLocale()
  const { kind } = useTeamArea()
  const invite = useInviteMember()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [language, setLanguage] = useState<'en' | 'bn'>(locale === 'bn' ? 'bn' : 'en')
  const [roleIds, setRoleIds] = useState<string[]>([])

  const valid = email.includes('@') && fullName.trim().length >= 2 && roleIds.length > 0

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!valid) return
    try {
      await invite.mutateAsync({
        email: email.trim(),
        full_name: fullName.trim(),
        phone: phone.trim() || undefined,
        language,
        role_ids: roleIds,
      })
      onClose()
    } catch {
      // the hook shows the error
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>{t('invite.title')}</DialogTitle>
            <DialogDescription>{kind === 'platform' ? t('platform.inviteDescription') : t('invite.description')}</DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <Label htmlFor="invite-name">{t('invite.fullName')}</Label>
            <Input id="invite-name" value={fullName} onChange={(e) => setFullName(e.target.value)} maxLength={255} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="invite-email">{t('invite.email')}</Label>
            <Input id="invite-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="invite-phone">{t('invite.phone')}</Label>
              <Input id="invite-phone" value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={20} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-language">{t('invite.language')}</Label>
              <select
                id="invite-language"
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                value={language}
                onChange={(e) => setLanguage(e.target.value as 'en' | 'bn')}
              >
                <option value="en">English</option>
                <option value="bn">বাংলা</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t('invite.roles')}</Label>
            <RoleChecklist roles={roles} selected={roleIds} onChange={setRoleIds} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {t('cancel')}
            </Button>
            <Button type="submit" disabled={!valid || invite.isLoading}>
              {invite.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('invite.submit')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
