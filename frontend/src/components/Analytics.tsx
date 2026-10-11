import Script from 'next/script'

/**
 * Privacy-friendly, cookieless visit statistics (Plausible). Renders nothing unless
 * NEXT_PUBLIC_ANALYTICS_DOMAIN is set, so local/dev and unconfigured deployments send nothing.
 * Set NEXT_PUBLIC_ANALYTICS_SRC to point at a self-hosted script instead of plausible.io.
 */
export function Analytics() {
  const domain = process.env.NEXT_PUBLIC_ANALYTICS_DOMAIN
  if (!domain) return null
  return (
    <Script
      defer
      data-domain={domain}
      src={process.env.NEXT_PUBLIC_ANALYTICS_SRC || 'https://plausible.io/js/script.js'}
      strategy="afterInteractive"
    />
  )
}
