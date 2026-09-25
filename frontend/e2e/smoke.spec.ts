import { test, expect } from '@playwright/test'

// One end-to-end path per T7: login -> patient -> prescription -> issue -> PDF.
// Uses the seeded doctor account (backend/seed_data/sample_data.json) rather
// than a throwaway registration, since a fresh tenant would need admin
// approval before it could log in.
const DOCTOR_EMAIL = 'dr.rahman@example.com'
const DOCTOR_PASSWORD = 'Test@1234'

test('login, create patient, issue prescription, generate PDF', async ({ page }) => {
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

  await test.step('generate PDF', async () => {
    // pdf_url is a placeholder domain today (no storage adapter yet — D6,
    // Stage 3), so assert at the API layer rather than fetching the file.
    const [pdfResponse] = await Promise.all([
      page.waitForResponse((res) => res.url().endsWith('/generate-pdf')),
      page.getByRole('button', { name: 'Download PDF' }).click(),
    ])
    expect(pdfResponse.ok()).toBe(true)
    const body = await pdfResponse.json()
    expect(typeof body.pdf_url).toBe('string')
    expect(body.pdf_url.length).toBeGreaterThan(0)
  })
})
