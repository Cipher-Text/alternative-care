import { ImageResponse } from 'next/og'

export const alt = 'AltCare — clinic software for alternative medicine practitioners'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: 80,
          background: '#0f172a',
          color: 'white',
        }}
      >
        <div style={{ fontSize: 112, fontWeight: 700 }}>AltCare</div>
        <div style={{ fontSize: 40, marginTop: 24, color: '#6ee7b7' }}>
          Homeopathy · Ayurveda · Unani · Herbal
        </div>
        <div style={{ fontSize: 32, marginTop: 16, color: '#cbd5e1' }}>
          Clinic software for alternative medicine practitioners
        </div>
      </div>
    ),
    size
  )
}
