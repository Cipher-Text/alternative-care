const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { test } = require('node:test')
const { join } = require('node:path')

const source = readFileSync(join(__dirname, '../../src/lib/api/payments.ts'), 'utf8')

test('payments API client uses API-version-relative base path', () => {
  assert.match(source, /const BASE_PATH = ['"]\/payments['"]/)
  assert.doesNotMatch(source, /const BASE_PATH = ['"]\/api\/v1\/payments['"]/)
})

test('payments API client builds invoice and bKash paths from the shared base path', () => {
  assert.match(source, /\`\$\{BASE_PATH\}\/bkash\/create\`/)
  assert.match(source, /\`\$\{BASE_PATH\}\/invoices\`/)
  assert.doesNotMatch(source, /\/api\/v1\/api\/v1\/payments/)
})
