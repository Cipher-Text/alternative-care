/** Public contact form and the staff inbox (matches backend app/shared/schemas/contact.py). */

export type ContactTopic = 'general' | 'enterprise' | 'billing' | 'report_profile' | 'other'

export const CONTACT_TOPICS: ContactTopic[] = ['general', 'enterprise', 'billing', 'report_profile', 'other']

export interface ContactMessageInput {
  topic: ContactTopic
  name: string
  /** At least one of email / phone is required */
  email?: string
  phone?: string
  organisation?: string
  message: string
  consent: boolean
  /** Honeypot — leave empty; hidden from people */
  website?: string
}

export interface ContactMessage {
  id: string
  topic: ContactTopic
  name: string
  email: string | null
  phone: string | null
  organisation: string | null
  message: string
  status: 'new' | 'handled'
  created_at: string
  handled_at: string | null
}
