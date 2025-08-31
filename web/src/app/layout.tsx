import './globals.css'
import { Metadata } from 'next'
import { AppShell } from '../components/AppShell'

export default function RootLayout({children}:{children:React.ReactNode}) {
  return (
    <html lang='fr'>
      <head>
        {/* PWA Meta Tags */}
        <meta name="theme-color" content="#0B0D12" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Outils Citoyens" />
        
        {/* Icons */}
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
        <link rel="manifest" href="/manifest.json" />
        
        {/* Viewport */}
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        
        {/* SEO */}
        <meta name="description" content="12 outils gratuits pour générer des lettres et procédures administratives" />
        <meta name="keywords" content="lettres administratives, outils citoyens, générateur, France" />
      </head>
      <body className="font-sans antialiased">
        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  )
}

export const metadata: Metadata = {
  title: 'Outils Citoyens – Générateur de lettres administratives',
  description: '12 outils gratuits pour générer des lettres et procédures administratives',
}