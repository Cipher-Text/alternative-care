import { useCallback, useState } from 'react'

export type NearMeStatus = 'idle' | 'locating' | 'ready' | 'denied' | 'unavailable' | 'error'

export interface Coords {
  lat: number
  lon: number
}

/**
 * Asks the browser for the practitioner's position, on request only.
 *
 * Privacy: nothing is stored. The coordinates stay in memory and are sent to the API only as
 * search parameters, rounded to 3 decimals (~110 m) so the exact position is never needed. The
 * browser itself asks for permission, and only works on HTTPS (or localhost).
 */
export function useNearMe() {
  const [status, setStatus] = useState<NearMeStatus>('idle')
  const [coords, setCoords] = useState<Coords | null>(null)

  const locate = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setStatus('unavailable')
      return
    }
    setStatus('locating')
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          lat: Math.round(position.coords.latitude * 1000) / 1000,
          lon: Math.round(position.coords.longitude * 1000) / 1000,
        })
        setStatus('ready')
      },
      (error) => {
        setCoords(null)
        // 1 = permission denied, 2 = position unavailable, 3 = timeout
        setStatus(error.code === 1 ? 'denied' : error.code === 2 ? 'unavailable' : 'error')
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
    )
  }, [])

  const clear = useCallback(() => {
    setCoords(null)
    setStatus('idle')
  }, [])

  return { status, coords, locate, clear }
}

export const NEAR_ME_MESSAGES: Partial<Record<NearMeStatus, string>> = {
  denied: 'Location access was blocked. Allow it in your browser settings to search near you.',
  unavailable: 'Your location is not available right now. Check that location services are on.',
  error: 'Finding your location took too long. Please try again.',
}
