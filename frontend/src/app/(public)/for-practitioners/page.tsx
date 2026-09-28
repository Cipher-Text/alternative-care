import Link from 'next/link'
import {
  ArrowRight,
  Users2,
  CalendarClock,
  FileText,
  CreditCard,
  Pill,
  ShieldCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const features = [
  {
    icon: Users2,
    title: 'Patient management',
    description: 'Full patient records, tags, diagnoses, and history in one place.',
  },
  {
    icon: CalendarClock,
    title: 'Appointments & visits',
    description: 'Scheduling, calendar views, and visit notes tied to each patient.',
  },
  {
    icon: FileText,
    title: 'Prescriptions',
    description: 'A prescription builder with medicine autocomplete and an issue/void workflow.',
  },
  {
    icon: Pill,
    title: 'Your own medicine library',
    description: 'Start from the global catalog and add your own medicines, aliases, and dosages.',
  },
  {
    icon: CreditCard,
    title: 'Payments & invoicing',
    description: 'Track payments and generate invoices without leaving the platform.',
  },
  {
    icon: ShieldCheck,
    title: 'Multi-tenant security',
    description: "Row-level isolation keeps every clinic's data separate and private.",
  },
]

export default function ForPractitionersPage() {
  return (
    <div>
      <section className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
          Practice management built for alternative medicine
        </h1>
        <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
          Homeopathy, Ayurveda, Unani, and Herbal Medicine practitioners run their whole clinic on
          AltCare — patients, appointments, prescriptions, and payments.
        </p>
        <div className="mt-8">
          <Button asChild size="lg">
            <Link href="/login">
              Get Started <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Card key={feature.title}>
              <CardHeader>
                <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center mb-2">
                  <feature.icon className="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-600 dark:text-gray-400">
                {feature.description}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
