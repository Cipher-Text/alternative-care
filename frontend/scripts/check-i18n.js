#!/usr/bin/env node
/**
 * i18n consistency check (run: npm run i18n:check).
 *  1. en and bn have exactly the same keys (after merging the per-area files).
 *  2. Each key has the same {placeholders} in both languages.
 *  3. Every literal t('key') used with useTranslations('ns') / getTranslations('ns') in src/ exists.
 *     (Dynamic keys such as t(`status.${s}`) cannot be checked statically and are skipped.)
 */
const fs = require('node:fs')
const path = require('node:path')

const ROOT = path.join(__dirname, '..')
const MSG = path.join(ROOT, 'src', 'messages')
const AREAS = ['patients', 'prescriptions', 'appointments', 'payments', 'home', 'library', 'symptoms']

function load(locale) {
  const out = JSON.parse(fs.readFileSync(path.join(MSG, `${locale}.json`), 'utf8'))
  for (const area of AREAS) {
    const part = JSON.parse(fs.readFileSync(path.join(MSG, locale, `${area}.json`), 'utf8'))
    for (const ns of Object.keys(part)) {
      if (ns in out) fail(`namespace "${ns}" in ${locale}/${area}.json collides with another file`)
      out[ns] = part[ns]
    }
  }
  return out
}

const errors = []
function fail(msg) { errors.push(msg) }

function flatten(obj, prefix = '', acc = {}) {
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object') flatten(v, key, acc)
    else acc[key] = String(v)
  }
  return acc
}

const en = flatten(load('en'))
const bn = flatten(load('bn'))

for (const k of Object.keys(en)) if (!(k in bn)) fail(`missing in bn: ${k}`)
for (const k of Object.keys(bn)) if (!(k in en)) fail(`missing in en: ${k}`)

const placeholders = (s) => [...s.matchAll(/\{(\w+)/g)].map((m) => m[1]).sort().join(',')
for (const k of Object.keys(en)) {
  if (k in bn && placeholders(en[k]) !== placeholders(bn[k])) {
    fail(`placeholder mismatch in ${k}: en {${placeholders(en[k])}} vs bn {${placeholders(bn[k])}}`)
  }
  if (en[k].trim() === '' || (k in bn && bn[k].trim() === '')) fail(`empty value: ${k}`)
}

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) { if (e.name !== 'messages' && e.name !== 'node_modules') walk(p, out) }
    else if (/\.(tsx?|jsx?)$/.test(e.name)) out.push(p)
  }
  return out
}

let checked = 0
for (const file of walk(path.join(ROOT, 'src'))) {
  const src = fs.readFileSync(file, 'utf8')
  const vars = {}
  for (const m of src.matchAll(/const\s+(\w+)\s*=\s*(?:await\s+)?(?:useTranslations|getTranslations)\(\s*['"]([^'"]+)['"]\s*\)/g)) {
    ;(vars[m[1]] ||= new Set()).add(m[2])
  }
  for (const [v, nsSet] of Object.entries(vars)) {
    const call = new RegExp(`(?<![\\w.])${v}\\(\\s*['"]([^'"]+)['"]`, 'g')
    for (const m of src.matchAll(call)) {
      checked++
      const key = m[1]
      const ok = [...nsSet].some((ns) => `${ns}.${key}` in en)
      if (!ok) fail(`${path.relative(ROOT, file)}: ${v}('${key}') not found in ${[...nsSet].join(' | ')}`)
    }
  }
}

if (errors.length) {
  console.error(errors.map((e) => '  ✖ ' + e).join('\n'))
  console.error(`\n${errors.length} i18n problem(s)`)
  process.exit(1)
}
console.log(`i18n OK: ${Object.keys(en).length} keys in en and bn, ${checked} t() call(s) checked`)
