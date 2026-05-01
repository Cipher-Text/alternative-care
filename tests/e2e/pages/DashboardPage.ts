import { expect, Page } from '@playwright/test'

export class DashboardPage {
  constructor(private readonly page: Page) {}

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/dashboard/)
  }
}
