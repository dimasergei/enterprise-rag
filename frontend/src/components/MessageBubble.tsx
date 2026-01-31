'use client'

import { User, Bot } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
  metrics?: any
}

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex items-start gap-3 max-w-3xl ${isUser ? 'flex-row-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-blue-600' : 'bg-gray-700'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Message content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <Card className={`p-4 ${
            isUser 
              ? 'bg-blue-600 text-white border-blue-600' 
              : 'bg-gray-800 text-white border-gray-700'
          }`}>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </Card>
          
          {/* Timestamp */}
          <div className="text-xs text-gray-500 mt-1">
            {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  )
}
