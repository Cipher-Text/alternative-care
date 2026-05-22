import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'light' | 'dark' | 'system'

interface ThemeStore {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  hasHydrated: boolean
  setHydrated: (value: boolean) => void
}

// Helper to get system preference
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Helper to resolve theme
const resolveTheme = (theme: Theme): 'light' | 'dark' => {
  return theme === 'system' ? getSystemTheme() : theme
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: 'system',
      resolvedTheme: 'dark',
      hasHydrated: false,

      setTheme: (theme: Theme) => {
        const resolved = resolveTheme(theme)

        // Update document class
        if (typeof window !== 'undefined') {
          const root = document.documentElement
          root.classList.remove('light', 'dark')
          root.classList.add(resolved)

          // Update meta theme-color for mobile browsers
          const metaThemeColor = document.querySelector('meta[name="theme-color"]')
          if (metaThemeColor) {
            metaThemeColor.setAttribute(
              'content',
              resolved === 'dark' ? '#0f172a' : '#ffffff'
            )
          }
        }

        set({ theme, resolvedTheme: resolved })
      },

      setHydrated: (value: boolean) => set({ hasHydrated: value }),
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          const resolved = resolveTheme(state.theme)
          state.resolvedTheme = resolved
          state.hasHydrated = true

          // Apply theme on hydration
          if (typeof window !== 'undefined') {
            const root = document.documentElement
            root.classList.remove('light', 'dark')
            root.classList.add(resolved)
          }
        }
      },
    }
  )
)

// Hook to listen to system theme changes
export const useSystemThemeListener = () => {
  const { theme, setTheme } = useThemeStore()

  if (typeof window !== 'undefined' && theme === 'system') {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = () => {
      if (theme === 'system') {
        setTheme('system') // Trigger re-resolution
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }
}
