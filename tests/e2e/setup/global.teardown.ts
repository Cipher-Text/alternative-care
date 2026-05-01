import type { FullConfig } from '@playwright/test'

export default async function globalTeardown(_config: FullConfig) {
  // Hook for cleanup if needed.
}
