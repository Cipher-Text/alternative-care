import apiClient from './client'
import type {
  AuditLevel,
  MemberInviteInput,
  RoleInput,
  RoleUpdateInput,
  TeamAuditPage,
  TeamMember,
  TeamPermission,
  TeamRole,
} from '@/types/team'

/** The same endpoints exist under two prefixes: a clinic's own team (`/team`) and the platform's (`/admin/staff`). */
export function createTeamApi(base: string) {
  return {
    permissions: async (): Promise<TeamPermission[]> => (await apiClient.get(`${base}/permissions`)).data,
    roles: async (): Promise<TeamRole[]> => (await apiClient.get(`${base}/roles`)).data,
    createRole: async (data: RoleInput): Promise<TeamRole> => (await apiClient.post(`${base}/roles`, data)).data,
    updateRole: async (id: string, data: RoleUpdateInput): Promise<TeamRole> =>
      (await apiClient.patch(`${base}/roles/${id}`, data)).data,
    deleteRole: async (id: string): Promise<void> => {
      await apiClient.delete(`${base}/roles/${id}`)
    },
    members: async (): Promise<TeamMember[]> => (await apiClient.get(`${base}/members`)).data,
    invite: async (data: MemberInviteInput): Promise<TeamMember> => (await apiClient.post(`${base}/members`, data)).data,
    setRoles: async (id: string, role_ids: string[]): Promise<TeamMember> =>
      (await apiClient.put(`${base}/members/${id}/roles`, { role_ids })).data,
    setActive: async (id: string, is_active: boolean): Promise<TeamMember> =>
      (await apiClient.patch(`${base}/members/${id}/status`, { is_active })).data,
    audit: async (params: { limit: number; offset: number; level?: AuditLevel }): Promise<TeamAuditPage> =>
      (await apiClient.get(`${base}/audit`, { params })).data,
  }
}

export type TeamApi = ReturnType<typeof createTeamApi>

export const clinicTeamApi = createTeamApi('/team')
export const platformTeamApi = createTeamApi('/admin/staff')
