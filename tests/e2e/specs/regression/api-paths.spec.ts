import { expect, test, type Page } from '@playwright/test'

async function useAuthenticatedState(page: Page) {
  const user = {
    id: 'user-e2e',
    email: 'doctor@example.com',
    full_name: 'Dr. E2E',
    role: 'doctor',
    tenant_id: 'tenant-e2e',
    plan: 'free',
    language: 'en',
    is_2fa_enabled: false,
    is_active: true,
    is_email_verified: true,
  }

  await page.context().addCookies([
    {
      name: 'accessToken',
      value: 'test-access-token',
      domain: 'localhost',
      path: '/',
    },
    {
      name: 'refreshToken',
      value: 'test-refresh-token',
      domain: 'localhost',
      path: '/',
    },
  ])

  await page.addInitScript((persistedUser) => {
    window.localStorage.setItem(
      'auth-storage',
      JSON.stringify({
        state: { user: persistedUser },
        version: 0,
      }),
    )
  }, user)
}

test('payments page calls versioned payment endpoints exactly once', async ({ page }) => {
  await useAuthenticatedState(page)

  const badUrls: string[] = []
  const seenUrls: string[] = []

  page.on('request', (request) => {
    const url = request.url()
    if (url.includes('/api/v1/api/v1/payments')) {
      badUrls.push(url)
    }
    if (url.includes('/api/v1/payments')) {
      seenUrls.push(url)
    }
  })

  await page.route('**/api/v1/payments/summary**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_payments: 0,
        total_amount: 0,
        paid_amount: 0,
        pending_amount: 0,
        cash_amount: 0,
        bkash_amount: 0,
      }),
    })
  })
  await page.route('**/api/v1/payments?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })
  await page.route('**/api/v1/payments', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.goto('/payments')
  await expect(page.getByRole('heading', { name: /payments & billing/i })).toBeVisible()

  expect(badUrls).toEqual([])
  expect(seenUrls.some((url) => url.includes('/api/v1/payments/summary'))).toBe(true)
  expect(seenUrls.some((url) => /\/api\/v1\/payments(?:\?|$)/.test(url))).toBe(true)
})

test('appointments page calls canonical appointments endpoint', async ({ page }) => {
  await useAuthenticatedState(page)

  const badUrls: string[] = []
  const seenUrls: string[] = []

  page.on('request', (request) => {
    const url = request.url()
    if (url.includes('/api/v1/appointments/appointments')) {
      badUrls.push(url)
    }
    if (url.includes('/api/v1/appointments')) {
      seenUrls.push(url)
    }
  })

  await page.route('**/api/v1/appointments**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })
  await page.route('**/api/v1/patients**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.goto('/appointments')
  await expect(page.getByRole('heading', { name: /^appointments$/i })).toBeVisible()

  expect(badUrls).toEqual([])
  expect(seenUrls.some((url) => /\/api\/v1\/appointments(?:\?|$)/.test(url))).toBe(true)
})
