from typing import List
import numpy as np
from sentence_transformers import CrossEncoder
import asyncio

from src.retrieval.hybrid import SearchResult
from src.core.config import get_settings

settings = get_settings()

class Reranker:
    """Cross-encoder reranker for better relevance"""
    
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
        self.model.max_seq_length = 512
    
    async def rerank(
        self,
        query: str,
        documents: List[SearchResult],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Rerank documents using cross-encoder"""
        if not documents:
            return []
        
        # Prepare input pairs
        pairs = [(query, doc.content) for doc in documents]
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            self.model.predict,
            pairs
        )
        
        # Combine with original scores (weighted average)
        reranked_docs = []
        for doc, rerank_score in zip(documents, scores):
            # Weight rerank score more heavily
            combined_score = 0.7 * float(rerank_score) + 0.3 * doc.score
            doc.score = combined_score
            doc.source = "reranked"
            reranked_docs.append(doc)
        
        # Sort by combined score and return top-k
        reranked_docs.sort(key=lambda x: x.score, reverse=True)
        return reranked_docs[:top_k]
