// Dashboard Analytics Types

export interface DateRangeFilter {
  date_from?: string
  date_to?: string
}

export interface TrendData {
  date: string
  value: number
  label?: string
}

// Overview Stats
export interface OverviewStats {
  // Patient stats
  total_patients: number
  new_patients_this_month: number
  active_patients: number

  // Appointment stats
  total_appointments: number
  upcoming_appointments: number
  appointments_today: number

  // Visit stats
  total_visits: number
  visits_this_month: number

  // Financial stats
  total_revenue: number
  revenue_this_month: number
  pending_payments: number

  // Prescription stats
  total_prescriptions: number
  prescriptions_this_month: number

  // Period info
  period_start?: string
  period_end?: string
}

// Financial Analytics
export interface RevenueByMethod {
  cash: number
  bkash: number
  other: number
}

export interface FinancialAnalytics {
  total_revenue: number
  total_payments: number
  average_payment: number
  paid_amount: number
  pending_amount: number
  refunded_amount: number
  revenue_by_method: RevenueByMethod
  total_invoices: number
  paid_invoices: number
  overdue_invoices: number
  overdue_amount: number
  daily_revenue: TrendData[]
  period_start?: string
  period_end?: string
}

// Patient Analytics
export interface PatientDemographics {
  male: number
  female: number
  other: number
}

export interface AgeGroupDistribution {
  age_0_18: number
  age_19_35: number
  age_36_50: number
  age_51_65: number
  age_66_plus: number
}

export interface TopDiagnosis {
  diagnosis: string
  count: number
}

export interface PatientAnalytics {
  total_patients: number
  new_patients: number
  active_patients: number
  demographics: PatientDemographics
  age_distribution: AgeGroupDistribution
  top_diagnoses: TopDiagnosis[]
  patient_growth: TrendData[]
  period_start?: string
  period_end?: string
}

// Appointment Analytics
export interface AppointmentByStatus {
  scheduled: number
  confirmed: number
  completed: number
  cancelled: number
  no_show: number
}

export interface AppointmentByType {
  consultation: number
  follow_up: number
  emergency: number
}

export interface AppointmentAnalytics {
  total_appointments: number
  upcoming_appointments: number
  completed_appointments: number
  cancellation_rate: number
  by_status: AppointmentByStatus
  by_type: AppointmentByType
  booking_trend: TrendData[]
  peak_hours: { hour: number; count: number }[]
  period_start?: string
  period_end?: string
}

// Visit Analytics
export interface VisitByType {
  consultation: number
  follow_up: number
  emergency: number
}

export interface TopChiefComplaint {
  complaint: string
  count: number
}

export interface VisitAnalytics {
  total_visits: number
  average_visits_per_patient: number
  by_type: VisitByType
  top_complaints: TopChiefComplaint[]
  visit_trend: TrendData[]
  period_start?: string
  period_end?: string
}

// Prescription Analytics
export interface TopMedicine {
  medicine_name: string
  count: number
}

export interface PrescriptionByStatus {
  draft: number
  issued: number
  voided: number
}

export interface PrescriptionAnalytics {
  total_prescriptions: number
  total_items: number
  average_items_per_prescription: number
  by_status: PrescriptionByStatus
  top_medicines: TopMedicine[]
  prescription_trend: TrendData[]
  period_start?: string
  period_end?: string
}
