'use client'

import { useTranslations } from 'next-intl'
import { Globe, Loader2, Mail, MapPin, Clock, Truck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { usePharmacy } from '@/lib/hooks/usePharmacies'
import { directionsLink, formatDistance, telLink, whatsappLink } from '@/lib/utils/contact'
import { ConfirmedNote } from './PharmacyCard'

interface PharmacyDetailDialogProps {
  pharmacyId: number | null
  onClose: () => void
  districtName?: string
  /** Distance from the near-me search, if there is one (the detail endpoint has no location) */
  distanceKm?: number | null
}

/** Everything about one pharmacy: notes, hours, all contact routes. */
export function PharmacyDetailDialog({
  pharmacyId,
  onClose,
  districtName,
  distanceKm,
}: PharmacyDetailDialogProps) {
  const t = useTranslations('pharmUi')
  const { data: p, isLoading, isError } = usePharmacy(pharmacyId, pharmacyId !== null)

  const tel = p && telLink(p.phone)
  const whatsapp = p && whatsappLink(p.whatsapp ?? p.phone)
  const directions = p && directionsLink(p)
  const distance = formatDistance(distanceKm)
  const website = p?.website_url && /^https?:\/\//i.test(p.website_url) ? p.website_url : null

  return (
    <Dialog open={pharmacyId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        {isLoading || (!p && !isError) ? (
          <div className="flex justify-center py-12">
            <DialogTitle className="sr-only">{t('loadingPharmacy')}</DialogTitle>
            <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          </div>
        ) : isError || !p ? (
          <>
            <DialogHeader>
              <DialogTitle>{t('unavailableTitle')}</DialogTitle>
              <DialogDescription>{t('unavailableDesc')}</DialogDescription>
            </DialogHeader>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>{p.name_en}</DialogTitle>
              <DialogDescription>{p.name_bn ?? t(`types.${p.pharmacy_type}`)}</DialogDescription>
            </DialogHeader>

            <div className="space-y-4 text-sm">
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="outline">{t(`types.${p.pharmacy_type}`)}</Badge>
                {p.disciplines.map((d) => (
                  <Badge key={d} variant="outline" className="capitalize">
                    {t(`disciplines.${d}`)}
                  </Badge>
                ))}
                {p.is_verified && <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">{t('verified')}</Badge>}
                {distance && <Badge variant="secondary">{t('distanceAway', { distance })}</Badge>}
              </div>

              <ul className="space-y-2">
                {(p.address || districtName) && (
                  <li className="flex gap-2">
                    <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    {[p.address, districtName].filter(Boolean).join(', ')}
                  </li>
                )}
                {p.opening_hours && (
                  <li className="flex gap-2">
                    <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    {p.opening_hours}
                  </li>
                )}
                {p.delivers && (
                  <li className="flex gap-2 text-emerald-700 dark:text-emerald-400">
                    <Truck className="mt-0.5 h-4 w-4 shrink-0" /> {t('deliversCourier')}
                  </li>
                )}
                {p.email && (
                  <li className="flex gap-2">
                    <Mail className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    <a href={`mailto:${p.email}`} className="text-emerald-700 hover:underline dark:text-emerald-400">
                      {p.email}
                    </a>
                  </li>
                )}
                {website && (
                  <li className="flex gap-2">
                    <Globe className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    <a href={website} target="_blank" rel="noopener noreferrer" className="break-all text-emerald-700 hover:underline dark:text-emerald-400">
                      {website}
                    </a>
                  </li>
                )}
              </ul>

              {(p.notes_en || p.notes_bn) && (
                <div className="space-y-1 rounded-md bg-muted p-3">
                  {p.notes_en && <p>{p.notes_en}</p>}
                  {p.notes_bn && <p>{p.notes_bn}</p>}
                </div>
              )}

              <ConfirmedNote confirmedAt={p.last_confirmed_at} />

              <div className="flex flex-wrap gap-2 border-t pt-4">
                {tel && (
                  <Button asChild className="h-10 flex-1">
                    <a href={tel}>{t('callNumber', { phone: p.phone ?? '' })}</a>
                  </Button>
                )}
                {whatsapp && (
                  <Button asChild variant="outline" className="h-10 flex-1">
                    <a href={whatsapp} target="_blank" rel="noopener noreferrer">{t('whatsapp')}</a>
                  </Button>
                )}
                {directions && (
                  <Button asChild variant="outline" className="h-10 flex-1">
                    <a href={directions} target="_blank" rel="noopener noreferrer">{t('directions')}</a>
                  </Button>
                )}
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
