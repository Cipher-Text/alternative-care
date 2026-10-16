const assert = require('node:assert/strict')
const { test } = require('node:test')

const load = () => import('../../src/components/consultation/visitDraft.ts')
const msgs = { numberInvalid: (min, max) => `${min}-${max}`, bpPair: 'bp pair', bpOrder: 'bp order', sugarPair: 'sugar pair' }

test('a saved visit becomes the strings the form shows, and an empty one the "none" choices', async () => {
  const { draftFromVisit, NONE } = await load()
  const d = draftFromVisit({ visit_date: '2026-10-16', visit_type: 'consultation', chief_complaint: 'Cough', pulse_bpm: 82, bp_systolic: 120, bp_diastolic: 80, weight_kg: 61.5 })
  assert.equal(d.chief_complaint, 'Cough')
  assert.equal(d.pulse_bpm, '82')
  assert.equal(d.bp_systolic, '120')
  assert.equal(d.weight_kg, '61.5')
  assert.equal(d.temperature_c, '')
  assert.equal(d.referral_urgency, NONE)
  assert.equal(d.blood_sugar_type, NONE)
})

test('valid answers become the payload, with numbers as numbers and text trimmed', async () => {
  const { visitPayload } = await load()
  const { errors, payload } = visitPayload(
    { visit_type: 'follow_up', chief_complaint: ' Cough ', temperature_c: '37.2', pulse_bpm: '82', bp_systolic: '120', bp_diastolic: '80', follow_up_date: '2026-10-30', referral_urgency: 'routine' },
    ['chest_pain'],
    msgs
  )
  assert.deepEqual(errors, {})
  assert.equal(payload.chief_complaint, 'Cough')
  assert.equal(payload.temperature_c, 37.2)
  assert.equal(payload.pulse_bpm, 82)
  assert.equal(payload.bp_systolic, 120)
  assert.equal(payload.follow_up_date, '2026-10-30')
  assert.deepEqual(payload.red_flags, ['chest_pain'])
  assert.equal(payload.referral_urgency, 'routine')
})

test('an emptied box is sent as null, so clearing it clears it on the server', async () => {
  const { visitPayload } = await load()
  const { errors, payload } = visitPayload({ visit_type: 'consultation', chief_complaint: '   ', pulse_bpm: '', follow_up_date: '', referral_urgency: '__none', blood_sugar_type: '__none' }, [], msgs)
  assert.deepEqual(errors, {})
  for (const key of ['chief_complaint', 'pulse_bpm', 'follow_up_date', 'referral_urgency', 'red_flags', 'bp_systolic', 'bp_diastolic', 'blood_sugar_mmol', 'blood_sugar_type']) {
    assert.equal(payload[key], null, key)
  }
})

test('out-of-range and incomplete vitals are refused with the problem named', async () => {
  const { visitPayload } = await load()
  const bad = (draft) => visitPayload({ visit_type: 'consultation', ...draft }, [], msgs).errors
  assert.deepEqual(Object.keys(bad({ temperature_c: '50' })), ['temperature_c'])
  assert.deepEqual(Object.keys(bad({ pulse_bpm: '80.5' })), ['pulse_bpm'])
  assert.deepEqual(Object.keys(bad({ pain_score: '11' })), ['pain_score'])
  assert.equal(bad({ bp_systolic: '120' }).bp, 'bp pair')
  assert.equal(bad({ bp_systolic: '80', bp_diastolic: '90' }).bp, 'bp order')
  assert.equal(bad({ blood_sugar_type: 'fasting' }).sugar, 'sugar pair')
  assert.equal(bad({ blood_sugar_mmol: '99' }).sugar, '1-60')
})

test('body mass index needs both measurements', async () => {
  const { bmiOf } = await load()
  assert.equal(bmiOf(70, 175), 22.9)
  assert.equal(bmiOf(70, null), null)
  assert.equal(bmiOf(null, 175), null)
})

test('the case-form fields the medicines section replaces are listed per system', async () => {
  const { SUPERSEDED_BY_MEDICINES } = await load()
  assert.ok(SUPERSEDED_BY_MEDICINES.homeopathy.includes('prescribed'))
  assert.ok(SUPERSEDED_BY_MEDICINES.unani.includes('ilaj_dawa_drug'))
  assert.ok(SUPERSEDED_BY_MEDICINES.ayurveda.includes('formulation'))
})

test('the visit fee comes from the clinic profile (paisa to taka), follow-ups use their own fee when there is one', async () => {
  const { visitFeeBdt } = await load()
  const fees = { consultation_fee: 80000, follow_up_fee: 50000 }
  assert.equal(visitFeeBdt('consultation', fees), 800)
  assert.equal(visitFeeBdt('emergency', fees), 800)
  assert.equal(visitFeeBdt('follow_up', fees), 500)
  assert.equal(visitFeeBdt('follow_up', { consultation_fee: 80000, follow_up_fee: null }), 800)
  assert.equal(visitFeeBdt('consultation', { consultation_fee: 0 }), null)
  assert.equal(visitFeeBdt('consultation', null), null)
})

test('a follow-up can be booked only for a real date that is not before the visit', async () => {
  const { canBookFollowUp } = await load()
  assert.equal(canBookFollowUp('2026-10-22', '2026-10-16'), true)
  assert.equal(canBookFollowUp('2026-10-16', '2026-10-16'), true)
  assert.equal(canBookFollowUp('2026-10-10', '2026-10-16'), false)
  assert.equal(canBookFollowUp('', '2026-10-16'), false)
  assert.equal(canBookFollowUp(undefined, '2026-10-16'), false)
  assert.equal(canBookFollowUp('2026-13-45', '2026-10-16'), false)
  assert.equal(canBookFollowUp('22/10/2026', '2026-10-16'), false)
})
