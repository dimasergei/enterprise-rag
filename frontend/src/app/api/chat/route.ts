import { NextRequest, NextResponse } from 'next/server'

// Mock enterprise documents
const mockDocuments = [
  {
    title: "Q3 2024 Financial Report",
    content: "EnterpriseRAG achieved $2.4M in Q3 revenue, representing 45% YoY growth. The company's hybrid retrieval system reduced operational costs by 32% while improving query accuracy to 94%. Major enterprise clients include Fortune 500 companies in finance, healthcare, and technology sectors.",
    metadata: { type: "financial", quarter: "Q3 2024", classification: "public" }
  },
  {
    title: "Security Protocol Documentation",
    content: "All EnterpriseRAG deployments implement end-to-end encryption using AES-256. Data is encrypted at rest and in transit. Access control follows RBAC principles with multi-factor authentication required for administrative access. Regular security audits are conducted quarterly by third-party firms.",
    metadata: { type: "security", last_updated: "2024-10-15", classification: "internal" }
  },
  {
    title: "Product Update v2.5",
    content: "Version 2.5 introduces enhanced semantic caching with 85% hit rate on similar queries. New hybrid retrieval algorithm combines BM25 and vector search using Reciprocal Rank Fusion. Performance improvements include 40% faster indexing and 60% reduction in memory usage.",
    metadata: { type: "product", version: "2.5", release_date: "2024-11-01" }
  },
  {
    title: "Enterprise Privacy Policy",
    content: "EnterpriseRAG complies with GDPR, CCPA, and SOC 2 Type II standards. Customer data is never used for model training. All processing occurs in isolated tenant environments. Data retention policies allow customers to specify retention periods from 30 days to 7 years.",
    metadata: { type: "policy", compliance: ["GDPR", "CCPA", "SOC2"], last_reviewed: "2024-09-30" }
  },
  {
    title: "Technical Architecture Overview",
    content: "The system uses a microservices architecture with Kubernetes orchestration. Vector embeddings are generated using OpenAI's text-embedding-ada-002 model. Retrieval combines Elasticsearch for BM25 scoring and Pinecone for vector similarity. Results are cached in Redis with intelligent invalidation.",
    metadata: { type: "technical", infrastructure: "kubernetes", embedding_model: "ada-002" }
  }
]

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json()
    
    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 })
    }

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1200))

    // Find relevant documents based on query keywords
    const relevantDocs = mockDocuments.filter(doc => {
      const queryLower = query.toLowerCase()
      const contentLower = doc.content.toLowerCase()
      const titleLower = doc.title.toLowerCase()
      
      // Simple keyword matching for demo
      return queryLower.split(' ').some(keyword => 
        keyword.length > 2 && (contentLower.includes(keyword) || titleLower.includes(keyword))
      )
    }).slice(0, 3) // Limit to top 3 most relevant

    // Generate contextual response based on query and relevant documents
    let answer = ""
    
    if (query.toLowerCase().includes('security') || query.toLowerCase().includes('protocol')) {
      answer = "EnterpriseRAG implements comprehensive security measures including AES-256 encryption for data at rest and in transit. The system follows Role-Based Access Control (RBAC) principles with mandatory multi-factor authentication for administrative access. Regular security audits are conducted quarterly by third-party firms, and the platform complies with GDPR, CCPA, and SOC 2 Type II standards."
    } else if (query.toLowerCase().includes('revenue') || query.toLowerCase().includes('financial')) {
      answer = "EnterpriseRAG achieved $2.4M in Q3 2024 revenue, representing 45% year-over-year growth. The company's hybrid retrieval technology has significantly reduced operational costs by 32% while improving query accuracy to 94%. Major enterprise clients include Fortune 500 companies across finance, healthcare, and technology sectors."
    } else if (query.toLowerCase().includes('performance') || query.toLowerCase().includes('latency')) {
      answer = "EnterpriseRAG delivers sub-2-second response times with P95 latency of 184ms. The latest version 2.5 features enhanced semantic caching achieving 85% hit rates on similar queries. Performance improvements include 40% faster indexing and 60% reduction in memory usage through optimized hybrid retrieval algorithms combining BM25 and vector search."
    } else if (query.toLowerCase().includes('architecture') || query.toLowerCase().includes('technical')) {
      answer = "EnterpriseRAG uses a microservices architecture orchestrated with Kubernetes. The system generates vector embeddings using OpenAI's text-embedding-ada-002 model and combines Elasticsearch for BM25 scoring with Pinecone for vector similarity search. Results are intelligently cached in Redis with automatic invalidation. The hybrid retrieval approach achieves 7-9% better recall than vector-only methods."
    } else {
      answer = "EnterpriseRAG is a production-grade document Q&A system that combines vector search and BM25 retrieval with semantic caching. The platform processes over 50K documents while maintaining sub-2-second response times and 94% query accuracy. Key features include hybrid retrieval for better recall, semantic caching for cost reduction, and enterprise-grade security with full compliance to major privacy regulations."
    }

    const sources = relevantDocs.map(doc => ({
      content: doc.content.substring(0, 200) + "...",
      metadata: doc.metadata,
      relevance_score: 0.8 + Math.random() * 0.2
    }))

    return NextResponse.json({
      answer,
      sources,
      latencyMs: 800 + Math.random() * 1200
    })

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
