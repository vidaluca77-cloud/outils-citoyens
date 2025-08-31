'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import axios from 'axios'
import Ajv from 'ajv'
import Link from 'next/link'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Field, Input, Textarea, Select } from '../../../components/ui/Field'
import { Toast as ToastComponent } from '../../../components/ui/Toast'
import { Copy, Download, ArrowLeft, FileText } from 'lucide-react'
import { ToolFAQ, generateFAQJsonLD } from '../../../components/ToolFAQ'
import { FormAssistant } from '../../../components/FormAssistant'

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
    'modele_id': 'Modèle de lettre',
    'destinataire_id': 'Destinataire',
    'type_amende': 'Type d\'amende',
    'date_infraction': 'Date de l\'infraction',
    'numero_process_verbal': 'Numéro du procès-verbal',
    'motif_contestation': 'Motif de contestation',
    'elements_preuve': 'Éléments de preuve',
    'pieces_suggerees': 'Pièces jointes suggérées',
    'identite': 'Identité',
    'nom': 'Nom',
    'prenom': 'Prénom',
    'adresse': 'Adresse',
    'lieu': 'Lieu',
    'plaque': 'Plaque d\'immatriculation',
    // Dynamic placeholder labels
    'heure_debut_stationnement': 'Heure de début de stationnement',
    'heure_fin_stationnement': 'Heure de fin de stationnement',
    'numero_ticket': 'Numéro du ticket de stationnement',
    'vitesse_retenue': 'Vitesse retenue (km/h)',
    'vitesse_reelle': 'Vitesse réelle (km/h)', 
    'conditions_circulation': 'Conditions de circulation',
    'vice_constate': 'Vice de forme constaté',
    'article_legal': 'Article de loi concerné'
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
  const fullKey = parentKey ? `${parentKey}.${fieldKey}` : fieldKey
  const label = humanizeLabel(fieldKey)
  const error = errors[fullKey]
  
  // Handle nested objects
  if (fieldDef.type === 'object' && fieldDef.properties) {
    return (
      <Card title={label}>
        <div className="space-y-4">
          {Object.entries(fieldDef.properties).map(([subKey, subDef]: any) => (
            <FormField
              key={subKey}
              fieldKey={subKey}
              fieldDef={subDef}
              value={value?.[subKey] || ''}
              onChange={(subValue) => onChange({ ...(value || {}), [subKey]: subValue })}
              errors={errors}
              parentKey={fullKey}
            />
          ))}
        </div>
      </Card>
    )
  }
  
  // Handle enums (select dropdowns) 
  if (fieldDef.enum) {
    // Special handling for modele_id
    if (fieldKey === 'modele_id') {
      return (
        <Field label={label} error={error} required={fieldDef.required}>
          <Select 
            value={value || ''} 
            onChange={onChange}
            options={[
              { value: '', label: 'Saisie libre (sans modèle)' },
              ...fieldDef.enum.filter(option => option !== '').map((option: string) => {
                // Find model details from schema
                const modeles = (window as any).currentSchema?.['x-modeles'] || []
                const modele = modeles.find((m: any) => m.id === option)
                return {
                  value: option,
                  label: modele ? modele.label : option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                }
              })
            ]}
          />
        </Field>
      )
    }
    
    // Special handling for destinataire_id
    if (fieldKey === 'destinataire_id') {
      const options = (window as any).currentSchema?.['x-options']?.destinataire_options || []
      return (
        <Field label={label} error={error} required={fieldDef.required}>
          <Select 
            value={value || ''} 
            onChange={onChange}
            options={[
              { value: '', label: 'Sélectionner...' },
              ...options.map((option: any) => ({
                value: option.id,
                label: option.label
              }))
            ]}
          />
        </Field>
      )
    }
    
    // Default enum handling
    return (
      <Field label={label} error={error} required={fieldDef.required}>
        <Select 
          value={value || ''} 
          onChange={onChange}
          options={[
            { value: '', label: 'Sélectionner...' },
            ...fieldDef.enum.map((option: string) => ({
              value: option,
              label: option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
            }))
          ]}
        />
      </Field>
    )
  }
  
  // Handle arrays (checkboxes for pieces_suggerees)
  if (fieldDef.type === 'array' && fieldKey === 'pieces_suggerees') {
    const options = (window as any).currentSchema?.['x-options']?.pieces_suggerees || []
    const selectedValues = Array.isArray(value) ? value : []
    
    return (
      <Field label={label} error={error} required={fieldDef.required}>
        <div className="space-y-2">
          {options.map((option: string) => (
            <label key={option} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedValues.includes(option)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onChange([...selectedValues, option])
                  } else {
                    onChange(selectedValues.filter(v => v !== option))
                  }
                }}
                className="form-checkbox"
              />
              <span className="text-sm text-gray-700">{option}</span>
            </label>
          ))}
        </div>
      </Field>
    )
  }
  
  // Handle long text fields
  if (isLongStringField(fieldDef)) {
    return (
      <Field label={label} error={error} required={fieldDef.required}>
        <Textarea 
          value={value || ''} 
          onChange={onChange}
          placeholder={fieldDef.description || `Entrer ${label.toLowerCase()}`}
          rows={4}
        />
      </Field>
    )
  }
  
  // Handle regular input fields
  return (
    <Field label={label} error={error} required={fieldDef.required}>
      <Input 
        type={isDateField(fieldKey) ? 'date' : 'text'}
        value={value || ''} 
        onChange={onChange}
        placeholder={fieldDef.description || `Entrer ${label.toLowerCase()}`}
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
export function ToolPageClient({ params }: { params: { id: string } }) {
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

  // Handle form suggestions from AI assistant
  const handleFieldSuggestion = (suggestedFields: Record<string, any>) => {
    setValues(prevValues => ({ ...prevValues, ...suggestedFields }))
    setToastMessage('💡 L\'assistant a prérempli certains champs pour vous')
    setToastType('success')
  }

  useEffect(() => {
    fetch(`/schemas/${id}.json`)
      .then(r => r.json())
      .then(loadedSchema => {
        setSchema(loadedSchema)
        // Make schema available globally for FormField components
        ;(window as any).currentSchema = loadedSchema
      })
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
  
  // Auto-set destinataire when model is selected
  useEffect(() => {
    if (values.modele_id && schema?.['x-modeles'] && !values.destinataire_id) {
      const selectedModele = schema['x-modeles']?.find((m: any) => m.id === values.modele_id)
      if (selectedModele?.destinataire_default) {
        setValues(prev => ({ ...prev, destinataire_id: selectedModele.destinataire_default }))
      }
    }
  }, [values.modele_id, schema, values.destinataire_id])

  const validateForm = () => {
    if (!schema) return false
    
    const ajv = new Ajv()
    const validate = ajv.compile(schema)
    const valid = validate(values)
    
    if (!valid) {
      const newErrors: { [key: string]: string } = {}
      
      validate.errors?.forEach(error => {
        const path = error.instancePath.substring(1)
        if (path) {
          newErrors[path] = error.message || 'Erreur de validation'
        }
      })
      
      setErrors(newErrors)
      return false
    }
    
    setErrors({})
    return true
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
      const response = await axios.post(`${API}/generate`, {
        tool_id: id,
        fields: values
      })
      
      setResp(response.data)
      setToastMessage('Document généré avec succès !')
      setToastType('success')
      
      // Scroll to results
      setTimeout(() => {
        const resultsElement = document.getElementById('results')
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' })
        }
      }, 100)
      
    } catch (error: any) {
      console.error('Generation error:', error)
      let errorMessage = 'Erreur lors de la génération'
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      setToastMessage(errorMessage)
      setToastType('error')
    } finally {
      setLoading(false)
    }
  }

  const downloadFile = (content: string, filename: string, type: string = 'text/plain') => {
    const blob = new Blob([content], { type })
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
    let fullText = '=== RÉSUMÉ DES ÉTAPES ===\\n\\n'
    resp.resume.forEach((item, i) => {
      fullText += `${i + 1}. ${item}\\n`
    })
    
    fullText += '\\n=== VOTRE LETTRE ===\\n\\n'
    fullText += generateLetterText(resp.lettre)
    
    fullText += '\\n\\n=== CHECKLIST À SUIVRE ===\\n\\n'
    resp.checklist.forEach((item, i) => {
      fullText += `☐ ${item}\\n`
    })
    
    fullText += '\\n\\n=== INFORMATIONS IMPORTANTES ===\\n\\n'
    fullText += resp.mentions
    
    return fullText
  }

  const generateLetterText = (lettre: any): string => {
    return `Destinataire:
${lettre.destinataire_bloc}

Objet: ${lettre.objet}

${lettre.corps}

Pièces jointes:
${lettre.pj.map((pj: string) => `- ${pj}`).join('\\n')}

${lettre.signature}`
  }

  if (!schema) {
    return (
      <div className="page-container">
        <div className="content-container">
          <div className="flex items-center justify-center min-h-64">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Chargement du formulaire...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* JSON-LD structured data for FAQ */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: generateFAQJsonLD(id)
        }}
      />
      
      <div className="page-container">
        <div className="content-container">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-xl font-medium transition-all duration-200 hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2" aria-label="Retour à la liste des outils">
            <span className="mr-2">←</span>
            Retour aux outils
          </Link>
          <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
            <span className="mr-2">📄</span>
            Générateur automatique
          </div>
        </div>

        {/* Tool Title */}
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 bg-clip-text text-transparent mb-4">
            {schema.title}
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Remplissez le formulaire ci-dessous pour générer automatiquement votre document personnalisé.
          </p>
        </div>

        {/* Form Section */}
        {!resp && (
          <Card title="Informations requises" icon="📝">
            <form onSubmit={handleSubmit}>
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
              
              {/* Dynamic placeholder fields based on selected model */}
              {values.modele_id && (() => {
                const modeles = schema['x-modeles'] || []
                const selectedModele = modeles.find((m: any) => m.id === values.modele_id)
                if (selectedModele && selectedModele.placeholders) {
                  return (
                    <Card title={`Informations spécifiques - ${selectedModele.label}`} icon="📋">
                      <div className="space-y-4">
                        <p className="text-sm text-gray-600 mb-4">{selectedModele.template_hint}</p>
                        {selectedModele.placeholders.map((placeholder: string) => (
                          <Field 
                            key={placeholder} 
                            label={humanizeLabel(placeholder)}
                            required
                          >
                            <Input 
                              value={values[placeholder] || ''} 
                              onChange={(value) => setValues((prev: any) => ({ ...prev, [placeholder]: value }))}
                              placeholder={`Entrer ${humanizeLabel(placeholder).toLowerCase()}`}
                            />
                          </Field>
                        ))}
                      </div>
                    </Card>
                  )
                }
                return null
              })()}
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
                    <span className="text-xl">⚡</span>
                    <span>Générer mon document</span>
                  </div>
                )}
              </Button>
            </div>
            </form>
          </Card>
        )}

        {/* Results Section */}
        {resp && (
          <div id="results">
            {/* Download Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <Button
                onClick={() => downloadFile(generateAllText(resp), `${schema.title.toLowerCase().replace(/\\s+/g, '_')}_complet.txt`)}
                className="flex-1"
                size="lg"
              >
                <span className="mr-2">📄</span>
                <span>Télécharger .txt</span>
              </Button>
              <Button
                onClick={() => downloadFile(generateLetterText(resp.lettre), `${schema.title.toLowerCase().replace(/\\s+/g, '_')}_lettre.txt`)}
                variant="secondary"
                className="flex-1"
                size="lg"
              >
                <span className="mr-2">✉️</span>
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
              <div className="bg-white border-2 border-gray-200 rounded-xl p-8 font-mono text-sm space-y-6">
                <div>
                  <div className="font-bold text-gray-700 mb-2">Destinataire :</div>
                  <div className="whitespace-pre-line text-gray-800">{resp.lettre.destinataire_bloc}</div>
                </div>
                
                <div>
                  <div className="font-bold text-gray-700 mb-2">Objet :</div>
                  <div className="text-gray-800 font-semibold">{resp.lettre.objet}</div>
                </div>
                
                <div>
                  <div className="font-bold text-gray-700 mb-2">Corps de la lettre :</div>
                  <div className="whitespace-pre-line text-gray-800 leading-relaxed">{resp.lettre.corps}</div>
                </div>
                
                <div>
                  <div className="font-bold text-gray-700 mb-2">Pièces jointes :</div>
                  <ul className="list-disc list-inside text-gray-800 space-y-1">
                    {resp.lettre.pj.map((pj, i) => (
                      <li key={i}>{pj}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <div className="font-bold text-gray-700 mb-2">Signature :</div>
                  <div className="whitespace-pre-line text-gray-800">{resp.lettre.signature}</div>
                </div>
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
          </div>
        )}

        {/* FAQ Section */}
        <ToolFAQ toolId={id} />

        {toastMessage && (
          <ToastComponent 
            message={toastMessage} 
            type={toastType}
            onClose={() => setToastMessage('')} 
          />
        )}

        {/* AI Assistant */}
        {schema && (
          <FormAssistant
            toolId={id}
            currentValues={values}
            onFieldSuggestion={handleFieldSuggestion}
            toolTitle={schema.title || id}
          />
        )}
      </div>
    </div>
    </>
  )
}