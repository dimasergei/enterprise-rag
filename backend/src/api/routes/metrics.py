from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from typing import Dict, Any, List
import structlog
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.evaluation.metrics import MetricsCollector
from src.api.dependencies import get_metrics

logger = structlog.get_logger()
router = APIRouter()

class MetricsResponse(BaseModel):
    current: Dict[str, Any]
    history: List[Dict[str, Any]]

@router.get("/metrics", response_model=MetricsResponse)
async def get_system_metrics(
    metrics: MetricsCollector = Depends(get_metrics),
):
    """Get current system metrics and historical data"""
    try:
        current_metrics = await metrics.get_metrics_summary()
        history = await metrics.get_latency_history()
        
        return MetricsResponse(
            current=current_metrics,
            history=history
        )
    except Exception as e:
        logger.error("metrics_fetch_failed", error=str(e))
        raise

@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus metrics in OpenMetrics format"""
    try:
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error("prometheus_metrics_failed", error=str(e))
        raise

@router.get("/metrics/health")
async def get_health_metrics(
    metrics: MetricsCollector = Depends(get_metrics),
):
    """Get health check metrics"""
    try:
        current = await metrics.get_metrics_summary()
        
        # Determine health status
        is_healthy = (
            current.get("retrieval_latency_p95", 999) < 200 and
            current.get("total_latency_p95", 9999) < 2000 and
            current.get("cache_hit_rate", 0) > 0.3
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "metrics": current,
            "checks": {
                "latency_ok": current.get("retrieval_latency_p95", 999) < 200,
                "cache_ok": current.get("cache_hit_rate", 0) > 0.3,
                "documents_ok": current.get("documents_indexed", 0) > 0,
            }
        }
    except Exception as e:
        logger.error("health_metrics_failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/metrics/real-time")
async def get_real_time_metrics(
    metrics: MetricsCollector = Depends(get_metrics),
):
    """Get real-time performance metrics"""
    try:
        current = await metrics.get_metrics_summary()
        
        return {
            "p95_latency_ms": current.get("retrieval_latency_p95", 0),
            "query_volume": current.get("queries_today", 0),
            "cache_hit_rate": current.get("cache_hit_rate", 0),
            "faithfulness_score": current.get("faithfulness_score", 0),
            "answer_relevancy": current.get("answer_relevancy", 0),
            "cost_per_query": current.get("cost_per_query", 0),
            "documents_indexed": current.get("documents_indexed", 0),
        }
    except Exception as e:
        logger.error("real_time_metrics_failed", error=str(e))
        raise
