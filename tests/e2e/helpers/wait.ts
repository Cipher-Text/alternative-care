import { expect, Page } from '@playwright/test'

export async function waitForDashboard(page: Page) {
  await expect(page).toHaveURL(/\/dashboard/)
}
