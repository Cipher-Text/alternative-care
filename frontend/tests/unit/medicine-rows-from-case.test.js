const assert = require('node:assert/strict')
const { test } = require('node:test')

// Node strips the types from the .ts file, so the real module is tested, not a copy.
const load = () => import('../../src/lib/prescriptions/medicineRowsFromCase.ts')
const label = (key, code) => (code ? `${key}:${code}` : `${key}!`)

test('homeopathy: the medicines list becomes rows, with potency', async () => {
  const { medicineRowsFromCase } = await load()
  const rows = medicineRowsFromCase(
    'homeopathy',
    { prescribed: [{ kind: 'dilution', name: 'Arnica', potency: '30C' }, { kind: 'mother_tincture', name: 'Thuja Q' }, { kind: 'other' }, { name: '  ' }] },
    label
  )
  assert.deepEqual(rows.map((r) => r.medicine_name), ['Arnica 30C', 'Thuja Q'])
  assert.deepEqual(rows.map((r) => r.display_order), [0, 1])
  assert.equal(rows[0].dosage, '')
  assert.equal(rows[0].frequency, '')
})

test('homeopathy: the older single remedy fills dose form and repetition from its labels', async () => {
  const { medicineRowsFromCase } = await load()
  const [r] = medicineRowsFromCase('homeopathy', { remedy: 'Belladonna', potency: '200c', dose_form: 'pills', repetition: 'twice_daily' }, label)
  assert.equal(r.medicine_name, 'Belladonna potency:200c')
  assert.equal(r.dosage, 'dose_form:pills')
  assert.equal(r.frequency, 'repetition:twice_daily')
})

test('homeopathy: the medicines list wins over the single remedy', async () => {
  const { medicineRowsFromCase } = await load()
  const rows = medicineRowsFromCase('homeopathy', { remedy: 'Old', prescribed: [{ name: 'New', potency: '6X' }] }, label)
  assert.deepEqual(rows.map((r) => r.medicine_name), ['New 6X'])
})

test('unani and ayurveda: the named drug becomes a row', async () => {
  const { medicineRowsFromCase } = await load()
  const [u] = medicineRowsFromCase('unani', { ilaj_dawa_drug: 'Sharbat-e-Bazoori', drug_form: 'sharbat' }, label)
  assert.equal(u.medicine_name, 'Sharbat-e-Bazoori')
  assert.equal(u.dosage, 'drug_form:sharbat')
  const [a] = medicineRowsFromCase('ayurveda', { formulation: 'Triphala churna', anupana: 'honey' }, label)
  assert.equal(a.medicine_name, 'Triphala churna')
  assert.equal(a.instructions, 'anupana!: anupana:honey')
})

test('nothing recorded, or an unknown system, gives no rows', async () => {
  const { medicineRowsFromCase } = await load()
  assert.deepEqual(medicineRowsFromCase('homeopathy', {}, label), [])
  assert.deepEqual(medicineRowsFromCase('unani', { ilaj_dawa_drug: '   ' }, label), [])
  assert.deepEqual(medicineRowsFromCase('herbal', { remedy: 'x' }, label), [])
})
