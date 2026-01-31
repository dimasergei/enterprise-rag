from typing import List, Dict, Any
import io
from pathlib import Path
import magic
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element

class DocumentParser:
    """Parse various document formats using unstructured.io"""
    
    @staticmethod
    def parse_file(file_path: str) -> List[Dict[str, Any]]:
        """Parse a file and return list of text chunks with metadata"""
        try:
            # Get file type
            mime_type = magic.from_file(file_path, mime=True)
            
            # Parse document
            elements = partition(filename=file_path)
            
            # Convert elements to chunks
            chunks = []
            for i, element in enumerate(elements):
                if hasattr(element, 'text') and element.text.strip():
                    chunk = {
                        "content": element.text.strip(),
                        "metadata": {
                            "source": Path(file_path).name,
                            "file_type": mime_type,
                            "element_type": element.category if hasattr(element, 'category') else 'unknown',
                            "page_number": getattr(element, 'page_number', None),
                            "element_id": i,
                        },
                        "document_id": Path(file_path).stem,
                        "chunk_id": f"{Path(file_path).stem}_{i}",
                    }
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            raise ValueError(f"Failed to parse {file_path}: {str(e)}")
    
    @staticmethod
    def parse_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """Parse file bytes and return list of text chunks with metadata"""
        try:
            # Get file type from bytes
            mime_type = magic.from_buffer(file_bytes, mime=True)
            
            # Parse document from bytes
            elements = partition(file=io.BytesIO(file_bytes))
            
            # Convert elements to chunks
            chunks = []
            for i, element in enumerate(elements):
                if hasattr(element, 'text') and element.text.strip():
                    chunk = {
                        "content": element.text.strip(),
                        "metadata": {
                            "source": filename,
                            "file_type": mime_type,
                            "element_type": element.category if hasattr(element, 'category') else 'unknown',
                            "page_number": getattr(element, 'page_number', None),
                            "element_id": i,
                        },
                        "document_id": Path(filename).stem,
                        "chunk_id": f"{Path(filename).stem}_{i}",
                    }
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            raise ValueError(f"Failed to parse {filename}: {str(e)}")
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported file formats"""
        return [
            "pdf", "docx", "doc", "txt", "rtf", "odt",
            "pptx", "ppt", "xlsx", "xls", "csv",
            "html", "htm", "md", "json", "xml"
        ]
