'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { useSaveListing } from '@/lib/hooks/useDirectory'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AVAILABILITY_OPTIONS, type Availability, type Listing } from '@/types/directory'

const HEADLINE_MAX = 200
const BIO_MAX = 3000
const LANGUAGES_MAX = 8

interface FormState {
  is_listed: boolean
  headline_en: string
  headline_bn: string
  bio_en: string
  bio_bn: string
  languages: string
  consultation_hours: string
  availability: Availability
  show_fee: boolean
  show_phone: boolean
  show_whatsapp: boolean
  accepts_requests: boolean
}

function fromListing(l: Listing): FormState {
  return {
    is_listed: l.is_listed,
    headline_en: l.headline_en ?? '',
    headline_bn: l.headline_bn ?? '',
    bio_en: l.bio_en ?? '',
    bio_bn: l.bio_bn ?? '',
    languages: (l.languages ?? []).join(', '),
    consultation_hours: l.consultation_hours ?? '',
    availability: l.availability,
    show_fee: l.show_fee,
    show_phone: l.show_phone,
    show_whatsapp: l.show_whatsapp,
    accepts_requests: l.accepts_requests,
  }
}

function parseLanguages(text: string): string[] {
  const seen = new Set<string>()
  for (const part of text.split(/[,،]/)) {
    const value = part.trim()
    if (value) seen.add(value)
  }
  return [...seen]
}

