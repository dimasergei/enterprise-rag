from typing import List, Dict, Any, Optional
import numpy as np
import asyncio
from openai import AsyncOpenAI
import structlog

from src.core.config import get_settings
from src.utils.embeddings import get_embeddings

logger = structlog.get_logger()
settings = get_settings()

class DocumentEmbedder:
    """Generate embeddings for documents using OpenAI"""
    
    def __init__(self, batch_size: int = 100):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.batch_size = batch_size
    
    async def embed_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of documents
        
        Args:
            documents: List of document dictionaries
            batch_size: Number of documents to process in each batch
        
        Returns:
            List of documents with embeddings added
        """
        batch_size = batch_size or self.batch_size
        
        # Extract content for embedding
        contents = [doc["content"] for doc in documents]
        
        # Process in batches to avoid rate limits
        all_embeddings = []
        
        for i in range(0, len(contents), batch_size):
            batch_contents = contents[i:i + batch_size]
            
            try:
                batch_embeddings = await get_embeddings(batch_contents)
                all_embeddings.extend(batch_embeddings)
                
                logger.info(
                    "embeddings_generated",
                    batch_size=len(batch_contents),
                    batch_index=i // batch_size,
                    total_batches=(len(contents) + batch_size - 1) // batch_size,
                )
                
            except Exception as e:
                logger.error(
                    "embedding_batch_failed",
                    error=str(e),
                    batch_index=i // batch_size,
                )
                raise
        
        # Add embeddings to documents
        documents_with_embeddings = []
        for doc, embedding in zip(documents, all_embeddings):
            doc_with_embedding = doc.copy()
            doc_with_embedding["embedding"] = embedding.tolist()
            documents_with_embeddings.append(doc_with_embedding)
        
        return documents_with_embeddings
    
    async def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        try:
            embedding = await get_embeddings([query])
            return embedding[0]
        except Exception as e:
            logger.error("query_embedding_failed", error=str(e))
            raise
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model": self.model,
            "dimensions": self.dimensions,
            "batch_size": self.batch_size,
        }
