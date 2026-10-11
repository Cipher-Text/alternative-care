import { FlaskConical, Leaf, Sprout, Stethoscope, ShieldCheck, BookOpen } from 'lucide-react'
import { getTranslations } from 'next-intl/server'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const disciplines = [
  { icon: FlaskConical, key: 'homeopathy' },
  { icon: Leaf, key: 'ayurveda' },
  { icon: Sprout, key: 'unani' },
  { icon: Stethoscope, key: 'herbal' },
] as const

export default async function AboutPage() {
  const t = await getTranslations('publicInfoUi.about')
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-16">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
        {t('intro')}
      </p>

      <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4">
        {disciplines.map((d) => (
          <div
            key={d.key}
            className="flex flex-col items-center gap-2 rounded-xl border border-gray-200 dark:border-slate-700 p-4 text-center"
          >
            <d.icon className="h-6 w-6 text-emerald-600 dark:text-emerald-300" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">{t(d.key)}</span>
          </div>
        ))}
      </div>

      <div className="mt-14 grid grid-cols-1 sm:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <ShieldCheck className="h-6 w-6 text-emerald-600 mb-2" />
            <CardTitle className="text-lg">{t('clinicsTitle')}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600 dark:text-gray-400">
            {t('clinicsBody')}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <BookOpen className="h-6 w-6 text-emerald-600 mb-2" />
            <CardTitle className="text-lg">{t('knowledgeTitle')}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600 dark:text-gray-400">
            {t('knowledgeBody')}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
