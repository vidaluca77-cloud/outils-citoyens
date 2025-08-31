import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  icon?: string
}

export function Card({ children, className, title, icon }: CardProps) {
  return (
    <div className={cn(
      'bg-white border border-gray-200 shadow-md rounded-2xl p-6 transition-shadow hover:shadow-lg',
      className
    )}>
      {(title || icon) && (
        <div className="flex items-center mb-4">
          {icon && <span className="text-2xl mr-3">{icon}</span>}
          {title && <h3 className="text-xl font-bold text-gray-800">{title}</h3>}
        </div>
      )}
      {children}
    </div>
  )
}