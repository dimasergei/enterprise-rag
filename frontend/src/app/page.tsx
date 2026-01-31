import Link from 'next/link'
import { ArrowRight, Zap, FileText, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <nav className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileText className="w-8 h-8 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent" />
              <h1 className="text-2xl font-bold text-white">EnterpriseRAG</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/chat">
                <Button variant="outline" className="text-white border-gray-600 hover:bg-gray-800">
                  Try Demo
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700">
                  View Metrics
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-4 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-white mb-6">
            Production Document Q&A with
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">Hybrid Retrieval</span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Enterprise-grade RAG system that combines vector search and BM25 with semantic caching,
            delivering sub-2-second response times on 50K+ documents.
          </p>
          <div className="flex items-center justify-center space-x-4 mb-8">
            <Link href="/chat?query=What are our security protocols?">
              <Button variant="outline" size="sm" className="border-gray-600 text-white hover:bg-gray-800">
                What are our security protocols?
              </Button>
            </Link>
            <Link href="/chat?query=Q3 revenue performance analysis">
              <Button variant="outline" size="sm" className="border-gray-600 text-white hover:bg-gray-800">
                Q3 revenue performance analysis
              </Button>
            </Link>
          </div>
          <div className="flex items-center justify-center space-x-4">
            <Link href="/chat">
              <Button size="lg" className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-lg px-8 py-3">
                Try Live Demo
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="text-lg px-8 py-3 border-gray-600 text-white hover:bg-gray-800">
                View Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-20">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white flex items-center">
                <Zap className="w-5 h-5 mr-2 text-yellow-400" />
                184ms
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-400 text-sm">P95 Retrieval Latency</p>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-green-400" />
                92%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-400 text-sm">Faithfulness Score</p>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white flex items-center">
                <FileText className="w-5 h-5 mr-2 text-blue-400" />
                50K+
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-400 text-sm">Documents Indexed</p>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white flex items-center">
                <Zap className="w-5 h-5 mr-2 text-purple-400" />
                68%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-400 text-sm">Cost Reduction</p>
            </CardContent>
          </Card>
        </div>

        {/* Features */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Why This Beats Basic RAG
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Hybrid Retrieval</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-300">
                  Combines vector search (semantic) and BM25 (lexical) using Reciprocal Rank Fusion,
                  achieving 7-9% better recall than vector-only approaches.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Semantic Caching</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-300">
                  Caches query embeddings + results in Redis, returning cached results for similar queries
                  and reducing LLM costs by 68%.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Production Monitoring</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-300">
                  Real-time metrics tracked with Prometheus, including latency percentiles,
                  cache hit rates, and automated RAGAS evaluation scores.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
