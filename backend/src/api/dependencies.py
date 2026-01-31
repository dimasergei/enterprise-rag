from functools import lru_cache
from typing import AsyncGenerator
import redis.asyncio as redis
import structlog

from src.core.config import get_settings
from src.retrieval.vector_store import VectorStore
from src.retrieval.bm25_store import BM25Store
from src.retrieval.reranker import Reranker
from src.retrieval.cache import SemanticCache
from src.retrieval.hybrid import HybridRetriever
from src.generation.llm import LLMGenerator
from src.ingestion.indexer import DocumentIndexer
from src.evaluation.metrics import MetricsCollector

logger = structlog.get_logger()
settings = get_settings()

# Redis client
@lru_cache()
def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    return redis.from_url(settings.REDIS_URL)

# Vector store
@lru_cache()
def get_vector_store() -> VectorStore:
    """Get vector store instance"""
    return VectorStore()

# BM25 store
def get_bm25_store() -> BM25Store:
    """Get BM25 store instance"""
    redis_client = get_redis_client()
    return BM25Store(redis_client)

# Reranker
@lru_cache()
def get_reranker() -> Reranker:
    """Get reranker instance"""
    return Reranker()

# Semantic cache
def get_semantic_cache() -> SemanticCache:
    """Get semantic cache instance"""
    redis_client = get_redis_client()
    return SemanticCache(
        redis_client=redis_client,
        threshold=settings.SEMANTIC_CACHE_THRESHOLD,
        ttl=settings.CACHE_TTL,
    )

# Hybrid retriever
def get_retriever() -> HybridRetriever:
    """Get hybrid retriever instance"""
    vector_store = get_vector_store()
    bm25_store = get_bm25_store()
    reranker = get_reranker()
    cache = get_semantic_cache()
    
    return HybridRetriever(
        vector_store=vector_store,
        bm25_store=bm25_store,
        reranker=reranker,
        cache=cache,
    )

# LLM generator
@lru_cache()
def get_llm() -> LLMGenerator:
    """Get LLM generator instance"""
    return LLMGenerator()

# Document indexer
def get_indexer() -> DocumentIndexer:
    """Get document indexer instance"""
    vector_store = get_vector_store()
    bm25_store = get_bm25_store()
    
    return DocumentIndexer(
        vector_store=vector_store,
        bm25_store=bm25_store,
    )

# Metrics collector
def get_metrics() -> MetricsCollector:
    """Get metrics collector instance"""
    redis_client = get_redis_client()
    return MetricsCollector(redis_client)
