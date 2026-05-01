import { test, expect } from '@playwright/test'

test('visiting / redirects to login or dashboard', async ({ page }) => {
  await page.goto('/')
  await expect(page.url()).toMatch(/\/(login|dashboard)/)
})
