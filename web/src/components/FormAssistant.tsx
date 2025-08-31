'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { MessageCircle, X, Send } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatResponse {
  answer: string
  suggested_fields?: Record<string, any>
}

interface FormAssistantProps {
  toolId: string
  currentValues: Record<string, any>
  onFieldSuggestion: (fields: Record<string, any>) => void
  toolTitle: string
}

export function FormAssistant({ 
  toolId, 
  currentValues, 
  onFieldSuggestion, 
  toolTitle 
}: FormAssistantProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize conversation when opened
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        role: 'assistant',
        content: `Bonjour ! Je suis votre assistant pour le formulaire "${toolTitle}". Je peux vous aider à comprendre les champs, vous guider dans vos démarches, ou répondre à vos questions. Comment puis-je vous aider ?`
      }
      setMessages([welcomeMessage])
    }
  }, [isOpen, messages.length, toolTitle])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMessage]
    
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post<ChatResponse>(`${API}/chat`, {
        tool_id: toolId,
        messages: newMessages,
        current_form_values: currentValues
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.answer
      }

      setMessages([...newMessages, assistantMessage])

      // If the assistant suggests field values, pass them to the parent
      if (response.data.suggested_fields) {
        onFieldSuggestion(response.data.suggested_fields)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      
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

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-200 flex items-center space-x-2"
        >
          <MessageCircle className="w-6 h-6" />
          <span className="hidden sm:inline">Assistant IA</span>
        </Button>
      </div>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 max-w-[calc(100vw-2rem)]">
      <Card className="h-[500px] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <MessageCircle className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Assistant IA</h3>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 p-3 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Posez votre question..."
              className="flex-1 p-2 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={loading}
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}