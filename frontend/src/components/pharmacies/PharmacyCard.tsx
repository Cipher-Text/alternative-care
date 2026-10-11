'use client'

import { differenceInCalendarDays, format } from 'date-fns'
import { BadgeCheck, Clock, MapPin, MessageCircle, Navigation, Phone, Truck, TriangleAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { directionsLink, formatDistance, telLink, whatsappLink } from '@/lib/utils/contact'
import { PHARMACY_TYPES, STALE_AFTER_DAYS, type PharmacyListItem } from '@/types/pharmacy'

export const typeLabel = (type: string) => PHARMACY_TYPES.find((t) => t.value === type)?.label ?? type

/** When this listing was last checked — and a plain warning when that was too long ago. */
export function ConfirmedNote({ confirmedAt }: { confirmedAt: string | null }) {
  if (!confirmedAt) {
    return (
      <p className="flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-400">
        <TriangleAlert className="h-3.5 w-3.5 shrink-0" />
        Not yet confirmed — please call before you go
      </p>
    )
  }
  const days = differenceInCalendarDays(new Date(), new Date(confirmedAt))
  const stale = days > STALE_AFTER_DAYS
  return (
    <p className={`flex items-center gap-1.5 text-xs ${stale ? 'text-amber-700 dark:text-amber-400' : 'text-muted-foreground'}`}>
      {stale && <TriangleAlert className="h-3.5 w-3.5 shrink-0" />}
      Confirmed {format(new Date(confirmedAt), 'MMM d, yyyy')}
      {stale && ' — may be out of date, please call first'}
    </p>
  )
}

interface PharmacyCardProps {
  pharmacy: PharmacyListItem
  districtName?: string
  onOpenDetails: (id: number) => void
}

/** Action buttons are 40px tall so they are easy to hit with a thumb. */
const actionClass = 'h-10 flex-1 min-w-[5.5rem]'

export function PharmacyCard({ pharmacy, districtName, onOpenDetails }: PharmacyCardProps) {
  const tel = telLink(pharmacy.phone)
  const whatsapp = whatsappLink(pharmacy.whatsapp ?? pharmacy.phone)
  const directions = directionsLink(pharmacy)
  const distance = formatDistance(pharmacy.distance_km)

  return (
    <Card className="flex h-full flex-col">
      <CardContent className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h2 className="text-base font-semibold leading-snug">{pharmacy.name_en}</h2>
            {pharmacy.name_bn && <p className="text-sm text-muted-foreground">{pharmacy.name_bn}</p>}
          </div>
          {distance && (
            <Badge className="shrink-0 bg-emerald-600 text-white hover:bg-emerald-600">{distance}</Badge>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="outline">{typeLabel(pharmacy.pharmacy_type)}</Badge>
          {pharmacy.disciplines.map((d) => (
            <Badge key={d} variant="outline" className="capitalize">
              {d}
            </Badge>
          ))}
          {pharmacy.is_verified && (
            <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">
              <BadgeCheck className="mr-1 h-3.5 w-3.5" /> Verified
            </Badge>
          )}
        </div>

        <div className="space-y-1 text-sm">
          {(pharmacy.address || districtName) && (
            <p className="flex items-start gap-1.5">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <span>{[pharmacy.address, districtName].filter(Boolean).join(', ')}</span>
            </p>
          )}
          {pharmacy.opening_hours && (
            <p className="flex items-start gap-1.5">
              <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <span>{pharmacy.opening_hours}</span>
            </p>
          )}
          {pharmacy.delivers && (
            <p className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400">
              <Truck className="h-4 w-4 shrink-0" /> Delivers
            </p>
          )}
        </div>

        <ConfirmedNote confirmedAt={pharmacy.last_confirmed_at} />

        <div className="mt-auto flex flex-wrap gap-2 pt-1">
          {tel && (
            <Button asChild variant="outline" className={actionClass}>
              <a href={tel} aria-label={`Call ${pharmacy.name_en}`}>
                <Phone className="mr-1.5 h-4 w-4" /> Call
              </a>
            </Button>
          )}
          {whatsapp && (
            <Button asChild variant="outline" className={actionClass}>
              <a href={whatsapp} target="_blank" rel="noopener noreferrer" aria-label={`WhatsApp ${pharmacy.name_en}`}>
                <MessageCircle className="mr-1.5 h-4 w-4" /> WhatsApp
              </a>
            </Button>
          )}
          {directions && (
            <Button asChild variant="outline" className={actionClass}>
              <a href={directions} target="_blank" rel="noopener noreferrer" aria-label={`Directions to ${pharmacy.name_en}`}>
                <Navigation className="mr-1.5 h-4 w-4" /> Directions
              </a>
            </Button>
          )}
          <Button variant="ghost" className={actionClass} onClick={() => onOpenDetails(pharmacy.id)} aria-label={`Details for ${pharmacy.name_en}`}>
            Details
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
