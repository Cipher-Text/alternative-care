import { useTranslations } from 'next-intl'

/** Label for a stored option code (`group` is a key under healthUi, such as "chronic"). An unknown or newly
 * added code shows as itself rather than breaking the screen. */
export function useCodeLabel(group: string) {
  const t = useTranslations('healthUi')
  return (code: string): string => (t.has(`${group}.${code}`) ? t(`${group}.${code}`) : code)
}
