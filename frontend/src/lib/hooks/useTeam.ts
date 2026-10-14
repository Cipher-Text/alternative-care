import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { useTeamArea } from '@/lib/team/area'
import type { TeamApi as TeamApiType } from '@/lib/api/team'
import { errorMessage } from '@/lib/apiErrors'
import type { AuditLevel, MemberInviteInput, RoleInput, RoleUpdateInput } from '@/types/team'

const keys = (area: string) => ({
  members: ['team', area, 'members'] as const,
  roles: ['team', area, 'roles'] as const,
  permissions: ['team', area, 'permissions'] as const,
  audit: (params: { limit: number; offset: number; level?: AuditLevel }) => ['team', area, 'audit', params] as const,
})

export function useTeamMembers() {
  const { key, api } = useTeamArea()
  return useQuery(keys(key).members, () => api.members(), { staleTime: 15000 })
}
export function useTeamRoles() {
  const { key, api } = useTeamArea()
  return useQuery(keys(key).roles, () => api.roles(), { staleTime: 15000 })
}
export function useTeamPermissions() {
  const { key, api } = useTeamArea()
  return useQuery(keys(key).permissions, () => api.permissions(), { staleTime: 60000 })
}
export function useTeamAudit(params: { limit: number; offset: number; level?: AuditLevel }) {
  const { key, api } = useTeamArea()
  return useQuery(keys(key).audit(params), () => api.audit(params), { keepPreviousData: true, staleTime: 15000 })
}

/** Every team change can alter who holds what, so all team data is refreshed together (and the user's own permissions, in
 * case they changed their own roles). */
function useTeamMutation<TInput, TOutput>(run: (api: TeamApiType, input: TInput) => Promise<TOutput>, successKey: string) {
  const t = useTranslations('teamUi')
  const queryClient = useQueryClient()
  const { api } = useTeamArea()
  return useMutation((input: TInput) => run(api, input), {
    onSuccess: () => {
      queryClient.invalidateQueries(['team'])
      queryClient.invalidateQueries(['auth', 'permissions'])
      toast.success(t(successKey))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('failed')))
    },
  })
}

export const useCreateRole = () => useTeamMutation((api, data: RoleInput) => api.createRole(data), 'saved')
export const useUpdateRole = () =>
  useTeamMutation((api, v: { id: string; data: RoleUpdateInput }) => api.updateRole(v.id, v.data), 'saved')
export const useDeleteRole = () => useTeamMutation((api, id: string) => api.deleteRole(id), 'roleDeleted')
export const useInviteMember = () => useTeamMutation((api, data: MemberInviteInput) => api.invite(data), 'invited')
export const useSetMemberRoles = () =>
  useTeamMutation((api, v: { id: string; roleIds: string[] }) => api.setRoles(v.id, v.roleIds), 'saved')
export const useSetMemberActive = () =>
  useTeamMutation((api, v: { id: string; active: boolean }) => api.setActive(v.id, v.active), 'saved')
