import React, { useEffect } from 'react'
import { cn } from '../../lib/utils'

interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'info'
  onClose: () => void
  duration?: number
}

export function Toast({ message, type = 'info', onClose, duration = 5000 }: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [onClose, duration])

  return (
    <div className={cn(
      'fixed top-4 right-4 max-w-md p-4 rounded-2xl shadow-lg z-50 transform transition-all duration-300',
      type === 'success' && 'bg-green-500 text-white',
      type === 'error' && 'bg-red-500 text-white',
      type === 'info' && 'bg-blue-500 text-white'
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-lg">
            {type === 'success' && '✅'}
            {type === 'error' && '❌'}
            {type === 'info' && 'ℹ️'}
          </span>
          <span className="font-medium">{message}</span>
        </div>
        <button 
          onClick={onClose}
          className="ml-4 text-white hover:text-gray-200 transition-colors"
        >
          ×
        </button>
      </div>
    </div>
  )
}