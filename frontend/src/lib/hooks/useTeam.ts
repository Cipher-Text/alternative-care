import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { teamApi } from '@/lib/api/team'
import { errorMessage } from '@/lib/apiErrors'
import type { MemberInviteInput, RoleInput, RoleUpdateInput } from '@/types/team'

const keys = {
  members: ['team', 'members'] as const,
  roles: ['team', 'roles'] as const,
  permissions: ['team', 'permissions'] as const,
  audit: (params: { limit: number; offset: number }) => ['team', 'audit', params] as const,
}

export const useTeamMembers = () => useQuery(keys.members, () => teamApi.members(), { staleTime: 15000 })
export const useTeamRoles = () => useQuery(keys.roles, () => teamApi.roles(), { staleTime: 15000 })
export const useTeamPermissions = () => useQuery(keys.permissions, () => teamApi.permissions(), { staleTime: 60000 })
export const useTeamAudit = (params: { limit: number; offset: number }) =>
  useQuery(keys.audit(params), () => teamApi.audit(params), { keepPreviousData: true, staleTime: 15000 })

/** Every team change can alter who holds what, so all team data is refreshed together (and the user's own permissions, in
 * case they changed their own roles). */
function useTeamMutation<TInput, TOutput>(run: (input: TInput) => Promise<TOutput>, successKey: string) {
  const t = useTranslations('teamUi')
  const queryClient = useQueryClient()
  return useMutation(run, {
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

export const useCreateRole = () => useTeamMutation((data: RoleInput) => teamApi.createRole(data), 'saved')
export const useUpdateRole = () =>
  useTeamMutation((v: { id: string; data: RoleUpdateInput }) => teamApi.updateRole(v.id, v.data), 'saved')
export const useDeleteRole = () => useTeamMutation((id: string) => teamApi.deleteRole(id), 'roleDeleted')
export const useInviteMember = () => useTeamMutation((data: MemberInviteInput) => teamApi.invite(data), 'invited')
export const useSetMemberRoles = () =>
  useTeamMutation((v: { id: string; roleIds: string[] }) => teamApi.setRoles(v.id, v.roleIds), 'saved')
export const useSetMemberActive = () =>
  useTeamMutation((v: { id: string; active: boolean }) => teamApi.setActive(v.id, v.active), 'saved')
