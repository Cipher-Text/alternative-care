'use client'

const SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

let scriptPromise: Promise<void> | null = null

/**
 * Loads the Google Identity Services script once and caches the promise,
 * so multiple components mounting a Google button don't each inject it.
 */
export function loadGoogleIdentityScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google Identity Services can only load in the browser'))
  }
  if (window.google?.accounts?.id) {
    return Promise.resolve()
  }
  if (scriptPromise) {
    return scriptPromise
  }

  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${SCRIPT_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () =>
        reject(new Error('Failed to load Google Identity Services'))
      )
      return
    }

    const script = document.createElement('script')
    script.src = SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Identity Services'))
    document.head.appendChild(script)
  })

  return scriptPromise
}

// Minimal ambient types for the slice of the GIS API this app uses.
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: { credential: string }) => void
          }) => void
          renderButton: (
            parent: HTMLElement,
            options: {
              type?: 'standard' | 'icon'
              theme?: 'outline' | 'filled_blue' | 'filled_black'
              size?: 'large' | 'medium' | 'small'
              text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
              shape?: 'rectangular' | 'pill' | 'circle' | 'square'
              width?: string
              logo_alignment?: 'left' | 'center'
            }
          ) => void
        }
      }
    }
  }
}
