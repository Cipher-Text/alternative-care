import { FlaskConical, Leaf, Sprout, Stethoscope, ShieldCheck, BookOpen } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const disciplines = [
  { icon: FlaskConical, label: 'Homeopathy' },
  { icon: Leaf, label: 'Ayurveda' },
  { icon: Sprout, label: 'Unani' },
  { icon: Stethoscope, label: 'Herbal' },
]

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-16">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">About AltCare</h1>
      <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
        AltCare is a practice management platform built specifically for alternative medicine
        practitioners — Homeopathy, Ayurveda, Unani, and Herbal medicine — alongside a public
        knowledge directory of medicines, symptoms, and the institutions that train the next
        generation of practitioners.
      </p>

      <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4">
        {disciplines.map((d) => (
          <div
            key={d.label}
            className="flex flex-col items-center gap-2 rounded-xl border border-gray-200 dark:border-slate-700 p-4 text-center"
          >
            <d.icon className="h-6 w-6 text-emerald-600 dark:text-emerald-300" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">{d.label}</span>
          </div>
        ))}
      </div>

      <div className="mt-14 grid grid-cols-1 sm:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <ShieldCheck className="h-6 w-6 text-emerald-600 mb-2" />
            <CardTitle className="text-lg">Built for clinics</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600 dark:text-gray-400">
            Every clinic&apos;s data is row-level isolated. Patients, prescriptions, and payments
            stay private to the practice that created them.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <BookOpen className="h-6 w-6 text-emerald-600 mb-2" />
            <CardTitle className="text-lg">Open knowledge</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600 dark:text-gray-400">
            The medicine, symptom, and institution catalogs are admin-curated and free to browse —
            no account required.
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
