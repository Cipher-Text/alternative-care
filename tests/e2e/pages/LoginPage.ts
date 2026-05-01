import { expect, Page } from '@playwright/test'

export class LoginPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto('/login')
    await expect(this.page.getByRole('heading', { name: /login to altcare/i })).toBeVisible()
  }

  async login(email: string, password: string) {
    await this.page.getByLabel(/email/i).fill(email)
    await this.page.getByLabel(/password/i).fill(password)
    await this.page.getByRole('button', { name: /^login$/i }).click()
  }
}
