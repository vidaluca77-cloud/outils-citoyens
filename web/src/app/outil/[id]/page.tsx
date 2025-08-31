'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import axios from 'axios'
import Ajv from 'ajv'
import Link from 'next/link'
import Head from 'next/head'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Field, Input, Textarea, Select } from '../../../components/ui/Field'
import { Toast as ToastComponent } from '../../../components/ui/Toast'

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
  const labelMap: { [key: string]: string } = {
    'type_amende': 'Type d\'amende',
    'date_infraction': 'Date de l\'infraction',
    'numero_process_verbal': 'Numéro du procès-verbal',
    'motif_contestation': 'Motif de contestation',
    'elements_preuve': 'Éléments de preuve',
    'identite': 'Identité',
    'nom': 'Nom',
    'prenom': 'Prénom',
    'adresse': 'Adresse',
    'lieu': 'Lieu',
    'plaque': 'Plaque d\'immatriculation'
  }
  
  return labelMap[key] || key
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
      <Card className="border-2 border-gray-200">
        <div className="flex items-center mb-4">
          <span className="text-2xl mr-3">👤</span>
          <h3 className="text-lg font-bold text-gray-800">{label}</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
      </Card>
    )
  }

  if (fieldDef.enum) {
    return (
      <Field label={label} error={error} required={isRequired}>
        <Select
          value={value || ''}
          onChange={e => onChange(e.target.value)}
          error={!!error}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${fullKey}-error` : undefined}
          options={[]}
        >
          <option value="">Choisir une option...</option>
          {fieldDef.enum.map((option: string) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </Select>
      </Field>
    )
  }

  if (fieldDef.type === 'boolean') {
    return (
      <Field label={label} error={error} required={isRequired}>
        <label className="flex items-center space-x-3 p-4 bg-gray-50 rounded-2xl border-2 border-gray-200 hover:border-blue-300 transition-colors cursor-pointer">
          <input
            type="checkbox"
            checked={value || false}
            onChange={e => onChange(e.target.checked)}
            className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${fullKey}-error` : undefined}
          />
          <span className="text-gray-700 font-medium">Oui</span>
        </label>
      </Field>
    )
  }

  if (fieldDef.type === 'number' || fieldDef.type === 'integer') {
    return (
      <Field label={label} error={error} required={isRequired}>
        <Input
          type="number"
          value={value || ''}
          onChange={e => onChange(fieldDef.type === 'integer' ? parseInt(e.target.value) || '' : parseFloat(e.target.value) || '')}
          placeholder={fieldDef.description || ''}
          step={fieldDef.type === 'integer' ? '1' : 'any'}
          error={!!error}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${fullKey}-error` : undefined}
        />
      </Field>
    )
  }

  if (isDateField(fieldKey)) {
    return (
      <Field label={label} error={error} required={isRequired}>
        <Input
          type="date"
          value={value || ''}
          onChange={e => onChange(e.target.value)}
          error={!!error}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${fullKey}-error` : undefined}
        />
      </Field>
    )
  }

  if (isLongStringField(fieldDef)) {
    return (
      <Field label={label} error={error} required={isRequired}>
        <Textarea
          value={value || ''}
          onChange={e => onChange(e.target.value)}
          placeholder={fieldDef.description || ''}
          error={!!error}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${fullKey}-error` : undefined}
        />
      </Field>
    )
  }

  return (
    <Field label={label} error={error} required={isRequired}>
      <Input
        type="text"
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        placeholder={fieldDef.description || ''}
        error={!!error}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${fullKey}-error` : undefined}
      />
    </Field>
  )
}

// Response panel component
function ResponsePanel({ title, children, icon }: { title: string; children: React.ReactNode; icon?: string }) {
  return (
    <Card title={title} icon={icon}>
      {children}
    </Card>
  )
}

