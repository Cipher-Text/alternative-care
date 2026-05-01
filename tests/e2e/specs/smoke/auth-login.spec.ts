import { test } from '@playwright/test'
import { loginAsAdmin } from '../../fixtures/auth'
import { waitForDashboard } from '../../helpers/wait'

test('admin can login and reach dashboard', async ({ page }) => {
  await loginAsAdmin(page)
  await waitForDashboard(page)
})
