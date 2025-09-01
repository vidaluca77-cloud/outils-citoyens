import './globals.css'
import { Metadata } from 'next'
import { AppShell } from '../components/AppShell'
// Client component for environment check
function EnvironmentBanner() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE
  
  if (apiBase) {
    return null
  }
  return (
    <div className="bg-red-600 text-white p-3 text-center text-sm font-medium">
      ⚠️ Configuration manquante: NEXT_PUBLIC_API_BASE n&apos;est pas définie. Les fonctionnalités sont désactivées.
    </div>
  )
}
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
        
        {/* Additional meta tags moved to metadata export */}
      </head>
      <body className="font-sans antialiased">
        <EnvironmentBanner/>
        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  )
}
export const metadata: Metadata = {
  metadataBase: new URL('https://outils-citoyens.vercel.app'),
  title: {
    default: 'Outils Citoyens — Générer vos courriers & démarches',
    template: '%s — Outils Citoyens'
  },
  description: '12 outils gratuits pour lettres et procédures (amendes, CAF, loyers, travail, santé…).',
  keywords: ['lettres administratives', 'outils citoyens', 'générateur', 'France', 'démarches', 'courriers', 'amendes', 'CAF', 'loyers'],
  authors: [{ name: 'Outils Citoyens' }],
  openGraph: {
    title: 'Outils Citoyens — Générer vos courriers & démarches',
    description: '12 outils gratuits pour lettres et procédures (amendes, CAF, loyers, travail, santé…).',
    url: 'https://outils-citoyens.vercel.app',
    siteName: 'Outils Citoyens',
    locale: 'fr_FR',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Outils Citoyens — Générer vos courriers & démarches',
    description: '12 outils gratuits pour lettres et procédures (amendes, CAF, loyers, travail, santé…).',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
    apple: '/icons/icon-192.png',
  },
}
