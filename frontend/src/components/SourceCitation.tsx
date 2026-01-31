'use client'

import { FileText, ExternalLink } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Source {
  content: string
  metadata: Record<string, any>
  relevance_score: number
}

interface SourceCitationProps {
  sources: Source[]
}

export default function SourceCitation({ sources }: SourceCitationProps) {
  if (!sources || sources.length === 0) return null

  return (
    <Card className="bg-gray-800/50 border-gray-700 p-4">
      <div className="flex items-center gap-2 mb-3">
        <FileText className="w-4 h-4 text-blue-400" />
        <h4 className="text-sm font-semibold text-white">Sources</h4>
        <Badge variant="secondary" className="text-xs">
          {sources.length} documents
        </Badge>
      </div>
      
      <div className="space-y-3">
        {sources.map((source, index) => (
          <div key={index} className="border-l-2 border-blue-500 pl-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <p className="text-sm text-gray-300 line-clamp-2">
                  {source.content}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {source.metadata?.source || 'Unknown source'}
                  </span>
                  {source.metadata?.page && (
                    <span className="text-xs text-gray-500">
                      Page {source.metadata.page}
                    </span>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {(source.relevance_score * 100).toFixed(1)}% match
                  </Badge>
                </div>
              </div>
              {source.metadata?.url && (
                <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0 mt-1" />
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
