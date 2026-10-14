'use client'

import { useMemo, useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreateRole, useUpdateRole } from '@/lib/hooks/useTeam'
import { roleName } from './roleNames'
import type { TeamPermission, TeamRole } from '@/types/team'

// Everyday clinic work first, administration last
const MODULE_ORDER = ['tenants', 'users', 'plans', 'billing', 'content', 'catalogue', 'contact', 'marketing', 'roles', 'audit', 'dashboard', 'patients', 'health', 'appointments', 'visits', 'prescriptions', 'payments', 'library', 'identity', 'messaging', 'clinic', 'directory', 'content', 'marketing', 'ai', 'billing', 'team']

export type RoleEditorMode = { kind: 'create'; base: TeamRole | null } | { kind: 'edit'; role: TeamRole }

/** Create a clinic role (from scratch or as a copy of one) or change one. A permission the person editing does not hold
 * is shown but cannot be ticked: nobody can hand out more than they have (the server enforces it as well). */
export function RoleEditorDialog({
  mode,
  permissions,
  onClose,
}: {
  mode: RoleEditorMode
  permissions: TeamPermission[]
  onClose: () => void
}) {
  const t = useTranslations('teamUi')
  const locale = useLocale()
  const create = useCreateRole()
  const update = useUpdateRole()

  const original = mode.kind === 'edit' ? mode.role : mode.base
  const initialKeys = useMemo(() => new Set(original?.permissions ?? []), [original])
  const [nameEn, setNameEn] = useState(mode.kind === 'edit' ? mode.role.name_en : '')
  const [nameBn, setNameBn] = useState(mode.kind === 'edit' ? mode.role.name_bn : '')
  const [selected, setSelected] = useState<Set<string>>(new Set(initialKeys))
  const [acknowledged, setAcknowledged] = useState(false)

  const groups = useMemo(() => {
    const byModule = new Map<string, TeamPermission[]>()
    for (const p of permissions) byModule.set(p.module, [...(byModule.get(p.module) ?? []), p])
    const rank = (m: string) => (MODULE_ORDER.includes(m) ? MODULE_ORDER.indexOf(m) : MODULE_ORDER.length)
    return Array.from(byModule.entries()).sort((a, b) => rank(a[0]) - rank(b[0]))
  }, [permissions])

  const newSensitive = permissions.filter((p) => p.is_sensitive && selected.has(p.key) && !(mode.kind === 'edit' && initialKeys.has(p.key)))
  const busy = create.isLoading || update.isLoading
  const valid = nameEn.trim().length >= 2 && selected.size > 0 && (newSensitive.length === 0 || acknowledged)

  const toggle = (key: string) => {
    const next = new Set(selected)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    setSelected(next)
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!valid) return
    const permissionList = Array.from(selected)
    try {
      if (mode.kind === 'edit') {
        await update.mutateAsync({
          id: mode.role.id,
          data: { name_en: nameEn.trim(), name_bn: nameBn.trim() || undefined, permissions: permissionList, acknowledge_sensitive: acknowledged },
        })
      } else {
        await create.mutateAsync({
          name_en: nameEn.trim(),
          name_bn: nameBn.trim() || undefined,
          permissions: permissionList,
          based_on_role_id: mode.base?.id ?? null,
          acknowledge_sensitive: acknowledged,
        })
      }
      onClose()
    } catch {
      // the hook shows the error
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>{mode.kind === 'edit' ? t('editor.editTitle') : t('editor.createTitle')}</DialogTitle>
            <DialogDescription>
              {mode.kind === 'create' && mode.base
                ? t('editor.copyOf', { name: roleName(mode.base, locale) })
                : t('editor.description')}
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="role-name-en">{t('editor.nameEn')}</Label>
              <Input id="role-name-en" value={nameEn} onChange={(e) => setNameEn(e.target.value)} maxLength={100} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role-name-bn">{t('editor.nameBn')}</Label>
              <Input id="role-name-bn" value={nameBn} onChange={(e) => setNameBn(e.target.value)} maxLength={100} />
            </div>
          </div>

          <div className="space-y-4">
            <Label>{t('editor.permissions', { count: selected.size })}</Label>
            {groups.map(([module, items]) => (
              <fieldset key={module} className="space-y-1 rounded-lg border p-3">
                <legend className="px-1 text-sm font-semibold">{t(`modules.${module}`)}</legend>
                {items.map((p) => (
                  <label key={p.key} className={`flex items-start gap-3 py-1 ${p.can_grant ? 'cursor-pointer' : 'opacity-50'}`}>
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4"
                      checked={selected.has(p.key)}
                      // Already in the role: keep it editable so it can be removed; a new one needs the person to hold it
                      disabled={!p.can_grant && !selected.has(p.key)}
                      onChange={() => toggle(p.key)}
                    />
                    <span className="text-sm">
                      {locale === 'bn' ? p.description_bn : p.description_en}
                      {p.is_sensitive && (
                        <span className="ml-2 inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-900">
                          <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                          {t('editor.sensitive')}
                        </span>
                      )}
                      {!p.can_grant && <span className="block text-xs text-muted-foreground">{t('editor.youDoNotHold')}</span>}
                    </span>
                  </label>
                ))}
              </fieldset>
            ))}
          </div>

          {newSensitive.length > 0 && (
            <label className="flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
              <input type="checkbox" className="mt-1 h-4 w-4" checked={acknowledged} onChange={(e) => setAcknowledged(e.target.checked)} />
              <span>{t('editor.acknowledge', { count: newSensitive.length })}</span>
            </label>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {t('cancel')}
            </Button>
            <Button type="submit" disabled={!valid || busy}>
              {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
