'use client'
import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '../lib/utils'
import { Home, Wrench, MessageCircle } from 'lucide-react'

interface AppShellProps {
  children: React.ReactNode
  title?: string
}

export function AppShell({ children, title }: AppShellProps) {
  const pathname = usePathname()

  const isActive = (path: string) => {
    if (path === '/') return pathname === '/'
    return pathname.startsWith(path)
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border px-4 py-3 sticky top-0 z-40">
        <div className="container flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">OC</span>
            </div>
            <div>
              <h1 className="font-bold text-lg text-foreground">
                {title || 'Outils Citoyens'}
              </h1>
              <p className="text-xs text-muted-foreground hidden sm:block">Générateur de lettres administratives</p>
            </div>
          </Link>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">🇫🇷</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pb-20 lg:pb-6">
        <div className="container">
          {children}
        </div>
      </main>

      {/* Bottom Navigation - Mobile Only */}
      <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border px-4 py-2 z-30 mobile-nav">
        <div className="flex items-center justify-around">
          <Link 
            href="/"
            className={cn(
              'flex flex-col items-center space-y-1 px-3 py-2 rounded-xl transition-all duration-200',
              isActive('/') 
                ? 'bg-primary/10 text-primary' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            )}
          >
            <Home className="w-5 h-5" />
            <span className="text-xs font-medium">Accueil</span>
          </Link>

          <Link 
            href="/outil"
            className={cn(
              'flex flex-col items-center space-y-1 px-3 py-2 rounded-xl transition-all duration-200',
              isActive('/outil') && !pathname.includes('/outil/') 
                ? 'bg-primary/10 text-primary' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            )}
          >
            <Wrench className="w-5 h-5" />
            <span className="text-xs font-medium">Outils</span>
          </Link>

          <Link
            href="/assistant"
            className={cn(
              'flex flex-col items-center space-y-1 px-3 py-2 rounded-xl transition-all duration-200',
              isActive('/assistant')
                ? 'bg-primary/10 text-primary' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            )}
          >
            <MessageCircle className="w-5 h-5" />
            <span className="text-xs font-medium">Assistant</span>
          </Link>
        </div>
      </nav>
    </div>
  )
}