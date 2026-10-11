const assert = require('node:assert/strict')
const { test } = require('node:test')
const { join } = require('node:path')
const { pathToFileURL } = require('node:url')

const load = () => import(pathToFileURL(join(__dirname, '../../src/lib/utils/contact.ts')).href)

test('whatsapp numbers are normalised to international form', async () => {
  const { whatsappNumber } = await load()
  assert.equal(whatsappNumber('01711-000000'), '8801711000000') // local BD
  assert.equal(whatsappNumber('+880 1711 000000'), '8801711000000') // already international
  assert.equal(whatsappNumber('008801711000000'), '8801711000000') // 00 prefix
  assert.equal(whatsappNumber('8801711000000'), '8801711000000')
  assert.equal(whatsappNumber('+1 (415) 555-0100'), '14155550100') // non-BD kept as is
})

test('whatsapp rejects values that cannot be a phone number', async () => {
  const { whatsappNumber, whatsappLink } = await load()
  for (const bad of [null, undefined, '', '   ', 'call us', '123', '0', '+'.repeat(3), '9'.repeat(20)]) {
    assert.equal(whatsappNumber(bad), null, String(bad))
    assert.equal(whatsappLink(bad), null, String(bad))
  }
})

test('whatsapp link can carry an encoded message', async () => {
  const { whatsappLink } = await load()
  assert.equal(whatsappLink('01711000000'), 'https://wa.me/8801711000000')
  assert.equal(
    whatsappLink('01711000000', 'Do you have Arnica 30C?'),
    'https://wa.me/8801711000000?text=Do%20you%20have%20Arnica%2030C%3F'
  )
})

test('tel links keep +, drop punctuation, and ignore junk', async () => {
  const { telLink } = await load()
  assert.equal(telLink('+880 1711-000 000'), 'tel:+8801711000000')
  assert.equal(telLink('(02) 9876543'), 'tel:029876543')
  assert.equal(telLink('n/a'), null)
  assert.equal(telLink(''), null)
  assert.equal(telLink(null), null)
})

test('directions prefer the pin and fall back to the address', async () => {
  const { directionsLink } = await load()
  assert.equal(
    directionsLink({ latitude: 23.78, longitude: 90.41, address: 'x' }),
    'https://www.google.com/maps/dir/?api=1&destination=23.78,90.41'
  )
  // a pin at exactly 0,0 or a negative coordinate is still a pin
  assert.match(directionsLink({ latitude: 0, longitude: -1 }), /destination=0,-1$/)
  assert.equal(
    directionsLink({ latitude: null, longitude: null, name: 'Alpha Homeo', address: 'Mitford Road, Dhaka' }),
    'https://www.google.com/maps/dir/?api=1&destination=Alpha%20Homeo%2C%20Mitford%20Road%2C%20Dhaka'
  )
  assert.equal(directionsLink({ latitude: null, longitude: null }), null)
})

test('distances read naturally', async () => {
  const { formatDistance } = await load()
  assert.equal(formatDistance(0), '10 m')
  assert.equal(formatDistance(0.85), '850 m')
  assert.equal(formatDistance(1.74), '1.7 km')
  assert.equal(formatDistance(23.4), '23 km')
  assert.equal(formatDistance(null), null)
  assert.equal(formatDistance(-1), null)
  assert.equal(formatDistance(Number.NaN), null)
})
