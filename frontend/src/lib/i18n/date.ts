'use client'

import { format as dfFormat, formatDistanceToNow as dfDistance } from 'date-fns'
import { bn, enUS } from 'date-fns/locale'
import { useLocale } from 'next-intl'

/**
 * date-fns formatting in the UI language (Bengali month and weekday names in Bengali mode).
 *
 *   const { fmt } = useDateFormat()
 *   fmt(patient.created_at, 'MMM d, yyyy')      // "Oct 11, 2026" / "অক্টো ১১, ২০২৬"
 *
 * Digits are Bengali numerals in Bengali mode (date-fns' own behaviour). That is intentional for
 * dates; plain numbers elsewhere in the UI stay ASCII.
 */
export function useDateFormat() {
  const locale = useLocale() === 'bn' ? bn : enUS
  return {
    fmt: (date: Date | string | number, pattern: string) => dfFormat(new Date(date), pattern, { locale }),
    ago: (date: Date | string | number) => dfDistance(new Date(date), { addSuffix: true, locale }),
    dateFnsLocale: locale,
  }
}