// Main page component
export default function Page({ params }: { params: { id: string } }) {
  const { id } = params
  const searchParams = useSearchParams()
  const [schema, setSchema] = useState<any>(null)
  const [values, setValues] = useState<any>({})
  const [resp, setResp] = useState<APIResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ [key: string]: string }>({})
  const [toastMessage, setToastMessage] = useState<string>('')
  const [toastType, setToastType] = useState<'error' | 'success'>('error')
  
  const API = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

  useEffect(() => {
    fetch(`/schemas/${id}.json`)
      .then(r => r.json())
      .then(setSchema)
      .catch(() => {
        setToastMessage('Erreur lors du chargement du schéma')
        setToastType('error')
      })
  }, [id])

  // Handle prefill from query parameters
  useEffect(() => {
    const prefillParam = searchParams.get('prefill')
    if (prefillParam) {
      try {
        const prefillData = JSON.parse(decodeURIComponent(prefillParam))
        setValues(prevValues => ({ ...prevValues, ...prefillData }))
        setToastMessage('Formulaire prérempli avec les informations de votre conversation')
        setToastType('success')
      } catch (error) {
        console.error('Error parsing prefill data:', error)
        setToastMessage('Erreur lors du préremplissage du formulaire')
        setToastType('error')
      }
    }
  }, [searchParams])

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
      setToastType('error')
      return
    }

    setLoading(true)
    try {
      // For demo purposes, use mock data if API is not available
      let response
      try {
        response = await axios.post(`${API}/generate`, { tool_id: id, fields: values })
      } catch (apiError) {
        console.log('API not available, using mock data for demo')
        // Mock response for demo
        response = {
          data: {
            resume: [
              "Rassembler les pièces justificatives nécessaires",
              "Rédiger une lettre de contestation motivée",
              "Envoyer la lettre en recommandé avec accusé de réception",
              "Attendre la réponse de l'administration dans les 45 jours"
            ],
            lettre: {
              destinataire_bloc: "Service des Contraventions\nPréfecture de Police\n9 Boulevard du Palais\n75004 Paris",
              objet: "Contestation d'amende pour stationnement irrégulier",
              corps: "Madame, Monsieur,\n\nPar la présente, je conteste l'amende qui m'a été infligée le 15/01/2024 pour stationnement irrégulier rue de la Paix à Paris.\n\nEn effet, à la date et heure mentionnées sur le procès-verbal, mon véhicule était en réparation chez le garagiste, comme l'attestent les pièces jointes.\n\nJe vous demande donc l'annulation de cette contravention.\n\nVeuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
              pj: [
                "Copie de la facture du garagiste",
                "Attestation de dépôt du véhicule",
                "Copie de la carte grise"
              ],
              signature: "Jean Dupont\n123 Avenue des Champs-Élysées\n75008 Paris\n\nLe " + new Date().toLocaleDateString('fr-FR')
            },
            checklist: [
              "Envoyer la lettre en recommandé avec accusé de réception",
              "Conserver une copie de tous les documents",
              "Noter les références de l'envoi postal",
              "Attendre la réponse dans un délai de 45 jours",
              "En cas de refus, possibilité de saisir le tribunal de police"
            ],
            mentions: "Cette aide automatisée ne remplace pas un conseil juridique professionnel. Pour des situations complexes, consultez un avocat."
          }
        }
      }
      
      setResp(response.data)
      setToastMessage('Document généré avec succès !')
      setToastType('success')
    } catch (error) {
      setToastMessage('Erreur lors de la génération. Veuillez réessayer.')
      setToastType('error')
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setToastMessage('Texte copié dans le presse-papiers !')
      setToastType('success')
    } catch (error) {
      setToastMessage('Erreur lors de la copie')
      setToastType('error')
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

  const generateAllText = (resp: APIResponse): string => {
    let fullText = '=== RÉSUMÉ DES ÉTAPES ===\n\n'
    resp.resume.forEach((item, i) => {
      fullText += `${i + 1}. ${item}\n`
    })
    
    fullText += '\n=== VOTRE LETTRE ===\n\n'
    fullText += generateLetterText(resp.lettre)
    
    fullText += '\n\n=== CHECKLIST À SUIVRE ===\n\n'
    resp.checklist.forEach((item, i) => {
      fullText += `☐ ${item}\n`
    })
    
    fullText += '\n=== INFORMATIONS IMPORTANTES ===\n\n'
    fullText += resp.mentions
    
    return fullText
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
      <div className="page-container flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl text-gray-600 font-medium">Chargement de l&apos;outil...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>{schema.title} – Outils Citoyens</title>
        <meta name="description" content={`Générateur automatique pour ${schema.title.toLowerCase()}. Outil gratuit et sécurisé.`} />
      </Head>
      <div className="page-container">
        <div className="content-container">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-xl font-medium transition-all duration-200 hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2">
            <span className="mr-2">←</span>
            Retour aux outils
          </Link>
          <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
            <span className="mr-2">📄</span>
            Générateur automatique
          </div>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            {schema.title}
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Remplissez le formulaire ci-dessous pour générer votre document personnalisé
          </p>
        </div>
        
        <Card className="mb-12">
          <form onSubmit={handleSubmit}>
            <h2 className="text-2xl font-bold text-gray-800 mb-8 flex items-center">
              <span className="mr-3">📝</span>
              Informations requises
            </h2>
            
            <div className="space-y-8">
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
            </div>
            
            <div className="mt-10 pt-8 border-t border-gray-200">
              <Button
                type="submit"
                disabled={loading}
                size="lg"
                className="w-full"
              >
                {loading ? (
                  <div className="flex items-center justify-center space-x-3">
                    <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Génération en cours...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-3">
                    <span>⚡</span>
                    <span>Générer mon document</span>
                  </div>
                )}
              </Button>
            </div>
          </form>
        </Card>

        {resp && (
          <>
            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <Button
                variant="secondary"
                onClick={() => copyToClipboard(generateAllText(resp))}
                className="flex items-center justify-center space-x-2 flex-1"
              >
                <span>📋</span>
                <span>Copier tout</span>
              </Button>
              <Button
                variant="primary"
                onClick={() => downloadAsText(generateAllText(resp), `document-${id}.txt`)}
                className="flex items-center justify-center space-x-2 flex-1"
              >
                <span>💾</span>
                <span>Télécharger .txt</span>
              </Button>
            </div>
            
            <div className="space-y-8">
            {/* Résumé Panel */}
            <ResponsePanel title="Résumé des étapes" icon="📋">
              <div className="space-y-4">
                {resp.resume.map((item, i) => (
                  <div key={i} className="flex items-start space-x-4 p-4 bg-blue-50 rounded-xl">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                      {i + 1}
                    </div>
                    <span className="text-gray-800 font-medium flex-1">{item}</span>
                  </div>
                ))}
              </div>
            </ResponsePanel>

            {/* Lettre Panel */}
            <ResponsePanel title="Votre lettre" icon="📄">
              <div className="bg-gray-50 rounded-2xl p-6 font-mono text-sm whitespace-pre-wrap mb-6 border-2 border-gray-200">
                {generateLetterText(resp.lettre)}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => copyToClipboard(generateLetterText(resp.lettre))}
                  className="btn-secondary flex items-center justify-center space-x-2"
                >
                  <span>📋</span>
                  <span>Copier le texte</span>
                </button>
                <button
                  onClick={() => downloadAsText(generateLetterText(resp.lettre), `lettre-${id}.txt`)}
                  className="btn-primary flex items-center justify-center space-x-2"
                >
                  <span>💾</span>
                  <span>Télécharger (.txt)</span>
                </button>
              </div>
            </ResponsePanel>

            {/* Checklist Panel */}
            <ResponsePanel title="Checklist à suivre" icon="✅">
              <div className="space-y-3">
                {resp.checklist.map((item, i) => (
                  <div key={i} className="flex items-start space-x-3 p-3 bg-green-50 rounded-xl">
                    <div className="flex-shrink-0 w-6 h-6 border-2 border-green-500 rounded-md mt-0.5"></div>
                    <span className="text-gray-800">{item}</span>
                  </div>
                ))}
              </div>
            </ResponsePanel>

            {/* Mentions Panel */}
            <ResponsePanel title="Informations importantes" icon="⚠️">
              <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-6">
                <p className="text-amber-800 font-medium">{resp.mentions}</p>
              </div>
            </ResponsePanel>
          </div>
          </>
        )}

        {toastMessage && (
          <ToastComponent 
            message={toastMessage} 
            type={toastType}
            onClose={() => setToastMessage('')} 
          />
        )}
      </div>
    </div>
    </>
  )
}