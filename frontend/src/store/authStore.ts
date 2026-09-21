import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import Cookies from 'js-cookie'
import type { User } from '@/types/auth'

interface AuthStore {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  hasHydrated: boolean

  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
  setAccessToken: (token: string) => void
  setHydrated: (value: boolean) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      hasHydrated: false,

      setAuth: (user, accessToken, refreshToken) => {
        // Store tokens in httpOnly-like cookies (more secure than localStorage)
        Cookies.set('accessToken', accessToken, { expires: 1/48 }) // 30 minutes
        Cookies.set('refreshToken', refreshToken, { expires: 7 }) // 7 days
        // Sync UI locale to the account's stored language preference
        Cookies.set('NEXT_LOCALE', user.language ?? 'en', { expires: 365 })

        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        })
      },

      logout: () => {
        Cookies.remove('accessToken')
        Cookies.remove('refreshToken')

        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }))
      },

      setAccessToken: (token) => {
        Cookies.set('accessToken', token, { expires: 1/48 })
        set({ accessToken: token })
      },

      setHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user }), // Only persist user, not tokens
      onRehydrateStorage: () => (state) => {
        const hasAccessToken = Boolean(Cookies.get('accessToken'))
        const hasRefreshToken = Boolean(Cookies.get('refreshToken'))
        const hasUser = Boolean(state?.user)

        if (state) {
          state.isAuthenticated = hasUser && (hasAccessToken || hasRefreshToken)
          state.accessToken = Cookies.get('accessToken') ?? null
          state.refreshToken = Cookies.get('refreshToken') ?? null
          state.hasHydrated = true
        }
      },
    }
  )
)
