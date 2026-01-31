from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

from src.core.config import get_settings

settings = get_settings()

class DocumentChunker:
    """Smart document chunking with overlap"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Default separators for different document types
        self.separators = separators or [
            "\n\n\n",  # Triple newlines (major sections)
            "\n\n",    # Double newlines (paragraphs)
            "\n",      # Single newlines
            ". ",      # Sentence endings
            "! ",      # Exclamation sentences
            "? ",      # Question sentences
            "; ",      # Semicolons
            ", ",      # Commas (last resort)
            " ",       # Spaces (very last resort)
            ""         # Character level (absolute last resort)
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            separators=self.separators,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
    
    def chunk_document(
        self,
        document: Dict[str, Any],
        preserve_structure: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document into smaller pieces
        
        Args:
            document: Document dict with content and metadata
            preserve_structure: Whether to preserve document structure info
        
        Returns:
            List of chunk dictionaries
        """
        content = document["content"]
        metadata = document.get("metadata", {})
        document_id = document.get("document_id", "")
        
        if preserve_structure:
            # Try to preserve structure by looking for headings
            chunks = self._chunk_with_structure(content, document_id, metadata)
        else:
            # Simple chunking
            chunks = self._simple_chunk(content, document_id, metadata)
        
        return chunks
    
    def _chunk_with_structure(
        self,
        content: str,
        document_id: str,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Chunk while preserving document structure"""
        # Look for markdown-style headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        chunks = []
        current_chunk = ""
        current_header = None
        chunk_id = 0
        
        for line in lines:
            # Check if line is a header
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous chunk if it exists
                if current_chunk.strip():
                    chunk = self._create_chunk(
                        content=current_chunk.strip(),
                        document_id=document_id,
                        chunk_id=f"{document_id}_{chunk_id}",
                        metadata={
                            **metadata,
                            "header": current_header,
                            "chunk_type": "section",
                        },
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk with header
                current_header = header_match.group(2)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                chunk_id=f"{document_id}_{chunk_id}",
                metadata={
                    **metadata,
                    "header": current_header,
                    "chunk_type": "section",
                },
            )
            chunks.append(chunk)
        
        # If no headers were found, fall back to simple chunking
        if len(chunks) == 1:
            return self._simple_chunk(content, document_id, metadata)
        
        return chunks
    
    def _simple_chunk(
        self,
        content: str,
        document_id: str,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Simple recursive character chunking"""
        texts = self.splitter.split_text(content)
        
        chunks = []
        for i, text in enumerate(texts):
            chunk = self._create_chunk(
                content=text,
                document_id=document_id,
                chunk_id=f"{document_id}_{i}",
                metadata={
                    **metadata,
                    "chunk_type": "recursive",
                    "chunk_index": i,
                },
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        document_id: str,
        chunk_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a chunk dictionary"""
        return {
            "content": content,
            "document_id": document_id,
            "chunk_id": chunk_id,
            "metadata": metadata,
            "char_count": len(content),
            "word_count": len(content.split()),
        }
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        preserve_structure: bool = True,
    ) -> List[Dict[str, Any]]:
        """Chunk multiple documents"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_document(doc, preserve_structure)
            all_chunks.extend(chunks)
        
        return all_chunks
