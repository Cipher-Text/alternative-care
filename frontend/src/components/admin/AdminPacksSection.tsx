'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { useAdminPacks, useCreatePack, useUpdatePack } from '@/lib/hooks/useCheckout'
import { formatMoney } from '@/lib/billingFormat'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { CreditPack } from '@/types/checkout'

function CreateForm() {
  const t = useTranslations('billingUi.adminBilling.packs')
  const tc = useTranslations('billingUi.channel')
  const create = useCreatePack()
  const [channel, setChannel] = useState<'sms' | 'email'>('sms')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [nameEn, setNameEn] = useState('')
  const [nameBn, setNameBn] = useState('')
  const [sort, setSort] = useState('0')
  const [invalid, setInvalid] = useState(false)

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const q = Number(quantity)
    const p = Number(price)
    const s = Number(sort)
    if (!Number.isInteger(q) || q <= 0 || !Number.isFinite(p) || p < 0 || price.trim() === '' || !nameEn.trim() || !Number.isInteger(s)) {
      setInvalid(true)
      return
    }
    setInvalid(false)
    try {
      await create.mutateAsync({
        channel,
        quantity: q,
        price: p,
        name_en: nameEn.trim(),
        name_bn: nameBn.trim() || null,
        sort_order: s,
      })
      setQuantity('')
      setPrice('')
      setNameEn('')
      setNameBn('')
    } catch {
      /* the mutation's onError already showed the server's reason */
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-4 rounded-lg border p-4">
      <h3 className="font-semibold">{t('createTitle')}</h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-1.5">
          <Label>{t('channel')}</Label>
          <Select value={channel} onValueChange={(v) => setChannel(v as 'sms' | 'email')}>
            <SelectTrigger aria-label={t('channel')}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="sms">{tc('sms')}</SelectItem>
              <SelectItem value="email">{tc('email')}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pack-qty">{t('quantity')}</Label>
          <Input id="pack-qty" inputMode="numeric" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pack-price">{t('price')}</Label>
          <Input id="pack-price" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pack-name-en">{t('nameEn')}</Label>
          <Input id="pack-name-en" maxLength={120} value={nameEn} onChange={(e) => setNameEn(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pack-name-bn">{t('nameBn')}</Label>
          <Input id="pack-name-bn" maxLength={120} value={nameBn} onChange={(e) => setNameBn(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pack-sort">{t('sortOrder')}</Label>
          <Input id="pack-sort" inputMode="numeric" value={sort} onChange={(e) => setSort(e.target.value)} />
        </div>
      </div>
      {invalid && <p role="alert" className="text-sm text-red-600">{t('invalid')}</p>}
      <p className="text-xs text-muted-foreground">{t('fixedNote')}</p>
      <Button type="submit" className="h-10" disabled={create.isLoading}>
        {create.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
        {t('create')}
      </Button>
    </form>
  )
}

function EditDialog({ pack, onClose }: { pack: CreditPack | null; onClose: () => void }) {
  const t = useTranslations('billingUi.adminBilling.packs')
  const tc = useTranslations('billingUi.channel')
  const update = useUpdatePack()
  const [price, setPrice] = useState('')
  const [nameEn, setNameEn] = useState('')
  const [nameBn, setNameBn] = useState('')
  const [sort, setSort] = useState('0')
  const [active, setActive] = useState(true)
  const [invalid, setInvalid] = useState(false)
  const [loadedId, setLoadedId] = useState<number | null>(null)

  // Load the form when a different pack is opened
  if (pack && pack.id !== loadedId) {
    setLoadedId(pack.id)
    setPrice(String(Number(pack.price)))
    setNameEn(pack.name_en)
    setNameBn(pack.name_bn ?? '')
    setSort(String(pack.sort_order))
    setActive(pack.is_active)
    setInvalid(false)
  }

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!pack) return
    const p = Number(price)
    const s = Number(sort)
    if (price.trim() === '' || !Number.isFinite(p) || p < 0 || !nameEn.trim() || !Number.isInteger(s)) {
      setInvalid(true)
      return
    }
    try {
      await update.mutateAsync({
        id: pack.id,
        data: { price: p, name_en: nameEn.trim(), name_bn: nameBn.trim() || null, sort_order: s, is_active: active },
      })
      onClose()
    } catch {
      /* toast shown by the mutation */
    }
  }

  return (
    <Dialog open={pack !== null} onOpenChange={(open) => { if (!open) { setLoadedId(null); onClose() } }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('editTitle')}</DialogTitle>
          <DialogDescription>
            {pack ? t('readOnlyInfo', { channel: tc(pack.channel), quantity: pack.quantity }) : ''}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} noValidate className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="edit-price">{t('price')}</Label>
            <Input id="edit-price" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="edit-name-en">{t('nameEn')}</Label>
            <Input id="edit-name-en" maxLength={120} value={nameEn} onChange={(e) => setNameEn(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="edit-name-bn">{t('nameBn')}</Label>
            <Input id="edit-name-bn" maxLength={120} value={nameBn} onChange={(e) => setNameBn(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="edit-sort">{t('sortOrder')}</Label>
            <Input id="edit-sort" inputMode="numeric" value={sort} onChange={(e) => setSort(e.target.value)} />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
            {t('activeHelp')}
          </label>
          {invalid && <p role="alert" className="text-sm text-red-600">{t('invalid')}</p>}
          <div className="flex gap-2">
            <Button type="submit" className="h-10" disabled={update.isLoading}>
              {update.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('save')}
            </Button>
            <Button type="button" variant="outline" className="h-10" onClick={() => { setLoadedId(null); onClose() }}>
              {t('cancel')}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function AdminPacksSection() {
  const t = useTranslations('billingUi.adminBilling.packs')
  const tc = useTranslations('billingUi.channel')
  const packs = useAdminPacks()
  const [editing, setEditing] = useState<CreditPack | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('title')}</CardTitle>
        <CardDescription>{t('description')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {packs.isLoading ? (
          <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
        ) : packs.error ? (
          <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
        ) : (packs.data ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('empty')}</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('channel')}</TableHead>
                  <TableHead className="text-right">{t('quantity')}</TableHead>
                  <TableHead className="text-right">{t('price')}</TableHead>
                  <TableHead>{t('nameEn')}</TableHead>
                  <TableHead>{t('nameBn')}</TableHead>
                  <TableHead className="text-right">{t('sortOrder')}</TableHead>
                  <TableHead>{t('status')}</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(packs.data ?? []).map((p) => (
                  <TableRow key={p.id}>
                    <TableCell>{tc(p.channel)}</TableCell>
                    <TableCell className="text-right tabular-nums">{p.quantity}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatMoney(p.price, p.currency)}</TableCell>
                    <TableCell>{p.name_en}</TableCell>
                    <TableCell>{p.name_bn || '-'}</TableCell>
                    <TableCell className="text-right tabular-nums">{p.sort_order}</TableCell>
                    <TableCell>
                      <Badge variant={p.is_active ? 'default' : 'outline'}>{p.is_active ? t('active') : t('inactive')}</Badge>
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => setEditing(p)}>{t('edit')}</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        <CreateForm />
        <EditDialog pack={editing} onClose={() => setEditing(null)} />
      </CardContent>
    </Card>
  )
}
