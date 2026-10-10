import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/** Two themes only. There is deliberately no "system" mode: the app never follows the OS. */
export type Theme = 'light' | 'dark'

interface ThemeStore {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  hasHydrated: boolean
  setHydrated: (value: boolean) => void
}

/** Apply a theme to the document (class used by Tailwind's `dark:` variant) and the browser UI. */
export function applyTheme(theme: Theme) {
  if (typeof window === 'undefined') return
  const root = document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(theme)

  // Keep the mobile browser chrome in step with the page
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', theme === 'dark' ? '#0f172a' : '#ffffff')
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: 'light',
      hasHydrated: false,

      setTheme: (theme: Theme) => {
        applyTheme(theme)
        set({ theme })
      },

      toggleTheme: () => get().setTheme(get().theme === 'dark' ? 'light' : 'dark'),

      setHydrated: (value: boolean) => set({ hasHydrated: value }),
    }),
    {
      name: 'theme-storage',
      version: 1,
      // v0 stored 'light' | 'dark' | 'system'. Anyone who had "system" keeps the look they
      // currently see (resolved once against the OS), then it is a plain light/dark choice.
      migrate: (persisted) => {
        const state = (persisted ?? {}) as { theme?: string }
        const resolved: Theme =
          state.theme === 'dark'
            ? 'dark'
            : state.theme === 'system' &&
                typeof window !== 'undefined' &&
                window.matchMedia('(prefers-color-scheme: dark)').matches
              ? 'dark'
              : 'light'
        return { theme: resolved }
      },
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.hasHydrated = true
          applyTheme(state.theme)
        }
      },
    }
  )
)
