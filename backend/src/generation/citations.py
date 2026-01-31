import re
from typing import List, Dict, Any, Tuple
from src.retrieval.hybrid import SearchResult

def extract_citations(answer: str, documents: List[SearchResult]) -> List[Dict[str, Any]]:
    """
    Extract and format citations from answer
    
    Args:
        answer: Generated answer text
        documents: Source documents used for generation
    
    Returns:
        List of citation objects with metadata
    """
    citations = []
    
    # Find all citation patterns like [Document 1], [Document 2], etc.
    citation_pattern = r'\[Document (\d+)\]'
    matches = re.findall(citation_pattern, answer)
    
    for doc_num in matches:
        try:
            doc_index = int(doc_num) - 1  # Convert to 0-based index
            if 0 <= doc_index < len(documents):
                doc = documents[doc_index]
                citation = {
                    "document_number": int(doc_num),
                    "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "metadata": doc.metadata,
                    "relevance_score": doc.score,
                    "source": doc.source,
                }
                citations.append(citation)
        except (ValueError, IndexError):
            continue
    
    return citations

def format_citations(citations: List[Dict[str, Any]]) -> str:
    """Format citations for display"""
    if not citations:
        return ""
    
    formatted = "\n\n**Sources:**\n"
    for citation in citations:
        source = citation["metadata"].get("source", "Unknown")
        page = citation["metadata"].get("page", "N/A")
        formatted += f"- [Document {citation['document_number']}] {source} (Page {page})\n"
    
    return formatted

def add_citations_to_answer(answer: str, documents: List[SearchResult]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Add citations to answer and return both the formatted answer and citation list
    
    Args:
        answer: Generated answer
        documents: Source documents
    
    Returns:
        Tuple of (formatted_answer_with_citations, citation_list)
    """
    citations = extract_citations(answer, documents)
    formatted_citations = format_citations(citations)
    
    if formatted_citations:
        answer_with_citations = answer + formatted_citations
    else:
        answer_with_citations = answer
    
    return answer_with_citations, citations
