'use client'

import { use } from 'react'
import { ConsultationScreen } from '@/components/consultation/ConsultationScreen'

/** One screen per consultation (a visit): complaint, vitals, case details, diagnosis and plan, medicines, issue, finish. */
export default function ConsultationPage({ params }: { params: Promise<{ visitId: string }> }) {
  const { visitId } = use(params)
  return <ConsultationScreen visitId={visitId} />
}
