from typing import List, Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime
import structlog

from src.ingestion.parsers import DocumentParser
from src.ingestion.chunker import DocumentChunker
from src.ingestion.embedder import DocumentEmbedder
from src.retrieval.vector_store import VectorStore
from src.retrieval.bm25_store import BM25Store
from src.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class DocumentIndexer:
    """Complete document ingestion pipeline"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_store: BM25Store,
    ):
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.parser = DocumentParser()
        self.chunker = DocumentChunker()
        self.embedder = DocumentEmbedder()
    
    async def ingest_file(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a single file
        
        Args:
            file_path: Path to the file
            document_id: Optional document ID (auto-generated if not provided)
            metadata: Optional metadata to attach to document
        
        Returns:
            Ingestion statistics
        """
        if not document_id:
            document_id = str(uuid.uuid4())
        
        if not metadata:
            metadata = {}
        
        try:
            # Parse document
            logger.info("parsing_document", file_path=file_path)
            parsed_chunks = self.parser.parse_file(file_path)
            
            if not parsed_chunks:
                raise ValueError("No content extracted from document")
            
            # Add document ID and metadata to all chunks
            for chunk in parsed_chunks:
                chunk["document_id"] = document_id
                chunk["metadata"].update(metadata)
                chunk["metadata"]["ingested_at"] = datetime.utcnow().isoformat()
            
            # Chunk documents (if not already chunked by parser)
            if len(parsed_chunks) == 1:
                logger.info("chunking_document", chunks_before=len(parsed_chunks))
                parsed_chunks = self.chunker.chunk_documents(parsed_chunks)
                logger.info("chunking_complete", chunks_after=len(parsed_chunks))
            
            # Generate embeddings
            logger.info("generating_embeddings", num_chunks=len(parsed_chunks))
            documents_with_embeddings = await self.embedder.embed_documents(parsed_chunks)
            
            # Add to vector store
            logger.info("adding_to_vector_store", num_documents=len(documents_with_embeddings))
            await self.vector_store.add_documents(documents_with_embeddings)
            
            # Update BM25 index
            logger.info("updating_bm25_index")
            await self._update_bm25_index(documents_with_embeddings)
            
            stats = {
                "document_id": document_id,
                "file_path": file_path,
                "chunks_processed": len(documents_with_embeddings),
                "status": "success",
                "ingested_at": datetime.utcnow().isoformat(),
            }
            
            logger.info("ingestion_complete", **stats)
            return stats
            
        except Exception as e:
            error_stats = {
                "document_id": document_id,
                "file_path": file_path,
                "status": "error",
                "error": str(e),
                "ingested_at": datetime.utcnow().isoformat(),
            }
            logger.error("ingestion_failed", **error_stats)
            raise
    
    async def ingest_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest file bytes
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            document_id: Optional document ID
            metadata: Optional metadata
        
        Returns:
            Ingestion statistics
        """
        if not document_id:
            document_id = str(uuid.uuid4())
        
        if not metadata:
            metadata = {}
        
        try:
            # Parse document from bytes
            logger.info("parsing_document_bytes", filename=filename)
            parsed_chunks = self.parser.parse_bytes(file_bytes, filename)
            
            if not parsed_chunks:
                raise ValueError("No content extracted from document")
            
            # Add document ID and metadata to all chunks
            for chunk in parsed_chunks:
                chunk["document_id"] = document_id
                chunk["metadata"].update(metadata)
                chunk["metadata"]["ingested_at"] = datetime.utcnow().isoformat()
            
            # Chunk documents (if not already chunked by parser)
            if len(parsed_chunks) == 1:
                logger.info("chunking_document", chunks_before=len(parsed_chunks))
                parsed_chunks = self.chunker.chunk_documents(parsed_chunks)
                logger.info("chunking_complete", chunks_after=len(parsed_chunks))
            
            # Generate embeddings
            logger.info("generating_embeddings", num_chunks=len(parsed_chunks))
            documents_with_embeddings = await self.embedder.embed_documents(parsed_chunks)
            
            # Add to vector store
            logger.info("adding_to_vector_store", num_documents=len(documents_with_embeddings))
            await self.vector_store.add_documents(documents_with_embeddings)
            
            # Update BM25 index
            logger.info("updating_bm25_index")
            await self._update_bm25_index(documents_with_embeddings)
            
            stats = {
                "document_id": document_id,
                "filename": filename,
                "chunks_processed": len(documents_with_embeddings),
                "status": "success",
                "ingested_at": datetime.utcnow().isoformat(),
            }
            
            logger.info("ingestion_complete", **stats)
            return stats
            
        except Exception as e:
            error_stats = {
                "document_id": document_id,
                "filename": filename,
                "status": "error",
                "error": str(e),
                "ingested_at": datetime.utcnow().isoformat(),
            }
            logger.error("ingestion_failed", **error_stats)
            raise
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document from all stores"""
        try:
            # Delete from vector store
            await self.vector_store.delete_document(document_id)
            
            # For BM25, we'd need to rebuild the index
            # In production, implement incremental BM25 updates
            logger.info("document_deleted", document_id=document_id)
            
            return {
                "document_id": document_id,
                "status": "deleted",
                "deleted_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error("document_deletion_failed", document_id=document_id, error=str(e))
            raise
    
    async def _update_bm25_index(self, new_documents: List[Dict[str, Any]]):
        """Update BM25 index with new documents"""
        # In a production system, you'd want to:
        # 1. Load existing documents from BM25 store
        # 2. Add new documents
        # 3. Rebuild index
        
        # For now, we'll just add the new documents
        # This is a simplification - in production, implement proper incremental updates
        await self.bm25_store.add_documents(new_documents)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return self.parser.get_supported_formats()
