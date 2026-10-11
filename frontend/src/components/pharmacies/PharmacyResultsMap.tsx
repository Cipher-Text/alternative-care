'use client'

import { useEffect } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { BANGLADESH_CENTER } from './MapPicker'
import { pinIcon, youIcon } from './mapIcons'
import { directionsLink, formatDistance, telLink } from '@/lib/utils/contact'
import type { PharmacyListItem } from '@/types/pharmacy'

/** Zooms to fit every pharmacy (and the practitioner's position, if known). */
function FitToResults({
  points,
}: {
  points: Array<[number, number]>
}) {
  const map = useMap()
  // A stable key so the view only changes when the set of points changes, not on every render
  const key = points.map((p) => p.join(',')).join('|')

  useEffect(() => {
    if (points.length === 0) return
    if (points.length === 1) {
      map.setView(points[0], 14)
      return
    }
    map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 15 })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` captures `points`
  }, [map, key])

  return null
}

interface PharmacyResultsMapProps {
  pharmacies: PharmacyListItem[]
  you: { lat: number; lon: number } | null
  onOpenDetails: (id: number) => void
  height?: number
}

/** Read-only map of search results: tap a pin for the name, distance, and call / directions. */
export default function PharmacyResultsMap({
  pharmacies,
  you,
  onOpenDetails,
  height = 520,
}: PharmacyResultsMapProps) {
  const pinned = pharmacies.filter(
    (p): p is PharmacyListItem & { latitude: number; longitude: number } =>
      p.latitude !== null && p.longitude !== null
  )
  const points: Array<[number, number]> = pinned.map((p) => [p.latitude, p.longitude])
  if (you) points.push([you.lat, you.lon])

  return (
    <MapContainer
      center={points[0] ?? BANGLADESH_CENTER}
      zoom={points.length ? 12 : 7}
      scrollWheelZoom
      style={{ height, width: '100%', borderRadius: 8 }}
      aria-label="Map of pharmacies"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
      />
      <FitToResults points={points} />

      {you && <Marker position={[you.lat, you.lon]} icon={youIcon} zIndexOffset={1000} />}

      {pinned.map((p) => {
        const tel = telLink(p.phone)
        const directions = directionsLink(p)
        const distance = formatDistance(p.distance_km)
        return (
          <Marker key={p.id} position={[p.latitude, p.longitude]} icon={pinIcon}>
            <Popup>
              <div className="space-y-1 text-sm">
                <div className="font-semibold">{p.name_en}</div>
                {p.name_bn && <div className="text-gray-600">{p.name_bn}</div>}
                {distance && <div className="text-emerald-700">{distance} away</div>}
                {p.address && <div className="text-gray-600">{p.address}</div>}
                <div className="flex flex-wrap gap-x-3 gap-y-1 pt-1">
                  {tel && (
                    <a href={tel} className="font-medium text-emerald-700 underline">
                      Call
                    </a>
                  )}
                  {directions && (
                    <a href={directions} target="_blank" rel="noopener noreferrer" className="font-medium text-emerald-700 underline">
                      Directions
                    </a>
                  )}
                  <button type="button" onClick={() => onOpenDetails(p.id)} className="font-medium text-emerald-700 underline">
                    Details
                  </button>
                </div>
              </div>
            </Popup>
          </Marker>
        )
      })}
    </MapContainer>
  )
}
