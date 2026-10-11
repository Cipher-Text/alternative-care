import type { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime'

/**
 * Go to `path` after login, making sure the page is rendered in the account's language.
 *
 * The language lives in a cookie that the *server* reads to pick the messages and `<html lang>`.
 * Login sets that cookie from the account, but a client-side `router.push` keeps the root layout
 * that was rendered with the old cookie, so the first screen stayed in the old language until a
 * manual reload. When the account's language differs from what is on screen, do a full navigation
 * instead so the server re-reads the cookie; otherwise a normal client navigation is fine.
 */
export function navigateAfterLogin(
  router: Pick<AppRouterInstance, 'push'>,
  path: string,
  accountLanguage: string | null | undefined,
  currentLocale: string
) {
  if ((accountLanguage ?? 'en') !== currentLocale) {
    window.location.assign(path)
  } else {
    router.push(path)
  }
}
