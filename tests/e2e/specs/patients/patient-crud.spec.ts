import { expect, test } from '@playwright/test'
import { loginAsAdmin } from '../../fixtures/auth'

test('patient CRUD flow works from UI', async ({ page }) => {
  await loginAsAdmin(page)

  const suffix = Date.now()
  const firstName = `E2E${suffix}`
  const lastName = 'Patient'
  const fullName = `${firstName} ${lastName}`
  const email = `e2e.patient.${suffix}@example.com`
  const phone = `017${String(suffix).slice(-8)}`

  await page.goto('/patients/new')
  await expect(page).toHaveURL(/\/patients\/new/)

  await page.getByLabel(/first name/i).fill(firstName)
  await page.getByLabel(/last name/i).fill(lastName)
  await page.getByLabel(/date of birth/i).fill('1990-01-15')
  await page.getByLabel(/^phone \*/i).fill(phone)
  await page.getByLabel(/^email$/i).fill(email)

  const createResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/patients') &&
      response.request().method() === 'POST' &&
      response.status() === 201,
  )
  await page.getByRole('button', { name: /create patient/i }).click()
  const createResponse = await createResponsePromise
  const createdPatient = await createResponse.json()
  const patientId = createdPatient.id as string

  await expect(page).toHaveURL(/\/patients/)
  await expect(page.getByText(fullName)).toBeVisible()

  await page.goto(`/patients/${patientId}/edit`)
  await expect(page).toHaveURL(new RegExp(`/patients/${patientId}/edit`))
  await page.getByLabel(/^phone \*/i).fill(`018${String(suffix).slice(-8)}`)
  await page.getByRole('button', { name: /update patient/i }).click()

  await expect(page).toHaveURL(new RegExp(`/patients/${patientId}$`))
  await expect(page.getByRole('heading', { name: fullName })).toBeVisible()

  await page.getByRole('button', { name: /^delete$/i }).first().click()
  await page
    .getByRole('dialog')
    .getByRole('button', { name: /^delete$/i })
    .click()

  await expect(page).toHaveURL(/\/patients/)
  await expect(page.getByText(fullName)).not.toBeVisible()
})
