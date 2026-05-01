import { format, parseISO, differenceInYears } from 'date-fns'

/**
 * Format date string to readable format
 */
export function formatDate(date: string | Date, formatStr: string = 'MMM dd, yyyy'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return format(dateObj, formatStr)
}

/**
 * Calculate age from date of birth
 */
export function calculateAge(dateOfBirth: string | Date): number {
  const dob = typeof dateOfBirth === 'string' ? parseISO(dateOfBirth) : dateOfBirth
  return differenceInYears(new Date(), dob)
}

/**
 * Format patient name
 */
export function formatPatientName(firstName: string, lastName: string): string {
  return `${firstName} ${lastName}`
}

/**
 * Format phone number
 */
export function formatPhone(phone: string): string {
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '')

  // Format as: +880 1XXX-XXXXXX
  if (cleaned.startsWith('880')) {
    return `+${cleaned.slice(0, 3)} ${cleaned.slice(3, 7)}-${cleaned.slice(7)}`
  }

  // Format as: 01XXX-XXXXXX
  if (cleaned.startsWith('0')) {
    return `${cleaned.slice(0, 5)}-${cleaned.slice(5)}`
  }

  return phone
}

/**
 * Format gender for display
 */
export function formatGender(gender: string): string {
  return gender.charAt(0).toUpperCase() + gender.slice(1).toLowerCase()
}

/**
 * Format blood group
 */
export function formatBloodGroup(bloodGroup?: string): string {
  if (!bloodGroup) return 'Not specified'
  return bloodGroup.toUpperCase()
}

/**
 * Get age group from age
 */
export function getAgeGroup(age: number): string {
  if (age <= 18) return '0-18'
  if (age <= 35) return '19-35'
  if (age <= 50) return '36-50'
  if (age <= 65) return '51-65'
  return '66+'
}
