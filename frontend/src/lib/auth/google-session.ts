/**
 * Hands the verified Google ID token from the login page to the
 * registration-completion page without putting it in the URL (it's a
 * short-lived bearer credential, not just an identifier). sessionStorage
 * scopes it to this tab and clears it once consumed or on tab close.
 */
export const GOOGLE_ID_TOKEN_STORAGE_KEY = 'altcare_google_id_token'

export function stashGoogleIdToken(idToken: string): void {
  sessionStorage.setItem(GOOGLE_ID_TOKEN_STORAGE_KEY, idToken)
}

export function consumeGoogleIdToken(): string | null {
  const token = sessionStorage.getItem(GOOGLE_ID_TOKEN_STORAGE_KEY)
  sessionStorage.removeItem(GOOGLE_ID_TOKEN_STORAGE_KEY)
  return token
}