function Field({ id, label, hint, children }: { id: string; label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}

function CheckRow({
  id,
  checked,
  onChange,
  label,
  hint,
}: {
  id: string
  checked: boolean
  onChange: (value: boolean) => void
  label: string
  hint?: string
}) {
  return (
    <div className="flex items-start gap-3">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1 h-5 w-5 shrink-0 rounded border-gray-300 accent-emerald-600"
      />
      <div className="space-y-0.5">
        <Label htmlFor={id} className="cursor-pointer">{label}</Label>
        {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
      </div>
    </div>
  )
}

/** Remounts when the saved listing changes, so the form always starts from what the server holds. */
export function ListingForm({ listing }: { listing: Listing }) {
  return <Form key={JSON.stringify(fromListing(listing))} listing={listing} />
}

function Form({ listing }: { listing: Listing }) {
  const t = useTranslations('directoryAdminUi')
  const initial = fromListing(listing)
  const [form, setForm] = useState<FormState>(initial)
  const [lang, setLang] = useState<'en' | 'bn'>('en')
  const save = useSaveListing()

  const dirty = JSON.stringify(form) !== JSON.stringify(initial)
  const languageList = parseLanguages(form.languages)
  const tooMany = languageList.length > LANGUAGES_MAX

  // Warn before closing the tab with unsaved changes
  useEffect(() => {
    if (!dirty) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [dirty])

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }))

  const onSave = async () => {
    if (tooMany) return
    try {
      await save.mutateAsync({
        is_listed: form.is_listed,
        headline_en: form.headline_en.trim(),
        headline_bn: form.headline_bn.trim(),
        bio_en: form.bio_en.trim(),
        bio_bn: form.bio_bn.trim(),
        languages: languageList,
        consultation_hours: form.consultation_hours.trim(),
        availability: form.availability,
        show_fee: form.show_fee,
        show_phone: form.show_phone,
        show_whatsapp: form.show_whatsapp,
        accepts_requests: form.accepts_requests,
      })
    } catch {
      /* the mutation's onError already showed the reason */
    }
  }

  const renderLang = (l: 'en' | 'bn') => {
    const headline = form[`headline_${l}`]
    const bio = form[`bio_${l}`]
    return (
      <div className="space-y-4">
        <Field
          id={`headline_${l}`}
          label={t('form.headline')}
          hint={`${t('form.headlineHint', { max: HEADLINE_MAX })} (${headline.length}/${HEADLINE_MAX})`}
        >
          <Input
            id={`headline_${l}`}
            lang={l}
            maxLength={HEADLINE_MAX}
            value={headline}
            onChange={(e) => set(`headline_${l}`, e.target.value)}
          />
        </Field>
        <Field
          id={`bio_${l}`}
          label={t('form.bio')}
          hint={`${t('form.bioHint', { max: BIO_MAX })} (${bio.length}/${BIO_MAX})`}
        >
          <Textarea
            id={`bio_${l}`}
            lang={l}
            rows={9}
            maxLength={BIO_MAX}
            value={bio}
            onChange={(e) => set(`bio_${l}`, e.target.value)}
          />
        </Field>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{t('form.title')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <CheckRow
          id="is_listed"
          checked={form.is_listed}
          onChange={(v) => set('is_listed', v)}
          label={t('form.enable')}
          hint={t('form.enableHint')}
        />

        <Tabs value={lang} onValueChange={(v) => setLang(v as 'en' | 'bn')}>
          <TabsList>
            <TabsTrigger value="en" className="min-h-9">{t('form.lang.en')}</TabsTrigger>
            <TabsTrigger value="bn" className="min-h-9">{t('form.lang.bn')}</TabsTrigger>
          </TabsList>
          <TabsContent value="en" className="mt-4">{renderLang('en')}</TabsContent>
          <TabsContent value="bn" className="mt-4">{renderLang('bn')}</TabsContent>
        </Tabs>

        <div className="grid gap-4 md:grid-cols-2">
          <Field id="languages" label={t('form.languages')} hint={t('form.languagesHint', { max: LANGUAGES_MAX })}>
            <Input
              id="languages"
              value={form.languages}
              placeholder={t('form.languagesPlaceholder')}
              onChange={(e) => set('languages', e.target.value)}
              aria-invalid={tooMany}
            />
            {tooMany && (
              <p role="alert" className="text-sm text-red-600">{t('form.tooManyLanguages', { max: LANGUAGES_MAX })}</p>
            )}
          </Field>
          <Field id="availability" label={t('form.availability')}>
            <Select value={form.availability} onValueChange={(v) => set('availability', v as Availability)}>
              <SelectTrigger id="availability" aria-label={t('form.availability')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AVAILABILITY_OPTIONS.map((o) => (
                  <SelectItem key={o} value={o}>{t(`form.availabilityOptions.${o}`)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <div className="md:col-span-2">
            <Field id="hours" label={t('form.hours')} hint={t('form.hoursHint')}>
              <Input
                id="hours"
                maxLength={500}
                value={form.consultation_hours}
                onChange={(e) => set('consultation_hours', e.target.value)}
              />
            </Field>
          </div>
        </div>

        <fieldset className="space-y-4">
          <legend className="mb-2 text-sm font-semibold">{t('form.privacy')}</legend>
          <CheckRow id="show_fee" checked={form.show_fee} onChange={(v) => set('show_fee', v)}
            label={t('form.showFee')} hint={t('form.showFeeHint')} />
          <CheckRow id="show_phone" checked={form.show_phone} onChange={(v) => set('show_phone', v)}
            label={t('form.showPhone')} hint={t('form.showPhoneHint')} />
          <CheckRow id="show_whatsapp" checked={form.show_whatsapp} onChange={(v) => set('show_whatsapp', v)}
            label={t('form.showWhatsapp')} hint={t('form.showWhatsappHint')} />
          <CheckRow id="accepts_requests" checked={form.accepts_requests} onChange={(v) => set('accepts_requests', v)}
            label={t('form.acceptsRequests')} hint={t('form.acceptsRequestsHint')} />
        </fieldset>

        <div className="rounded-lg border bg-muted/40 p-4 text-sm">
          <p className="font-semibold">{t('form.alwaysShown')}</p>
          <p className="mt-1 text-muted-foreground">{t('form.alwaysShownText')}</p>
          <div className="mt-3 flex flex-wrap gap-4">
            <Link href="/profile" className="font-medium text-primary underline">{t('form.profileLink')}</Link>
            <Link href="/settings" className="font-medium text-primary underline">{t('form.settingsLink')}</Link>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={onSave} disabled={!dirty || save.isLoading || tooMany} className="h-10">
            {save.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {save.isLoading ? t('form.saving') : t('form.save')}
          </Button>
          {dirty && (
            <Button variant="ghost" onClick={() => setForm(initial)} disabled={save.isLoading} className="h-10">
              {t('form.discard')}
            </Button>
          )}
          <span className="text-sm text-muted-foreground" aria-live="polite">
            {dirty ? t('form.unsaved') : t('form.saved')}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
