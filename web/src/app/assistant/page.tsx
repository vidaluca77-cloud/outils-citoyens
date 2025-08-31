'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Toast } from '@/components/ui/Toast'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatResponse {
  answer: string
  suggested_fields?: Record<string, any>
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Bonjour ! Je suis votre assistant juridique. Comment puis-je vous aider avec vos démarches administratives aujourd&apos;hui ?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastSuggestedFields, setLastSuggestedFields] = useState<{
    tool_id: string
    fields: Record<string, any>
  } | null>(null)
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-clear toast after 3 seconds
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [toastMessage])

  const identifyToolFromMessage = (messageContent: string): string | null => {
    const content = messageContent.toLowerCase()
    
    if (content.includes('amende') || content.includes('contravention') || content.includes('pv')) {
      return 'amendes'
    }
    if (content.includes('loyer') || content.includes('logement') || content.includes('propriétaire')) {
      return 'loyers'
    }
    if (content.includes('travail') || content.includes('licenciement') || content.includes('employeur')) {
      return 'travail'
    }
    if (content.includes('caf') || content.includes('allocat')) {
      return 'caf'
    }
    if (content.includes('aide') || content.includes('social')) {
      return 'aides'
    }
    if (content.includes('santé') || content.includes('médical') || content.includes('sécurité sociale')) {
      return 'sante'
    }
    if (content.includes('énergie') || content.includes('électricité') || content.includes('gaz')) {
      return 'energie'
    }
    if (content.includes('expulsion') || content.includes('expulser')) {
      return 'expulsions'
    }
    if (content.includes('css') || content.includes('complémentaire santé')) {
      return 'css'
    }
    if (content.includes('école') || content.includes('scolaire') || content.includes('éducation')) {
      return 'ecole'
    }
    if (content.includes('surendettement') || content.includes('dette') || content.includes('usure')) {
      return 'usure'
    }
    if (content.includes('décodeur') || content.includes('courrier administratif') || content.includes('décrypter')) {
      return 'decodeur'
    }
    
    return null
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMessage]
    
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      // Try to identify which tool might be relevant
      const tool_id = identifyToolFromMessage(input)
      
      const response = await axios.post<ChatResponse>(`${API}/chat`, {
        tool_id,
        messages: newMessages
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.answer
      }

      setMessages([...newMessages, assistantMessage])

      // If we have suggested fields, store them for the "Fill Form" button
      if (response.data.suggested_fields && tool_id) {
        setLastSuggestedFields({
          tool_id,
          fields: response.data.suggested_fields
        })
      } else {
        setLastSuggestedFields(null)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      setToastMessage('Erreur lors de l\'envoi du message')
      setToastType('error')
      
      // Add error message from assistant
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Désolé, j\'ai rencontré un problème technique. Pouvez-vous reformuler votre question ?'
      }
      setMessages([...newMessages, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const fillForm = () => {
    if (!lastSuggestedFields) return
    
    const prefillData = encodeURIComponent(JSON.stringify(lastSuggestedFields.fields))
    router.push(`/outil/${lastSuggestedFields.tool_id}?prefill=${prefillData}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            Assistant Juridique
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Discutez avec votre assistant pour identifier l&apos;outil adapté à votre situation
          </p>
        </div>

        <Card className="h-[600px] flex flex-col">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] p-4 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white ml-4'
                      : 'bg-gray-100 text-gray-800 mr-4'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 p-4 rounded-2xl mr-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested action */}
          {lastSuggestedFields && (
            <div className="px-6 py-4 border-t border-gray-200 bg-blue-50">
              <div className="flex items-center justify-between">
                <div className="text-sm text-blue-700">
                  💡 Je peux préremplir le formulaire avec les informations que vous avez partagées
                </div>
                <Button
                  onClick={fillForm}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm"
                >
                  Remplir le formulaire
                </Button>
              </div>
            </div>
          )}

          {/* Input area */}
          <div className="p-6 border-t border-gray-200">
            <div className="flex space-x-4">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Tapez votre message..."
                className="flex-1 p-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
                disabled={loading}
              />
              <Button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-xl"
              >
                Envoyer
              </Button>
            </div>
          </div>
        </Card>
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