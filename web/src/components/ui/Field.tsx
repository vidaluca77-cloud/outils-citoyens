import React from 'react'
import { cn } from '../../lib/utils'

interface FieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
  className?: string
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean
  options: { value: string; label: string }[]
}

export function Field({ label, error, required, children, className }: FieldProps) {
  // Generate unique IDs for accessibility
  const fieldId = React.useMemo(() => `field-${Math.random().toString(36).substr(2, 9)}`, [])
  const errorId = React.useMemo(() => `error-${Math.random().toString(36).substr(2, 9)}`, [])
  
  return (
    <div className={cn('stack', className)}>
      <label 
        htmlFor={fieldId}
        className="block text-sm font-medium text-foreground"
      >
        {label}
        {required && (
          <span className="text-destructive ml-1" aria-label="obligatoire">
            *
          </span>
        )}
      </label>
      {React.cloneElement(children as React.ReactElement, {
        id: fieldId,
        'aria-describedby': error ? errorId : undefined,
        'aria-invalid': error ? 'true' : 'false',
        'aria-required': required ? 'true' : 'false'
      })}
      {error && (
        <p 
          id={errorId}
          className="text-sm text-destructive flex items-center"
          role="alert"
          aria-live="polite"
        >
          <span className="mr-1" aria-hidden="true">⚠️</span>
          {error}
        </p>
      )}
    </div>
  )
}

export function Input({ className, error, onChange, ...props }: InputProps & { onChange?: (value: string) => void }) {
  return (
    <input
      className={cn(
        'w-full px-3 py-2 bg-background border border-input rounded-md text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        'focus:border-ring transition-colors duration-200',
        error && 'border-destructive focus:border-destructive',
        className
      )}
      onChange={(e) => onChange?.(e.target.value)}
      {...props}
    />
  )
}

export function Textarea({ className, error, onChange, ...props }: TextareaProps & { onChange?: (value: string) => void }) {
  return (
    <textarea
      className={cn(
        'w-full px-3 py-2 bg-background border border-input rounded-md text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none',
        error && 'border-destructive',
        className
      )}
      rows={4}
      onChange={(e) => onChange?.(e.target.value)}
      {...props}
    />
  )
}

export function Select({ className, error, options, children, onChange, ...props }: SelectProps & { onChange?: (value: string) => void }) {
  return (
    <select
      className={cn(
        'w-full px-3 py-2 bg-background border border-input rounded-md text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        error && 'border-destructive',
        className
      )}
      onChange={(e) => onChange?.(e.target.value)}
      {...props}
    >
      {children}
      {options?.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}