import Link from 'next/link'
import { ShieldCheck } from 'lucide-react'
import { getTranslations } from 'next-intl/server'

export async function VerifiedBadge() {
  const t = await getTranslations('publicPractitionersUi')
  return (
    <Link
      href="/verification"
      title={t('verifiedHelp')}
      className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-950 dark:text-emerald-300"
    >
      <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
      {t('verified')}
    </Link>
  )
}
