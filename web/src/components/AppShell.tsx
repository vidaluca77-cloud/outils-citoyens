'use client'
import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '../lib/utils'

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
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900 truncate">
            {title || 'Outils Citoyens'}
          </h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">🇫🇷</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pb-20 lg:pb-6">
        <div className="max-w-7xl mx-auto lg:max-w-4xl lg:px-6">
          {children}
        </div>
      </main>

      {/* Bottom Navigation - Mobile Only */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2 z-30 lg:hidden">
        <div className="flex items-center justify-around">
          <Link 
            href="/"
            className={cn(
              'flex flex-col items-center space-y-1 px-3 py-2 rounded-xl transition-all duration-200',
              isActive('/') 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            )}
          >
            <span className="text-xl">🏠</span>
            <span className="text-xs font-medium">Accueil</span>
          </Link>

          <Link 
            href="/outil"
            className={cn(
              'flex flex-col items-center space-y-1 px-3 py-2 rounded-xl transition-all duration-200',
              isActive('/outil') 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            )}
          >
            <span className="text-xl">🛠️</span>
            <span className="text-xs font-medium">Outils</span>
          </Link>

          <button 
            className={cn(
              'flex flex-col items-center space-y-1 px-3 py-2 rounded-xl transition-all duration-200',
              pathname.includes('/outil/') && !pathname.endsWith('/outil')
                ? 'bg-green-50 text-green-600' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            )}
            disabled={!pathname.includes('/outil/') || pathname.endsWith('/outil')}
          >
            <span className="text-xl">⚡</span>
            <span className="text-xs font-medium">Générer</span>
          </button>
        </div>
      </nav>
    </div>
  )
}