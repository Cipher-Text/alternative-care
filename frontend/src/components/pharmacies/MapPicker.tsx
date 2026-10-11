'use client'

import { useEffect } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { pinIcon } from './mapIcons'

/** Rough centre of Bangladesh, used when there is no pin and no district chosen yet. */
export const BANGLADESH_CENTER: [number, number] = [23.685, 90.356]

const round = (n: number) => Math.round(n * 1e6) / 1e6

function ClickToPlace({ onChange }: { onChange: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(event) {
      onChange(round(event.latlng.lat), round(event.latlng.lng))
    },
  })
  return null
}

/**
 * Keeps the view in step with the data without fighting the user: a pin placed by clicking is
 * already on screen, so nothing moves; a pin typed in elsewhere (out of view) brings the map to it;
 * and choosing a district (no pin yet) jumps to that district.
 */
function FollowTarget({
  pin,
  fallback,
}: {
  pin: [number, number] | null
  fallback: [number, number] | null
}) {
  const map = useMap()
  const pinLat = pin?.[0]
  const pinLon = pin?.[1]
  const fbLat = fallback?.[0]
  const fbLon = fallback?.[1]

  useEffect(() => {
    if (pinLat === undefined || pinLon === undefined) return
    if (!map.getBounds().contains([pinLat, pinLon])) {
      map.setView([pinLat, pinLon], Math.max(map.getZoom(), 13))
    }
  }, [map, pinLat, pinLon])

  useEffect(() => {
    if (pinLat !== undefined || fbLat === undefined || fbLon === undefined) return
    map.setView([fbLat, fbLon], 11)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only re-centre when the district changes
  }, [map, fbLat, fbLon])

  return null
}

interface MapPickerProps {
  latitude: number | null
  longitude: number | null
  onChange: (lat: number, lon: number) => void
  /** Where to look when there is no pin yet (e.g. the chosen district's centre) */
  fallbackCenter?: [number, number] | null
  height?: number
}

/**
 * Click the map (or drag the pin) to set a location. OpenStreetMap tiles — fine for an admin tool;
 * switch the tile URL to a provider with a usage allowance before heavy public use.
 */
export default function MapPicker({
  latitude,
  longitude,
  onChange,
  fallbackCenter,
  height = 280,
}: MapPickerProps) {
  const hasPin = latitude !== null && longitude !== null
  const center: [number, number] = hasPin
    ? [latitude, longitude]
    : (fallbackCenter ?? BANGLADESH_CENTER)
  const zoom = hasPin ? 15 : fallbackCenter ? 11 : 7

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      scrollWheelZoom
      style={{ height, width: '100%', borderRadius: 8 }}
      aria-label="Map: click to set the pharmacy location"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
      />
      <FollowTarget pin={hasPin ? [latitude, longitude] : null} fallback={fallbackCenter ?? null} />
      <ClickToPlace onChange={onChange} />
      {hasPin && (
        <Marker
          position={[latitude, longitude]}
          icon={pinIcon}
          draggable
          eventHandlers={{
            dragend(event) {
              const { lat, lng } = (event.target as L.Marker).getLatLng()
              onChange(round(lat), round(lng))
            },
          }}
        />
      )}
    </MapContainer>
  )
}
