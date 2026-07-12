const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { test } = require('node:test')
const { join } = require('node:path')

const providersSource = readFileSync(join(__dirname, '../../src/app/providers.tsx'), 'utf8')
const loginPageSource = readFileSync(
  join(__dirname, '../../src/app/(auth)/login/page.tsx'),
  'utf8'
)
const dashboardLayoutSource = readFileSync(
  join(__dirname, '../../src/app/(dashboard)/layout.tsx'),
  'utf8'
)

test('toast notifications are mounted once at the root with finite success duration', () => {
  assert.match(providersSource, /<ThemedToaster \/>/)
  assert.match(providersSource, /success:\s*\{[\s\S]*duration:\s*3000/)

  assert.doesNotMatch(loginPageSource, /<Toaster/)
  assert.doesNotMatch(dashboardLayoutSource, /<Toaster/)
})
