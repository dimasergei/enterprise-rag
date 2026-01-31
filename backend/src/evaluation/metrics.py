from typing import Dict, List, Any
import time
import numpy as np
from prometheus_client import Counter, Histogram, Gauge
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()

# Prometheus metrics
QUERY_COUNTER = Counter("rag_queries_total", "Total queries processed")
QUERY_LATENCY = Histogram("rag_query_latency_seconds", "Query latency")
RETRIEVAL_LATENCY = Histogram("rag_retrieval_latency_seconds", "Retrieval latency")
GENERATION_LATENCY = Histogram("rag_generation_latency_seconds", "Generation latency")
CACHE_HIT_COUNTER = Counter("rag_cache_hits_total", "Total cache hits")
CACHE_MISS_COUNTER = Counter("rag_cache_misses_total", "Total cache misses")
TOKEN_USAGE = Counter("rag_tokens_total", "Total tokens used", ["model", "type"])
COST_TRACKER = Counter("rag_cost_total", "Total cost in USD", ["service"])
DOCUMENTS_INDEXED = Gauge("rag_documents_indexed", "Number of documents indexed")

class MetricsCollector:
    """Collect and track system metrics"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.query_times = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_query_start(self) -> float:
        """Record query start time"""
        return time.perf_counter()
    
    def record_query_end(self, start_time: float, cache_hit: bool = False):
        """Record query completion"""
        duration = time.perf_counter() - start_time
        QUERY_LATENCY.observe(duration)
        QUERY_COUNTER.inc()
        
        self.query_times.append(duration)
        
        if cache_hit:
            CACHE_HIT_COUNTER.inc()
            self.cache_hits += 1
        else:
            CACHE_MISS_COUNTER.inc()
            self.cache_misses += 1
        
        # Store in Redis for dashboard
        asyncio.create_task(self._store_metrics())
    
    def record_retrieval_time(self, duration: float):
        """Record retrieval latency"""
        RETRIEVAL_LATENCY.observe(duration)
    
    def record_generation_time(self, duration: float):
        """Record generation latency"""
        GENERATION_LATENCY.observe(duration)
    
    def record_token_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Record LLM token usage"""
        TOKEN_USAGE.labels(model=model, type="input").inc(input_tokens)
        TOKEN_USAGE.labels(model=model, type="output").inc(output_tokens)
        
        # Calculate cost (approximate)
        # Claude 3.5 Sonnet: $3/1M input, $15/1M output
        input_cost = (input_tokens / 1_000_000) * 3
        output_cost = (output_tokens / 1_000_000) * 15
        total_cost = input_cost + output_cost
        
        COST_TRACKER.labels(service="llm").inc(total_cost)
    
    def record_documents_indexed(self, count: int):
        """Update document count"""
        DOCUMENTS_INDEXED.set(count)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        try:
            # Calculate percentiles
            if self.query_times:
                p50 = np.percentile(self.query_times, 50)
                p95 = np.percentile(self.query_times, 95)
                p99 = np.percentile(self.query_times, 99)
            else:
                p50 = p95 = p99 = 0
            
            # Cache hit rate
            total_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
            
            # Get document count from Prometheus
            docs_indexed = DOCUMENTS_INDEXED._value._value
            
            # Estimate cost per query
            cost_per_query = 0.018  # Default estimate with caching
            
            return {
                "retrieval_latency_p50": p50 * 1000,  # Convert to ms
                "retrieval_latency_p95": p95 * 1000,
                "total_latency_p95": p95 * 1000,  # Simplified
                "cache_hit_rate": cache_hit_rate,
                "cost_per_query": cost_per_query,
                "documents_indexed": int(docs_indexed),
                "queries_today": total_requests,
                "faithfulness_score": 0.92,  # Mock values - should come from RAGAS
                "answer_relevancy": 0.88,
            }
            
        except Exception as e:
            logger.error("metrics_collection_failed", error=str(e))
            return {}
    
    async def _store_metrics(self):
        """Store metrics in Redis for dashboard"""
        try:
            metrics = await self.get_metrics_summary()
            await self.redis.setex(
                "current_metrics",
                60,  # 1 minute TTL
                str(metrics)
            )
        except Exception as e:
            logger.error("metrics_storage_failed", error=str(e))
    
    async def get_latency_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get latency history for charts"""
        # In a real implementation, this would query a time-series database
        # For now, return mock data
        import random
        from datetime import datetime, timedelta
        
        history = []
        now = datetime.now()
        
        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            history.append({
                "time": timestamp.strftime("%H:%M"),
                "p95_latency": random.uniform(150, 250),
                "p50_latency": random.uniform(80, 120),
                "queries": random.randint(10, 50),
            })
        
        return list(reversed(history))
