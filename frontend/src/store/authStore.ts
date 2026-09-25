import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import Cookies from 'js-cookie'
import type { User } from '@/types/auth'

interface AuthStore {
  user: User | null
  // In-memory only — never persisted or written to a JS-readable cookie.
  // The refresh token lives solely in the backend's httpOnly cookie; a
  // fresh page load re-derives accessToken via a silent /auth/refresh
  // call rather than reading it back from storage.
  accessToken: string | null
  isAuthenticated: boolean
  hasHydrated: boolean

  setAuth: (user: User, accessToken: string) => void
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
      isAuthenticated: false,
      hasHydrated: false,

      setAuth: (user, accessToken) => {
        // Sync UI locale to the account's stored language preference
        Cookies.set('NEXT_LOCALE', user.language ?? 'en', { expires: 365 })

        set({
          user,
          accessToken,
          isAuthenticated: true,
        })
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
        })
      },

      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }))
      },

      setAccessToken: (token) => {
        set({ accessToken: token, isAuthenticated: true })
      },

      setHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user }), // Only persist user, not tokens
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.hasHydrated = true
        }
      },
    }
  )
)
