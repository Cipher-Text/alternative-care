import { getRequestConfig } from 'next-intl/server'
import { cookies } from 'next/headers'

/**
 * Messages are split so areas can be translated independently:
 *   messages/{locale}.json            shared strings (common, auth, nav, pager, pages)
 *   messages/{locale}/<area>.json     one file per area; its top-level keys are that area's
 *                                     namespaces (e.g. patients.json -> "patientsUi": {...})
 * Keep this list, scripts/check-i18n.js and the files in step.
 */
export const MESSAGE_AREAS = ['patients', 'prescriptions', 'appointments', 'payments', 'home', 'library', 'symptoms', 'publicShell', 'publicHome', 'publicInfo', 'publicDirectory', 'publicLegal', 'publicContent', 'contentAdmin', 'directoryAdmin', 'billing', 'marketing', 'publicContact', 'publicHelp', 'identity'] as const

export default getRequestConfig(async () => {
  const store = await cookies()
  const locale = store.get('NEXT_LOCALE')?.value === 'bn' ? 'bn' : 'en'

  const base = (await import(`../messages/${locale}.json`)).default
  const areas = await Promise.all(
    MESSAGE_AREAS.map(async (area) => (await import(`../messages/${locale}/${area}.json`)).default)
  )

  return {
    locale,
    messages: Object.assign({}, base, ...areas),
  }
})
