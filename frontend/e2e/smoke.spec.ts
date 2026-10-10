import { test, expect } from '@playwright/test'

// One end-to-end path per T7: login -> patient -> prescription -> issue -> PDF.
// Uses the seeded doctor account (backend/seed_data/sample_data.json) rather
// than a throwaway registration, since a fresh tenant would need admin
// approval before it could log in.
const DOCTOR_EMAIL = 'dr.rahman@example.com'
const DOCTOR_PASSWORD = 'Test@1234'

test('login, create patient, issue prescription, view PDF', async ({ page }) => {
  const patientName = `E2E Smoke Patient ${Date.now()}`

  await test.step('login', async () => {
    await page.goto('/login')
    await page.locator('#email').fill(DOCTOR_EMAIL)
    await page.locator('#password').fill(DOCTOR_PASSWORD)
    await Promise.all([
      page.waitForURL('**/dashboard**', { timeout: 15000 }),
      page.locator('button[type="submit"]').click(),
    ])
  })

  await test.step('create patient', async () => {
    await page.goto('/patients/new')
    await page.locator('#full_name').fill(patientName)

    const [createResponse] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().endsWith('/api/v1/patients') && res.request().method() === 'POST'
      ),
      page.getByRole('button', { name: 'Create Patient' }).click(),
    ])
    expect(createResponse.ok()).toBe(true)
  })

  await test.step('build and issue prescription', async () => {
    await page.goto('/prescriptions/new')

    // Pick the patient just created
    await page.getByPlaceholder('Search by name or phone...').fill(patientName)
    await page.locator('button', { hasText: patientName }).first().click()

    // Add one medicine item via free text (autocomplete needs seeded global
    // medicines, which Stage 2 hasn't populated yet)
    await page.getByRole('button', { name: 'Add First Medicine' }).click()
    await page.getByRole('button', { name: 'Use free text' }).click()
    await page.locator('#medicine_name').fill('Arnica Montana 30C')
    await page.locator('#dosage').fill('2 drops')
    await page.locator('#frequency').fill('3 times daily')
    await page.getByRole('button', { name: 'Add Medicine' }).click()

    const [issueResponse] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().endsWith('/api/v1/prescriptions') && res.request().method() === 'POST'
      ),
      page.waitForURL('**/prescriptions/**', { timeout: 15000 }),
      page.getByRole('button', { name: 'Issue Prescription' }).click(),
    ])
    expect(issueResponse.ok()).toBe(true)
  })

  await test.step('view PDF', async () => {
    // The PDF is rendered by the backend on demand and fetched with the auth header, so assert
    // on the API response: a real PDF document, not a placeholder link.
    const [pdfResponse] = await Promise.all([
      page.waitForResponse((res) => res.url().endsWith('/pdf') && res.request().method() === 'GET'),
      page.getByRole('button', { name: 'View / Print PDF' }).click(),
    ])
    expect(pdfResponse.ok()).toBe(true)
    expect(pdfResponse.headers()['content-type']).toBe('application/pdf')
    expect((await pdfResponse.body()).subarray(0, 4).toString()).toBe('%PDF')
  })
})
