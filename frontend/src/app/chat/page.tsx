'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText, Clock, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import MessageBubble from '@/components/MessageBubble'
import SourceCitation from '@/components/SourceCitation'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  metrics?: QueryMetrics
}

interface Source {
  content: string
  metadata: Record<string, any>
  relevance_score: number
}

interface QueryMetrics {
  retrieval_ms: number
  generation_ms: number
  total_ms: number
  cache_hit: boolean
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Call streaming API
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/query/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: input, stream: true }),
        }
      )

      if (!response.ok) throw new Error('Query failed')

      // Process SSE stream
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ''
      let sources: Source[] = []
      let metrics: QueryMetrics | undefined

      const assistantMessageObj: Message = {
        role: 'assistant',
        content: '',
      }
      setMessages(prev => [...prev, assistantMessageObj])

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'retrieval') {
              sources = data.sources
            } else if (data.type === 'token') {
              assistantMessage += data.content
              setMessages(prev => {
                const newMessages = [...prev]
                newMessages[newMessages.length - 1].content = assistantMessage
                return newMessages
              })
            } else if (data.type === 'done') {
              metrics = {
                total_ms: data.latency_ms,
                retrieval_ms: 0,
                generation_ms: 0,
                cache_hit: false,
              }
              setMessages(prev => {
                const newMessages = [...prev]
                newMessages[newMessages.length - 1].sources = sources
                newMessages[newMessages.length - 1].metrics = metrics
                return newMessages
              })
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, there was an error processing your query.',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">EnterpriseRAG</h1>
              <p className="text-sm text-gray-400">
                Production Document Q&A with Hybrid Retrieval
              </p>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline" className="text-green-400 border-green-400">
                <Zap className="w-3 h-3 mr-1" />
                99.9% Uptime
              </Badge>
              <Badge variant="outline" className="text-blue-400 border-blue-400">
                <Clock className="w-3 h-3 mr-1" />
                &lt;2s Response
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 mt-20">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Ask a question about your documents</p>
              <p className="text-sm mt-2">
                Powered by Claude Sonnet 4 • Hybrid Retrieval • Semantic Caching
              </p>
            </div>
          ) : (
            messages.map((message, i) => (
              <div key={i}>
                <MessageBubble message={message} />
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-4 ml-12">
                    <SourceCitation sources={message.sources} />
                  </div>
                )}
                {message.metrics && (
                  <div className="mt-2 ml-12 flex gap-4 text-xs text-gray-500">
                    <span>Total: {message.metrics.total_ms.toFixed(0)}ms</span>
                    {message.metrics.cache_hit && (
                      <Badge variant="secondary" className="text-xs">
                        ⚡ Cache Hit
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex items-center gap-2 text-gray-400 ml-12">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Searching documents...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={isLoading}
              className="flex-1 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
            />
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
