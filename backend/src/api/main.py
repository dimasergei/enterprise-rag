from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog
import time

from src.core.config import get_settings
from src.core.logging import setup_logging
from src.api.routes import query, ingest, metrics, health

# Setup
settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = structlog.get_logger()

# FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade RAG system with hybrid retrieval and semantic caching",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    
    # Log request
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        duration_ms=process_time * 1000,
        status_code=response.status_code,
    )
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Routes
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(query.router, prefix=settings.API_PREFIX, tags=["Query"])
app.include_router(ingest.router, prefix=settings.API_PREFIX, tags=["Ingestion"])
app.include_router(metrics.router, prefix=settings.API_PREFIX, tags=["Metrics"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def startup_event():
    logger.info("application_startup", version=settings.VERSION)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("application_shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Use structlog
    )
