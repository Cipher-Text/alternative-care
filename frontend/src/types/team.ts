/** Mirrors app/modules/team/schemas.py */

export interface RoleBrief {
  id: string
  key: string
  name_en: string
  name_bn: string
  is_system: boolean
}

export interface TeamRole extends RoleBrief {
  based_on_role_id: string | null
  permissions: string[]
  member_count: number
  can_edit: boolean
  can_assign: boolean
}

export interface TeamPermission {
  key: string
  module: string
  description_en: string
  description_bn: string
  is_sensitive: boolean
  can_grant: boolean
}

export interface TeamMember {
  id: string
  email: string
  full_name: string
  phone: string | null
  is_active: boolean
  is_email_verified: boolean
  last_login_at: string | null
  is_you: boolean
  roles: RoleBrief[]
  can_manage: boolean
}

export interface RoleInput {
  name_en: string
  name_bn?: string
  permissions: string[]
  based_on_role_id?: string | null
  acknowledge_sensitive: boolean
}

export interface RoleUpdateInput {
  name_en?: string
  name_bn?: string
  permissions?: string[]
  acknowledge_sensitive: boolean
}

export interface MemberInviteInput {
  email: string
  full_name: string
  phone?: string
  language: 'en' | 'bn'
  role_ids: string[]
}

export type AuditLevel = 'all' | 'platform' | 'clinic'

export interface TeamAuditItem {
  id: string
  created_at: string
  action: string
  actor_name: string | null
  member_name: string | null
  role_name: string | null
  /** Platform audit view only: the clinic a change was made in */
  clinic_name?: string | null
  before: Record<string, unknown> | null
  after: Record<string, unknown> | null
}

export interface TeamAuditPage {
  items: TeamAuditItem[]
  total: number
}
