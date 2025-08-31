'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import axios from 'axios'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Field } from '@/components/ui/Field'
import { Toast } from '@/components/ui/Toast'
import { useRouter, useSearchParams } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'

interface LegalCitation {
  title: string
  source: string
  date: string
  url: string
  type: string
}

interface LegalAnswer {
  answer: string
  citations: LegalCitation[]
  disclaimer: string
}

interface LegalSearchRequest {
  question: string
  limit: number
  since_months: number
}

function LegalSearchContent() {
  const [question, setQuestion] = useState('')
  const [limitTo24Months, setLimitTo24Months] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<LegalAnswer | null>(null)
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // Auto-clear toast after 3 seconds
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [toastMessage])

  // Pre-fill question from URL params (from assistant)
  useEffect(() => {
    const questionParam = searchParams?.get('q')
    if (questionParam) {
      setQuestion(decodeURIComponent(questionParam))
    }
  }, [searchParams])

  const handleSearch = async () => {
    if (!question.trim()) {
      setToastMessage('Veuillez saisir votre question juridique')
      setToastType('error')
      return
    }

    if (question.length > 500) {
      setToastMessage('Question trop longue (500 caractères maximum)')
      setToastType('error')
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const searchRequest: LegalSearchRequest = {
        question: question.trim(),
        limit: 6,
        since_months: limitTo24Months ? 24 : 36
      }

      const response = await axios.post<LegalAnswer>(`${API}/legal/search`, searchRequest)
      setResult(response.data)
      
      if (response.data.citations.length === 0) {
        setToastMessage('Aucune source pertinente trouvée')
        setToastType('error')
      } else {
        setToastMessage(`${response.data.citations.length} sources trouvées`)
        setToastType('success')
      }

    } catch (error) {
      console.error('Error searching:', error)
      setToastMessage('Erreur lors de la recherche juridique')
      setToastType('error')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const copyToClipboard = () => {
    if (!result) return
    
    const textToCopy = `RECHERCHE JURIDIQUE
Question: ${question}

SYNTHÈSE:
${result.answer}

SOURCES CITÉES:
${result.citations.map((cite, i) => 
  `${i+1}. ${cite.title}
   Source: ${cite.source} (${cite.type})
   Date: ${cite.date}
   URL: ${cite.url}`
).join('\n\n')}

AVERTISSEMENT:
${result.disclaimer}

---
Généré par Outils Citoyens - ${new Date().toLocaleDateString('fr-FR')}`

    navigator.clipboard.writeText(textToCopy).then(() => {
      setToastMessage('Contenu copié dans le presse-papiers')
      setToastType('success')
    }).catch(() => {
      setToastMessage('Erreur lors de la copie')
      setToastType('error')
    })
  }

  const exportAsText = () => {
    if (!result) return

    const textContent = `RECHERCHE JURIDIQUE
Question: ${question}

SYNTHÈSE:
${result.answer}

SOURCES CITÉES:
${result.citations.map((cite, i) => 
  `${i+1}. ${cite.title}
   Source: ${cite.source} (${cite.type})
   Date: ${cite.date}
   URL: ${cite.url}`
).join('\n\n')}

AVERTISSEMENT:
${result.disclaimer}

---
Généré par Outils Citoyens - ${new Date().toLocaleDateString('fr-FR')}`

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `recherche-juridique-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            Recherche Juridique
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Recherche dans les sources juridiques françaises récentes avec synthèse automatisée
          </p>
        </div>

        {/* Search Form */}
        <Card className="mb-8">
          <div className="p-6 space-y-6">
            <Field label="Votre question juridique" required>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ex: Quels sont mes droits en cas de licenciement abusif ?"
                className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                maxLength={500}
                disabled={loading}
              />
              <div className="text-sm text-gray-500 mt-1">
                {question.length}/500 caractères
              </div>
            </Field>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="limitTo24Months"
                checked={limitTo24Months}
                onChange={(e) => setLimitTo24Months(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                disabled={loading}
              />
              <label htmlFor="limitTo24Months" className="text-sm text-gray-700">
                Limiter aux sources des 24 derniers mois (recommandé)
              </label>
            </div>

            <div className="flex justify-center">
              <Button
                onClick={handleSearch}
                disabled={!question.trim() || loading}
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Recherche en cours...</span>
                  </div>
                ) : (
                  'Rechercher'
                )}
              </Button>
            </div>
          </div>
        </Card>

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Answer */}
            <Card>
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">Synthèse juridique</h2>
                  <div className="flex space-x-2">
                    <Button
                      onClick={copyToClipboard}
                      className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
                    >
                      📋 Copier
                    </Button>
                    <Button
                      onClick={exportAsText}
                      className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
                    >
                      📄 Export .txt
                    </Button>
                  </div>
                </div>
                
                <div className="prose max-w-none">
                  <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                    {result.answer}
                  </div>
                </div>
              </div>
            </Card>

            {/* Citations */}
            {result.citations.length > 0 && (
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">
                    Sources citées ({result.citations.length})
                  </h3>
                  <div className="space-y-4">
                    {result.citations.map((citation, index) => (
                      <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900 mb-1">
                              <a 
                                href={citation.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800 hover:underline"
                              >
                                {citation.title}
                              </a>
                            </h4>
                            <div className="text-sm text-gray-600 space-x-4">
                              <span className="font-medium">{citation.source}</span>
                              <span>{citation.type}</span>
                              <span>{citation.date}</span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-sm"
                            >
                              🔗 Consulter
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            )}

            {/* Disclaimer */}
            <Card className="bg-amber-50 border-amber-200">
              <div className="p-6">
                <div className="flex items-start space-x-3">
                  <div className="text-amber-600 text-xl">⚠️</div>
                  <div>
                    <h3 className="font-semibold text-amber-800 mb-2">Avertissement important</h3>
                    <p className="text-amber-700 text-sm leading-relaxed">
                      {result.disclaimer}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Back to tools */}
        <div className="mt-8 text-center">
          <Button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg"
          >
            ← Retour aux outils
          </Button>
        </div>
      </div>

      {toastMessage && (
        <Toast 
          message={toastMessage} 
          type={toastType} 
          onClose={() => setToastMessage('')} 
        />
      )}
    </div>
  )
}

export default function LegalSearchClient() {
  return (
    <Suspense fallback={<div>Chargement...</div>}>
      <LegalSearchContent />
    </Suspense>
  )
}