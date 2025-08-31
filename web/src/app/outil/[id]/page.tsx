'use client'
import { useEffect, useState } from 'react'
import axios from 'axios'
import Ajv from 'ajv'

// Type definitions
interface APIResponse {
  resume: string[]
  lettre: {
    destinataire_bloc: string
    objet: string
    corps: string
    pj: string[]
    signature: string
  }
  checklist: string[]
  mentions: string
}

// Utility functions
function humanizeLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

function isDateField(key: string): boolean {
  return key.toLowerCase().includes('date')
}

function isLongStringField(def: any): boolean {
  return def.type === 'string' && !def.enum && def.description && def.description.length > 50
}

// Form field component
function FormField({ 
  fieldKey, 
  fieldDef, 
  value, 
  onChange, 
  errors = {},
  parentKey = ''
}: { 
  fieldKey: string
  fieldDef: any
  value: any
  onChange: (value: any) => void
  errors?: { [key: string]: string }
  parentKey?: string
}) {
  const label = humanizeLabel(fieldKey)
  const fullKey = parentKey ? `${parentKey}.${fieldKey}` : fieldKey
  const isRequired = fieldDef.required || false
  const error = errors[fullKey]

  if (fieldDef.type === 'object') {
    return (
      <fieldset className="border border-gray-300 rounded-lg p-4 mb-4">
        <legend className="text-sm font-medium text-gray-700 px-2">{label}</legend>
        <div className="space-y-3">
          {Object.entries(fieldDef.properties || {}).map(([subKey, subDef]: any) => (
            <FormField
              key={subKey}
              fieldKey={subKey}
              fieldDef={subDef}
              value={value?.[subKey] || ''}
              onChange={(val) => onChange({ ...value, [subKey]: val })}
              errors={errors}
              parentKey={fieldKey}
            />
          ))}
        </div>
      </fieldset>
    )
  }

  let inputElement
  const baseClasses = `w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
    error ? 'border-red-500' : 'border-gray-300'
  }`

  if (fieldDef.enum) {
    inputElement = (
      <select 
        value={value || ''} 
        onChange={e => onChange(e.target.value)}
        className={baseClasses}
      >
        <option value="">Choisir...</option>
        {fieldDef.enum.map((option: string) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    )
  } else if (fieldDef.type === 'boolean') {
    inputElement = (
      <label className="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={value || false}
          onChange={e => onChange(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-600">Oui</span>
      </label>
    )
  } else if (fieldDef.type === 'number' || fieldDef.type === 'integer') {
    inputElement = (
      <input
        type="number"
        value={value || ''}
        onChange={e => onChange(fieldDef.type === 'integer' ? parseInt(e.target.value) || '' : parseFloat(e.target.value) || '')}
        placeholder={fieldDef.description || ''}
        className={baseClasses}
        step={fieldDef.type === 'integer' ? '1' : 'any'}
      />
    )
  } else if (isDateField(fieldKey)) {
    inputElement = (
      <input
        type="date"
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        className={baseClasses}
      />
    )
  } else if (isLongStringField(fieldDef)) {
    inputElement = (
      <textarea
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        placeholder={fieldDef.description || ''}
        rows={4}
        className={baseClasses}
      />
    )
  } else {
    inputElement = (
      <input
        type="text"
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        placeholder={fieldDef.description || ''}
        className={baseClasses}
      />
    )
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {isRequired && <span className="text-red-500 ml-1">*</span>}
      </label>
      {inputElement}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}

// Toast component for error notifications
function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className="fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-md shadow-lg z-50">
      <div className="flex items-center space-x-2">
        <span>{message}</span>
        <button onClick={onClose} className="text-white hover:text-gray-200">
          ×
        </button>
      </div>
    </div>
  )
}

// Response panel component
function ResponsePanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">{title}</h2>
      {children}
    </div>
  )
}

// Main page component
export default function Page({ params }: { params: { id: string } }) {
  const { id } = params
  const [schema, setSchema] = useState<any>(null)
  const [values, setValues] = useState<any>({})
  const [resp, setResp] = useState<APIResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ [key: string]: string }>({})
  const [toastMessage, setToastMessage] = useState<string>('')
  
  const API = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

  useEffect(() => {
    fetch(`/schemas/${id}.json`)
      .then(r => r.json())
      .then(setSchema)
      .catch(() => setToastMessage('Erreur lors du chargement du schéma'))
  }, [id])

  const validateForm = (): boolean => {
    if (!schema) return false
    
    const newErrors: { [key: string]: string } = {}
    
    // Simple validation for required fields
    if (schema.required) {
      schema.required.forEach((fieldName: string) => {
        if (schema.properties[fieldName]?.type === 'object') {
          // For object fields, check if all required sub-fields are filled
          const objectDef = schema.properties[fieldName]
          if (objectDef.required) {
            objectDef.required.forEach((subField: string) => {
              if (!values[fieldName]?.[subField]) {
                newErrors[`${fieldName}.${subField}`] = 'Ce champ est requis'
              }
            })
          }
        } else {
          // For simple fields
          if (!values[fieldName] || values[fieldName] === '') {
            newErrors[fieldName] = 'Ce champ est requis'
          }
        }
      })
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      setToastMessage('Veuillez corriger les erreurs dans le formulaire')
      return
    }

    setLoading(true)
    try {
      const response = await axios.post(`${API}/generate`, { tool_id: id, fields: values })
      setResp(response.data)
    } catch (error) {
      setToastMessage('Erreur lors de la génération. Veuillez réessayer.')
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setToastMessage('Texte copié dans le presse-papiers !')
    } catch (error) {
      setToastMessage('Erreur lors de la copie')
    }
  }

  const downloadAsText = (text: string, filename: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const generateLetterText = (lettre: APIResponse['lettre']): string => {
    return `Destinataire:
${lettre.destinataire_bloc}

Objet: ${lettre.objet}

${lettre.corps}

Pièces jointes: ${lettre.pj.join(', ')}

Signature:
${lettre.signature}`
  }

  if (!schema) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Chargement…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto max-w-3xl px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">{schema.title}</h1>
        
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 mb-8">
          {Object.entries(schema.properties).map(([key, def]: any) => (
            <FormField
              key={key}
              fieldKey={key}
              fieldDef={def}
              value={values[key]}
              onChange={(value) => setValues((prev: any) => ({ ...prev, [key]: value }))}
              errors={errors}
            />
          ))}
          
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-4 rounded-md font-medium transition-colors ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            } text-white`}
          >
            {loading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Génération en cours...</span>
              </div>
            ) : (
              'Générer'
            )}
          </button>
        </form>

        {resp && (
          <div className="space-y-6">
            {/* Résumé Panel */}
            <ResponsePanel title="Résumé">
              <ul className="space-y-2">
                {resp.resume.map((item, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="flex-shrink-0 w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </ResponsePanel>

            {/* Lettre Panel */}
            <ResponsePanel title="Lettre">
              <div className="bg-gray-50 rounded-md p-4 font-mono text-sm whitespace-pre-wrap mb-4">
                {generateLetterText(resp.lettre)}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => copyToClipboard(generateLetterText(resp.lettre))}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md transition-colors"
                >
                  Copier le texte
                </button>
                <button
                  onClick={() => downloadAsText(generateLetterText(resp.lettre), `lettre-${id}.txt`)}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md transition-colors"
                >
                  Télécharger .txt
                </button>
              </div>
            </ResponsePanel>

            {/* Checklist Panel */}
            <ResponsePanel title="Checklist">
              <ul className="space-y-2">
                {resp.checklist.map((item, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="flex-shrink-0 w-4 h-4 border-2 border-green-500 rounded mt-1"></span>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </ResponsePanel>

            {/* Mentions Panel */}
            <ResponsePanel title="Mentions">
              <p className="text-sm text-gray-600 italic">{resp.mentions}</p>
            </ResponsePanel>
          </div>
        )}

        {toastMessage && (
          <Toast 
            message={toastMessage} 
            onClose={() => setToastMessage('')} 
          />
        )}
      </div>
    </div>
  )
}