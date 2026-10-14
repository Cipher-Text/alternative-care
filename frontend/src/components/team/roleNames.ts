import type { RoleBrief } from '@/types/team'

/** A role's name in the user's language (system roles and clinic roles both carry both). */
export function roleName(role: Pick<RoleBrief, 'name_en' | 'name_bn'>, locale: string): string {
  return locale === 'bn' && role.name_bn ? role.name_bn : role.name_en
}
