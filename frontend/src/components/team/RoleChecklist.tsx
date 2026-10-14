'use client'

import { useLocale, useTranslations } from 'next-intl'
import { roleName } from './roleNames'
import type { TeamRole } from '@/types/team'

/** Pick one or more roles. A role the signed-in person could not hand out (it carries permissions they lack) is shown but disabled. */
export function RoleChecklist({
  roles,
  selected,
  onChange,
}: {
  roles: TeamRole[]
  selected: string[]
  onChange: (ids: string[]) => void
}) {
  const t = useTranslations('teamUi')
  const locale = useLocale()

  const toggle = (id: string) => onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])

  return (
    <div className="space-y-2" role="group" aria-label={t('members.roles')}>
      {roles.map((r) => {
        const locked = !r.can_assign
        return (
          <label
            key={r.id}
            className={`flex items-start gap-3 rounded-lg border p-3 ${locked ? 'opacity-60' : 'cursor-pointer hover:bg-muted/50'}`}
          >
            <input
              type="checkbox"
              className="mt-1 h-4 w-4"
              checked={selected.includes(r.id)}
              disabled={locked}
              onChange={() => toggle(r.id)}
            />
            <span>
              <span className="font-medium">{roleName(r, locale)}</span>
              <span className="ml-2 text-xs text-muted-foreground">
                {r.is_system ? t('roles.system') : t('roles.custom')} · {t('roles.permissionCount', { count: r.permissions.length })}
              </span>
              {locked && <span className="block text-xs text-amber-700">{t('roles.cannotAssign')}</span>}
            </span>
          </label>
        )
      })}
    </div>
  )
}
