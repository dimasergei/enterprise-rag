from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, AsyncIterator
import asyncio
import json
import time

from src.core.config import get_settings
from src.retrieval.hybrid import HybridRetriever, SearchResult
from src.generation.llm import LLMGenerator
from src.generation.citations import extract_citations
from src.evaluation.metrics import MetricsCollector
from src.api.dependencies import get_retriever, get_llm, get_metrics

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    stream: bool = Field(default=True, description="Stream response")
    top_k: int = Field(default=5, ge=1, le=20)
    use_cache: bool = Field(default=True)

class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any]
    relevance_score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    query_id: str
    latency_ms: float
    cache_hit: bool
    metrics: Dict[str, float]

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMGenerator = Depends(get_llm),
    metrics: MetricsCollector = Depends(get_metrics),
):
    """
    Query documents with hybrid retrieval + LLM generation
    
    Returns answer with citations and source documents
    """
    start_time = metrics.record_query_start()
    
    try:
        # 1. Retrieve relevant documents
        retrieval_start = time.perf_counter()
        results = await retriever.retrieve(
            query=request.query,
            top_k=request.top_k * 4,  # Retrieve more, rerank to top_k
            rerank_top_k=request.top_k,
            use_cache=request.use_cache,
        )
        retrieval_time = time.perf_counter() - retrieval_start
        metrics.record_retrieval_time(retrieval_time)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found"
            )
        
        # 2. Generate answer with LLM
        generation_start = time.perf_counter()
        answer = await llm.generate(
            query=request.query,
            context_documents=results,
        )
        generation_time = time.perf_counter() - generation_start
        metrics.record_generation_time(generation_time)
        
        # 3. Extract citations
        citations = extract_citations(answer, results)
        
        # 4. Prepare response
        total_time = time.perf_counter() - start_time
        metrics.record_query_end(start_time, cache_hit=(retrieval_time < 0.01))
        
        return QueryResponse(
            answer=answer,
            sources=[
                SourceDocument(
                    content=r.content,
                    metadata=r.metadata,
                    relevance_score=r.score,
                )
                for r in results
            ],
            query_id=f"q_{int(time.time())}",
            latency_ms=total_time * 1000,
            cache_hit=(retrieval_time < 0.01),  # Cached if < 10ms
            metrics={
                "retrieval_ms": retrieval_time * 1000,
                "generation_ms": generation_time * 1000,
                "total_ms": total_time * 1000,
                "num_sources": len(results),
            }
        )
        
    except Exception as e:
        metrics.record_query_end(start_time, cache_hit=False)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/stream")
async def query_documents_stream(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMGenerator = Depends(get_llm),
    metrics: MetricsCollector = Depends(get_metrics),
):
    """
    Stream query response with Server-Sent Events
    
    Format:
        data: {"type": "retrieval", "sources": [...]}
        data: {"type": "token", "content": "text"}
        data: {"type": "done", "latency_ms": 1234}
    """
    
    async def generate_stream() -> AsyncIterator[str]:
        start_time = metrics.record_query_start()
        
        try:
            # 1. Retrieve and send sources
            retrieval_start = time.perf_counter()
            results = await retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
                use_cache=request.use_cache,
            )
            retrieval_time = time.perf_counter() - retrieval_start
            metrics.record_retrieval_time(retrieval_time)
            
            sources_data = {
                "type": "retrieval",
                "sources": [
                    {
                        "content": r.content[:200],  # Preview only
                        "metadata": r.metadata,
                        "score": r.score,
                    }
                    for r in results
                ],
            }
            yield f"data: {json.dumps(sources_data)}\n\n"
            
            # 2. Stream LLM response
            generation_start = time.perf_counter()
            answer = ""
            async for token in llm.generate_stream(
                query=request.query,
                context_documents=results,
            ):
                answer += token
                token_data = {"type": "token", "content": token}
                yield f"data: {json.dumps(token_data)}\n\n"
            
            generation_time = time.perf_counter() - generation_start
            metrics.record_generation_time(generation_time)
            
            # 3. Send completion
            total_time = time.perf_counter() - start_time
            metrics.record_query_end(start_time, cache_hit=(retrieval_time < 0.01))
            
            done_data = {
                "type": "done",
                "latency_ms": total_time * 1000,
            }
            yield f"data: {json.dumps(done_data)}\n\n"
            
        except Exception as e:
            metrics.record_query_end(start_time, cache_hit=False)
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
