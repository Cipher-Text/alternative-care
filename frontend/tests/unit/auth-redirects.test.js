const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { test } = require('node:test')
const { join } = require('node:path')

const redirectsSource = readFileSync(
  join(__dirname, '../../src/lib/auth/redirects.ts'),
  'utf8'
)
const dashboardSource = readFileSync(
  join(__dirname, '../../src/app/(dashboard)/dashboard/page.tsx'),
  'utf8'
)

test('platform admins and operators are routed to the platform dashboard', () => {
  assert.match(redirectsSource, /tenant_id === null/)
  assert.match(redirectsSource, /role === 'admin'/)
  assert.match(redirectsSource, /role === 'operator'/)
  assert.match(redirectsSource, /return '\/admin\/dashboard'/)
})

test('tenant dashboard redirects platform users before mounting analytics hooks', () => {
  assert.match(dashboardSource, /router\.replace\('\/admin\/dashboard'\)/)
  assert.match(dashboardSource, /return <TenantDashboardContent userName=\{user\?\.full_name\} \/>/)

  const guardIndex = dashboardSource.indexOf('return <TenantDashboardContent')
  const childComponentIndex = dashboardSource.indexOf('function TenantDashboardContent')
  const hooksIndex = dashboardSource.indexOf('useOverviewStats', childComponentIndex)
  assert.ok(guardIndex > 0)
  assert.ok(childComponentIndex > guardIndex)
  assert.ok(hooksIndex > guardIndex)
})
