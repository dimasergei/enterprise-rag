from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
import structlog

from src.ingestion.indexer import DocumentIndexer
from src.api.dependencies import get_indexer

logger = structlog.get_logger()
router = APIRouter()

class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_processed: int
    status: str
    message: str

class DocumentListResponse(BaseModel):
    documents: List[Dict[str, Any]]
    total: int

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),  # JSON string
    indexer: DocumentIndexer = Depends(get_indexer),
):
    """
    Upload and ingest a document
    
    Supported formats: PDF, DOCX, TXT, HTML, MD, and more
    """
    try:
        # Validate file type
        supported_formats = indexer.get_supported_formats()
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {', '.join(supported_formats)}"
            )
        
        # Parse metadata if provided
        doc_metadata = {}
        if metadata:
            import json
            try:
                doc_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metadata JSON"
                )
        
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Read file content
        file_bytes = await file.read()
        
        # Ingest document
        logger.info(
            "ingesting_document",
            filename=file.filename,
            document_id=document_id,
            file_size=len(file_bytes)
        )
        
        result = await indexer.ingest_bytes(
            file_bytes=file_bytes,
            filename=file.filename,
            document_id=document_id,
            metadata=doc_metadata,
        )
        
        return IngestResponse(
            document_id=result["document_id"],
            filename=file.filename,
            chunks_processed=result["chunks_processed"],
            status=result["status"],
            message="Document ingested successfully"
        )
        
    except Exception as e:
        logger.error(
            "ingestion_failed",
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/ingest/{document_id}")
async def delete_document(
    document_id: str,
    indexer: DocumentIndexer = Depends(get_indexer),
):
    """Delete a document from the system"""
    try:
        result = await indexer.delete_document(document_id)
        return result
    except Exception as e:
        logger.error(
            "document_deletion_failed",
            document_id=document_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ingest/formats")
async def get_supported_formats(
    indexer: DocumentIndexer = Depends(get_indexer),
):
    """Get list of supported file formats"""
    return {
        "supported_formats": indexer.get_supported_formats(),
        "max_file_size": "50MB"
    }
