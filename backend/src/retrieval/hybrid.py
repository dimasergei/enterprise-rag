from typing import List, Dict, Any
import numpy as np
from dataclasses import dataclass
import asyncio

from src.retrieval.vector_store import VectorStore
from src.retrieval.bm25_store import BM25Store
from src.retrieval.reranker import Reranker
from src.retrieval.cache import SemanticCache

@dataclass
class SearchResult:
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str  # "vector", "bm25", or "hybrid"

class HybridRetriever:
    """
    Production-grade hybrid retrieval with:
    - Vector search (semantic)
    - BM25 search (lexical)
    - Reciprocal Rank Fusion
    - Cross-encoder reranking
    - Semantic caching
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_store: BM25Store,
        reranker: Reranker,
        cache: SemanticCache,
        alpha: float = 0.5,  # Weight for vector vs BM25
    ):
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.reranker = reranker
        self.cache = cache
        self.alpha = alpha
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        rerank_top_k: int = 5,
        use_cache: bool = True,
    ) -> List[SearchResult]:
        """
        Hybrid retrieval pipeline with caching
        
        Returns:
            Top-k reranked results with scores
        """
        
        # 1. Check semantic cache
        if use_cache:
            cached_results = await self.cache.get(query)
            if cached_results:
                return cached_results
        
        # 2. Parallel retrieval from vector and BM25
        vector_task = self.vector_store.search(query, top_k=top_k)
        bm25_task = self.bm25_store.search(query, top_k=top_k)
        
        vector_results, bm25_results = await asyncio.gather(
            vector_task, bm25_task
        )
        
        # 3. Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(
            vector_results, bm25_results
        )
        
        # 4. Rerank with cross-encoder
        reranked_results = await self.reranker.rerank(
            query=query,
            documents=fused_results,
            top_k=rerank_top_k,
        )
        
        # 5. Cache results
        if use_cache:
            await self.cache.set(query, reranked_results)
        
        return reranked_results
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: List[SearchResult],
        bm25_results: List[SearchResult],
        k: int = 60,
    ) -> List[SearchResult]:
        """
        RRF formula: score = sum(1 / (k + rank))
        
        This gives 1-9% better recall than single-method retrieval
        """
        
        # Build document ID to result mapping
        doc_map: Dict[str, SearchResult] = {}
        doc_scores: Dict[str, float] = {}
        
        # Process vector results
        for rank, result in enumerate(vector_results, start=1):
            doc_id = self._get_doc_id(result)
            doc_map[doc_id] = result
            doc_scores[doc_id] = self.alpha / (k + rank)
        
        # Process BM25 results
        for rank, result in enumerate(bm25_results, start=1):
            doc_id = self._get_doc_id(result)
            if doc_id not in doc_map:
                doc_map[doc_id] = result
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + (
                (1 - self.alpha) / (k + rank)
            )
        
        # Sort by fused score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        # Return results with updated scores
        results = []
        for doc_id, score in sorted_docs:
            result = doc_map[doc_id]
            result.score = score
            result.source = "hybrid"
            results.append(result)
        
        return results
    
    def _get_doc_id(self, result: SearchResult) -> str:
        """Generate unique ID for deduplication"""
        return f"{result.metadata.get('document_id', '')}_{result.metadata.get('chunk_id', '')}"
