import './globals.css'
import { Metadata } from 'next'

export default function RootLayout({children}:{children:React.ReactNode}) {
  return (
    <html lang='fr'>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="12 outils gratuits pour générer des lettres et procédures administratives" />
      </head>
      <body className="font-sans antialiased">
        <div className="container mx-auto max-w-3xl px-4">
          {children}
        </div>
      </body>
    </html>
  )
}

export const metadata: Metadata = {
  title: 'Outils Citoyens – Générateur de lettres administratives',
  description: '12 outils gratuits pour générer des lettres et procédures administratives',
}