import { expect, Page } from '@playwright/test'

export class PatientsPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto('/patients')
    await expect(this.page).toHaveURL(/\/patients/)
  }
}
