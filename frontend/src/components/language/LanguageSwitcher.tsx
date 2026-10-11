'use client'

import Cookies from 'js-cookie'
import { Globe } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function LanguageSwitcher() {
  const locale = useLocale()
  const router = useRouter()
  const t = useTranslations('common')
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const updateUser = useAuthStore((state) => state.updateUser)

  const setLocale = (next: 'en' | 'bn') => {
    if (next === locale) return
    // Apply now (the server reads this cookie to pick the language)...
    Cookies.set('NEXT_LOCALE', next, { expires: 365 })
    router.refresh()

    // ...and remember it on the account, so the next login or other device keeps the choice
    // instead of reverting to the old one. A failure only costs the cross-device memory.
    if (isAuthenticated) {
      updateUser({ language: next })
      authApi.setLanguage(next).catch(() => {
        toast.error(t('languageNotSaved'))
      })
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700"
        >
          <Globe className="h-4 w-4" />
          <span className="sr-only">{t('language')}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700"
      >
        <DropdownMenuItem
          onClick={() => setLocale('en')}
          className="cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700"
        >
          <span>{t('english')}</span>
          {locale === 'en' && (
            <span className="ml-auto text-emerald-600 dark:text-emerald-400">✓</span>
          )}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setLocale('bn')}
          className="cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700"
        >
          <span>{t('bengali')}</span>
          {locale === 'bn' && (
            <span className="ml-auto text-emerald-600 dark:text-emerald-400">✓</span>
          )}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
