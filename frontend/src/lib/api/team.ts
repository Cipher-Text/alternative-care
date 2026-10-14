import apiClient from './client'
import type {
  MemberInviteInput,
  RoleInput,
  RoleUpdateInput,
  TeamAuditPage,
  TeamMember,
  TeamPermission,
  TeamRole,
} from '@/types/team'

export const teamApi = {
  permissions: async (): Promise<TeamPermission[]> => (await apiClient.get('/team/permissions')).data,
  roles: async (): Promise<TeamRole[]> => (await apiClient.get('/team/roles')).data,
  createRole: async (data: RoleInput): Promise<TeamRole> => (await apiClient.post('/team/roles', data)).data,
  updateRole: async (id: string, data: RoleUpdateInput): Promise<TeamRole> =>
    (await apiClient.patch(`/team/roles/${id}`, data)).data,
  deleteRole: async (id: string): Promise<void> => {
    await apiClient.delete(`/team/roles/${id}`)
  },
  members: async (): Promise<TeamMember[]> => (await apiClient.get('/team/members')).data,
  invite: async (data: MemberInviteInput): Promise<TeamMember> => (await apiClient.post('/team/members', data)).data,
  setRoles: async (id: string, role_ids: string[]): Promise<TeamMember> =>
    (await apiClient.put(`/team/members/${id}/roles`, { role_ids })).data,
  setActive: async (id: string, is_active: boolean): Promise<TeamMember> =>
    (await apiClient.patch(`/team/members/${id}/status`, { is_active })).data,
  audit: async (params: { limit: number; offset: number }): Promise<TeamAuditPage> =>
    (await apiClient.get('/team/audit', { params })).data,
}
