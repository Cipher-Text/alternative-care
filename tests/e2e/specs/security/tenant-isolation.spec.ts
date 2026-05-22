import { APIRequestContext, expect, test } from '@playwright/test'
import { apiUrl } from '../../helpers/api'
import { seededUsers } from '../../fixtures/users'

async function loginAndGetAccessToken(
  request: APIRequestContext,
  email: string,
  password: string,
) {
  const res = await request.post(apiUrl('/auth/login'), {
    data: { email, password },
  })
  expect(res.ok()).toBeTruthy()
  const body = await res.json()
  return body.tokens.access_token as string
}

test('cross-tenant patient access is blocked', async ({ request }) => {
  const tokenA = await loginAndGetAccessToken(
    request,
    seededUsers.doctorRahman.email,
    seededUsers.doctorRahman.password,
  )
  const tokenB = await loginAndGetAccessToken(
    request,
    seededUsers.doctorKarim.email,
    seededUsers.doctorKarim.password,
  )

  const unique = Date.now()
  const createRes = await request.post(apiUrl('/patients'), {
    headers: { Authorization: `Bearer ${tokenA}` },
    data: {
      first_name: `Tenant${unique}`,
      last_name: 'Locked',
      date_of_birth: '1989-03-12',
      gender: 'male',
      phone: `019${String(unique).slice(-8)}`,
      email: `tenant.locked.${unique}@example.com`,
    },
  })
  expect(createRes.status()).toBe(201)
  const created = await createRes.json()

  const forbiddenRead = await request.get(apiUrl(`/patients/${created.id}`), {
    headers: { Authorization: `Bearer ${tokenB}` },
  })
  expect([403, 404]).toContain(forbiddenRead.status())
})
