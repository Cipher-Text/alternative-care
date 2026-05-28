export const integrationLogoByProviderName: Record<string, string> = {
  twilio: '/integrations/twilio.svg',
  banglalink: '/integrations/banglalink.svg',
  robi: '/integrations/robi.svg',
  bulksmsbd: '/integrations/bulksmsbd.svg',
  sendgrid: '/integrations/sendgrid.svg',
  aws_ses: '/integrations/aws-ses.png',
  smtp: '/integrations/smtp.svg',
  bkash: '/integrations/bkash.svg',
  nagad: '/integrations/nagad.svg',
  rocket: '/integrations/rocket.svg',
  sslcommerz: '/integrations/sslcommerz.svg',
  stripe: '/integrations/stripe.svg',
};

export function getIntegrationLogoUrl(provider?: { name?: string; logo_url?: string | null } | null) {
  if (!provider?.name) {
    return provider?.logo_url ?? null;
  }

  return integrationLogoByProviderName[provider.name] ?? provider.logo_url ?? null;
}
