from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
import pickle
import redis.asyncio as redis

from src.retrieval.hybrid import SearchResult
from src.core.config import get_settings

settings = get_settings()

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class BM25Store:
    """BM25 search store with Redis persistence"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.bm25_index = None
        self.documents = []
        self.doc_mapping = {}  # Maps index to document info
    
    async def build_index(self, documents: List[Dict[str, Any]]):
        """Build BM25 index from documents"""
        self.documents = documents
        
        # Tokenize documents
        tokenized_docs = []
        for i, doc in enumerate(documents):
            tokens = word_tokenize(doc["content"].lower())
            tokenized_docs.append(tokens)
            self.doc_mapping[i] = {
                "content": doc["content"],
                "metadata": doc.get("metadata", {}),
                "document_id": doc.get("document_id", ""),
                "chunk_id": doc.get("chunk_id", ""),
            }
        
        # Build BM25 index
        self.bm25_index = BM25Okapi(tokenized_docs)
        
        # Save to Redis
        await self._save_to_redis()
    
    async def search(
        self,
        query: str,
        top_k: int = 20,
    ) -> List[SearchResult]:
        """Search using BM25"""
        if not self.bm25_index:
            # Try to load from Redis
            await self._load_from_redis()
            if not self.bm25_index:
                return []
        
        # Tokenize query
        query_tokens = word_tokenize(query.lower())
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top-k results
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include relevant results
                doc_info = self.doc_mapping[idx]
                result = SearchResult(
                    content=doc_info["content"],
                    metadata=doc_info["metadata"],
                    score=float(scores[idx]),
                    source="bm25",
                )
                results.append(result)
        
        return results
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents and rebuild index"""
        # For simplicity, rebuild entire index
        # In production, implement incremental updates
        await self.build_index(documents)
    
    async def _save_to_redis(self):
        """Save BM25 index to Redis"""
        if not self.bm25_index:
            return
        
        # Serialize BM25 index
        bm25_data = {
            "corpus": self.bm25_index.corpus,
            "idf": self.bm25_index.idf,
            "doc_len": self.bm25_index.doc_len,
            "doc_freqs": self.bm25_index.doc_freqs,
        }
        
        # Save to Redis
        await self.redis.set(
            "bm25_index",
            pickle.dumps(bm25_data)
        )
        await self.redis.set(
            "bm25_documents",
            pickle.dumps(self.doc_mapping)
        )
    
    async def _load_from_redis(self):
        """Load BM25 index from Redis"""
        try:
            # Load BM25 index
            bm25_data = await self.redis.get("bm25_index")
            if bm25_data:
                bm25_dict = pickle.loads(bm25_data)
                self.bm25_index = BM25Okapi(bm25_dict["corpus"])
                self.bm25_index.idf = bm25_dict["idf"]
                self.bm25_index.doc_len = bm25_dict["doc_len"]
                self.bm25_index.doc_freqs = bm25_dict["doc_freqs"]
            
            # Load document mapping
            doc_data = await self.redis.get("bm25_documents")
            if doc_data:
                self.doc_mapping = pickle.loads(doc_data)
                
        except Exception:
            # If loading fails, start fresh
            pass
