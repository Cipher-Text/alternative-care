'use client'

import { useEffect } from 'react'
import { applyTheme, useThemeStore } from '@/store/themeStore'

/** Keeps the document's theme class in step with the stored choice (light or dark). */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useThemeStore((state) => state.theme)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  return <>{children}</>
}
