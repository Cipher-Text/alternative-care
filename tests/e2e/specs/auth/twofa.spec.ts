import { expect, test } from '@playwright/test'

test('2FA login flow shows verification step and completes login', async ({ page }) => {
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user: {
          id: 'user-2fa',
          email: '2fa@test.com',
          role: 'doctor',
          tenant_id: 'tenant-1',
          is_2fa_enabled: true,
          is_active: true,
        },
        requires_2fa: true,
      }),
    })
  })

  await page.route('**/api/v1/auth/login-2fa', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user: {
          id: 'user-2fa',
          email: '2fa@test.com',
          role: 'doctor',
          tenant_id: 'tenant-1',
          is_2fa_enabled: true,
          is_active: true,
        },
        tokens: {
          access_token: 'access-token-2fa',
          refresh_token: 'refresh-token-2fa',
          token_type: 'bearer',
        },
      }),
    })
  })

  await page.goto('/login')
  await page.getByLabel(/email/i).fill('2fa@test.com')
  await page.getByLabel(/password/i).fill('StrongPass123')
  await page.getByRole('button', { name: /^login$/i }).click()

  await expect(
    page.getByRole('heading', { name: /two-factor authentication/i }),
  ).toBeVisible()

  await page.getByLabel(/authentication code/i).fill('123456')
  await page.getByRole('button', { name: /^verify$/i }).click()

  await expect(page).toHaveURL(/\/dashboard/)
})
