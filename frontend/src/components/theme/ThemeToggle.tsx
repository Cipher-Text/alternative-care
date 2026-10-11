'use client'

import { Moon, Sun } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useThemeStore } from '@/store/themeStore'
import { Button } from '@/components/ui/button'

/** One button that switches between light and dark. */
export function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)
  const isDark = theme === 'dark'
  const t = useTranslations('nav')
  const label = isDark ? t('switchToLight') : t('switchToDark')

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={label}
      title={label}
      className="h-9 w-9 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700"
    >
      {/* Show the mode you would switch TO */}
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  )
}
