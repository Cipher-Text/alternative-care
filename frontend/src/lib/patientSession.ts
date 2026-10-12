/** The patient portal's own session: a token kept in sessionStorage only (gone when the tab closes).
 * It is deliberately separate from the clinic staff session and never shares its storage or client. */

const KEY = 'altcare.patient.session'

interface Stored {
  token: string
  expiresAt: string
}

function read(): Stored | null {
  try {
    const raw = window.sessionStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as Stored) : null
  } catch {
    return null
  }
}

export function getPatientToken(): string | null {
  if (typeof window === 'undefined') return null
  const stored = read()
  if (!stored) return null
  if (new Date(stored.expiresAt).getTime() <= Date.now()) {
    clearPatientSession()
    return null
  }
  return stored.token
}

export function setPatientSession(token: string, expiresAt: string): void {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify({ token, expiresAt }))
  } catch {
    /* private mode: the session simply will not persist */
  }
}

export function clearPatientSession(): void {
  try {
    window.sessionStorage.removeItem(KEY)
  } catch {
    /* ignore */
  }
}
