from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = "EnterpriseRAG"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # LLM Settings
    GOOGLE_AI_API_KEY: str  # Gemini-2.0-Flash via Google AI Studio
    LLM_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 3072
    
    # Vector Store (Supabase pgvector)
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    COLLECTION_NAME: str = "documents"
    
    # Redis Cache (Upstash)
    REDIS_URL: str
    REDIS_REST_URL: str
    REDIS_REST_TOKEN: str
    CACHE_TTL: int = 3600
    SEMANTIC_CACHE_THRESHOLD: float = 0.95
    
    # Database
    DATABASE_URL: str
    
    # Retrieval Settings
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 5
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    TIMEOUT_SECONDS: int = 30
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "https://*.vercel.app"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
