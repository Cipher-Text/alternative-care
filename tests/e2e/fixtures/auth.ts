import { Page } from '@playwright/test'
import { LoginPage } from '../pages/LoginPage'
import { seededUsers } from './users'

export async function loginAsAdmin(page: Page) {
  const login = new LoginPage(page)
  await login.goto()
  await login.login(seededUsers.admin.email, seededUsers.admin.password)
}

export async function loginAsOperator(page: Page) {
  const login = new LoginPage(page)
  await login.goto()
  await login.login(seededUsers.operator.email, seededUsers.operator.password)
}
