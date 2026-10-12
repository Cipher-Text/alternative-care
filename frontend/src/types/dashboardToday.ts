export interface TodayAppointment {
  id: string
  patient_id: string
  patient_name: string
  /** HH:MM:SS */
  appointment_time: string
  duration_minutes: number
  status: string
  reason: string | null
}

export interface FollowUpDue {
  patient_id: string
  patient_name: string
  visit_id: string
  follow_up_date: string
  follow_up_notes: string | null
  /** Positive once the date has passed, negative while it is still ahead */
  days_overdue: number
}

export interface VisitAlert {
  patient_id: string
  patient_name: string
  visit_id: string
  visit_date: string
  red_flags: string[]
  referral_urgency: string | null
}

export interface PlanStatus {
  plan: string
  expires_at: string | null
  days_left: number | null
  expired: boolean
}

export interface TodayOverview {
  today: string
  appointments: TodayAppointment[]
  requests_waiting: number
  follow_ups_due: FollowUpDue[]
  alerts: VisitAlert[]
  plan: PlanStatus
}
