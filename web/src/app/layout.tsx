import './globals.css'

export default function RootLayout({children}:{children:React.ReactNode}) {
  return (
    <html lang='fr'>
      <head>
        <title>Outils Citoyens - Générateur de lettres administratives</title>
        <meta name="description" content="12 outils gratuits pour générer des lettres et procédures administratives" />
      </head>
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  )
}