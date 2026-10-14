'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Copy, Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useDeleteRole, useTeamPermissions, useTeamRoles } from '@/lib/hooks/useTeam'
import { useTeamArea } from '@/lib/team/area'
import { RoleEditorDialog, type RoleEditorMode } from './RoleEditorDialog'
import { roleName } from './roleNames'

/** The roles a clinic can use: the built-in ones (read only) and its own. Copying a built-in role is the usual way to start one. */
export function RolesTab({ canManage }: { canManage: boolean }) {
  const t = useTranslations('teamUi')
  const locale = useLocale()
  const { kind, byPlatform } = useTeamArea()
  const roles = useTeamRoles()
  const permissions = useTeamPermissions()
  const remove = useDeleteRole()
  const [editor, setEditor] = useState<RoleEditorMode | null>(null)

  if (roles.isLoading || permissions.isLoading) {
    return (
      <div className="flex justify-center py-12" role="status" aria-label={t('loading')}>
        <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
      </div>
    )
  }
  if (roles.isError || permissions.isError) {
    return <p className="py-8 text-center text-sm text-red-600">{t('loadFailed')}</p>
  }

  const labels = new Map((permissions.data ?? []).map((p) => [p.key, locale === 'bn' ? p.description_bn : p.description_en]))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">{byPlatform ? t('byPlatform.rolesIntro') : kind === 'platform' ? t('platform.rolesIntro') : t('roles.intro')}</p>
        {canManage && (
          <Button onClick={() => setEditor({ kind: 'create', base: null })} className="shrink-0">
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
            {t('roles.create')}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {(roles.data ?? []).map((r) => (
          <Card key={r.id}>
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center gap-2 text-lg">
                {roleName(r, locale)}
                <Badge variant={r.is_system ? 'secondary' : 'outline'}>{r.is_system ? t('roles.system') : t('roles.custom')}</Badge>
              </CardTitle>
              <CardDescription>
                {t('roles.members', { count: r.member_count })} · {t('roles.permissionCount', { count: r.permissions.length })}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <details>
                <summary className="cursor-pointer text-sm text-emerald-700">{t('roles.showPermissions')}</summary>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                  {r.permissions.map((key) => (
                    <li key={key}>{labels.get(key) ?? key}</li>
                  ))}
                </ul>
              </details>
              {canManage && (
                <div className="flex flex-wrap gap-2">
                  {r.can_assign && (
                    <Button variant="outline" size="sm" onClick={() => setEditor({ kind: 'create', base: r })}>
                      <Copy className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
                      {t('roles.copy')}
                    </Button>
                  )}
                  {r.can_edit && (
                    <Button variant="outline" size="sm" onClick={() => setEditor({ kind: 'edit', role: r })}>
                      <Pencil className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
                      {t('roles.edit')}
                    </Button>
                  )}
                  {r.can_edit && (
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={r.member_count > 0 || remove.isLoading}
                      title={r.member_count > 0 ? t('roles.deleteBlocked') : undefined}
                      onClick={() => {
                        if (window.confirm(t('roles.deleteConfirm', { name: roleName(r, locale) }))) remove.mutate(r.id)
                      }}
                    >
                      <Trash2 className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
                      {t('roles.delete')}
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {editor && <RoleEditorDialog mode={editor} permissions={permissions.data ?? []} onClose={() => setEditor(null)} />}
    </div>
  )
}
