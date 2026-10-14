import { useMemo } from 'react'
import { useQuery } from 'react-query'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/authStore'

/**
 * What the signed-in user may do, as the server computed it (GET /auth/me/permissions: the union of the permissions
 * of their roles; ADR 010). The UI only uses it to show or hide controls: the server checks every request itself.
 * Loaded once by the dashboard layout, which holds the page until it arrives, so `can()` never reads an empty list.
 */
export function usePermissions() {
  const userId = useAuthStore((state) => state.user?.id)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return useQuery(['auth', 'permissions', userId], () => authApi.getPermissions(), {
    enabled: isAuthenticated && Boolean(userId),
    staleTime: 60_000,
    refetchOnWindowFocus: true,
  })
}

export function useCan() {
  const { data, isSuccess } = usePermissions()
  const held = useMemo(() => new Set(data?.permissions ?? []), [data])
  return {
    /** True once the permission list has loaded (the dashboard layout waits for it) */
    ready: isSuccess,
    /** Does the user hold this permission? e.g. can('prescriptions.issue') */
    can: (key: string) => held.has(key),
    /** Does the user hold at least one of these? */
    canAny: (...keys: string[]) => keys.some((key) => held.has(key)),
  }
}
