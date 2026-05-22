import { expect, test } from '@playwright/test'
import { loginAsAdmin } from '../../fixtures/auth'

test('expired access token triggers refresh and retries request', async ({ page, context }) => {
  await loginAsAdmin(page)

  await context.addCookies([
    {
      name: 'accessToken',
      value: 'expired-access-token',
      domain: 'localhost',
      path: '/',
    },
    {
      name: 'refreshToken',
      value: 'valid-refresh-token',
      domain: 'localhost',
      path: '/',
    },
  ])

  let refreshCalled = 0
  await page.route('**/api/v1/auth/refresh', async (route) => {
    refreshCalled += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      }),
    })
  })

  let patientCalls = 0
  await page.route('**/api/v1/patients**', async (route) => {
    patientCalls += 1
    if (patientCalls === 1) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Token expired' }),
      })
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.goto('/patients')
  await expect(page).toHaveURL(/\/patients/)
  await expect(page.getByRole('heading', { name: /patients/i })).toBeVisible()
  expect(refreshCalled).toBe(1)
})
