import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Coarse server-side gate (D8): the httpOnly refresh_token cookie is
// invisible to browser JS but readable here. Presence-only — this can't
// validate the JWT (no secret on the frontend), it just kills the
// "server renders the dashboard shell then flashes/redirects" case for a
// signed-out visitor hitting a protected URL directly. Real authorization
// is still enforced by the backend's 401s.
export function proxy(request: NextRequest) {
  const hasRefreshCookie = request.cookies.has('refresh_token')

  if (!hasRefreshCookie) {
    const loginUrl = new URL('/login', request.url)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/patients/:path*',
    '/appointments/:path*',
    '/prescriptions/:path*',
    '/profile/:path*',
    '/payments/:path*',
    '/medicines/:path*',
    '/symptoms/:path*',
    '/settings/:path*',
    '/admin/:path*',
  ],
}
