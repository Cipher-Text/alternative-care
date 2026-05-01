import type { FullConfig } from '@playwright/test'

export default async function globalSetup(_config: FullConfig) {
  // Hook for health checks / seed trigger if needed.
}
