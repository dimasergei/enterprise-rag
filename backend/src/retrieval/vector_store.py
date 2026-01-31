from typing import List, Dict, Any, Optional
import numpy as np
import asyncpg
import json
from sentence_transformers import SentenceTransformer
import structlog

from src.retrieval.hybrid import SearchResult
from src.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class VectorStore:
    """Supabase pgvector database interface"""
    
    def __init__(self):
        self.connection_string = settings.DATABASE_URL
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._ensure_table()
    
    async def _get_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.connection_string)
    
    def _ensure_table(self):
        """Create vector table if it doesn't exist"""
        # This would be handled by Supabase migrations
        pass
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[np.ndarray]] = None,
    ):
        """Add documents to vector store"""
        if embeddings is None:
            embeddings = self.model.encode([doc["content"] for doc in documents])
        
        conn = await self._get_connection()
        try:
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                await conn.execute(
                    """
                    INSERT INTO documents (id, content, metadata, document_id, chunk_id, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    doc["id"],
                    doc["content"],
                    json.dumps(doc.get("metadata", {})),
                    doc.get("document_id", ""),
                    doc.get("chunk_id", ""),
                    embedding.tolist()
                )
        finally:
            await conn.close()
    
    async def search(
        self,
        query: str,
        top_k: int = 20,
        score_threshold: float = 0.7,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents using pgvector"""
        query_embedding = self.model.encode([query])[0]
        
        conn = await self._get_connection()
        try:
            # Build WHERE clause for filtering
            where_clause = ""
            if filter:
                conditions = []
                for key, value in filter.items():
                    conditions.append(f"metadata->>'{key}' = '{value}'")
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            # Perform vector similarity search
            query_sql = f"""
                SELECT 
                    id, content, metadata, document_id, chunk_id,
                    1 - (embedding <=> $1) as similarity
                FROM documents
                {where_clause}
                ORDER BY embedding <=> $1
                LIMIT $2
            """
            
            rows = await conn.fetch(query_sql, query_embedding.tolist(), top_k)
            
            results = []
            for row in rows:
                similarity = float(row['similarity'])
                if similarity >= score_threshold:
                    result = SearchResult(
                        content=row['content'],
                        metadata=json.loads(row['metadata']),
                        score=similarity,
                        source="vector",
                    )
                    results.append(result)
            
            return results
            
        finally:
            await conn.close()
    
    async def delete_document(self, document_id: str):
        """Delete all chunks for a document"""
        conn = await self._get_connection()
        try:
            await conn.execute(
                "DELETE FROM documents WHERE document_id = $1",
                document_id
            )
        finally:
            await conn.close()
    
    async def get_collection_info(self):
        """Get collection statistics"""
        conn = await self._get_connection()
        try:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(DISTINCT document_id) as unique_documents,
                    AVG(1 - (embedding <=> embedding)) as avg_similarity
                FROM documents
            """)
            
            return {
                "total_documents": stats['total_documents'],
                "unique_documents": stats['unique_documents'],
                "avg_similarity": float(stats['avg_similarity']) if stats['avg_similarity'] else 0
            }
        finally:
            await conn.close()
