import { ImageResponse } from 'next/og'

export const runtime = 'edge'

export const alt = 'Outils Citoyens — Générer vos courriers & démarches'
export const size = {
  width: 1200,
  height: 630,
}
export const contentType = 'image/png'

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 60,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          textAlign: 'center',
          padding: '60px',
        }}
      >
        <div style={{ fontSize: 80, fontWeight: 'bold', marginBottom: 30 }}>
          🇫🇷 Outils Citoyens
        </div>
        <div style={{ fontSize: 40, opacity: 0.9, maxWidth: '80%' }}>
          12 outils gratuits pour générer vos courriers & démarches administratives
        </div>
      </div>
    ),
    {
      ...size,
    }
  )
}