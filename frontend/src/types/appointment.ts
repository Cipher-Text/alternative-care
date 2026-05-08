export type AppointmentStatus =
  | 'scheduled'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'no_show'

export interface Appointment {
  id: string
  patient_id: string
  doctor_id: string
  appointment_date: string
  appointment_time: string
  duration_minutes: number
  status: AppointmentStatus
  reason?: string | null
  notes?: string | null
}

export interface AppointmentCreateRequest {
  patient_id: string
  doctor_id: string
  appointment_date: string
  appointment_time: string
  duration_minutes?: number
  reason?: string
  notes?: string
}

export interface AppointmentListParams {
  appointment_date?: string
  patient_id?: string
  doctor_id?: string
  status?: AppointmentStatus
  limit?: number
  offset?: number
}
