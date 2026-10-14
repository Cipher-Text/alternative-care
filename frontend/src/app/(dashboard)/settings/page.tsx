'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { MessageSquare } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

/** Settings index: Messaging (SMS and email credits). */
export default function SettingsPage() {
  const t = useTranslations('billingUi.settingsIndex')
  const tm = useTranslations('billingUi.messaging')

  const items = [
    { href: '/settings/messaging', icon: MessageSquare, title: tm('title'), text: t('messagingText') },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {items.map(({ href, icon: Icon, title, text }) => (
          <Link key={href} href={href} className="block rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-600">
            <Card className="h-full transition-colors hover:border-emerald-300">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-emerald-600" aria-hidden="true" />
                  {title}
                </CardTitle>
                <CardDescription>{text}</CardDescription>
              </CardHeader>
              <CardContent />
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
