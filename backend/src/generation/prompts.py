from typing import List
from src.retrieval.hybrid import SearchResult

def build_rag_prompt(query: str, documents: List[SearchResult]) -> str:
    """
    Build RAG prompt with best practices:
    - Clear instructions
    - Structured context
    - Citation requirements
    - Grounding instructions
    """
    
    # Format context documents
    context_parts = []
    for i, doc in enumerate(documents, start=1):
        source_info = doc.metadata.get('source', 'Unknown')
        page_info = doc.metadata.get('page', 'N/A')
        
        context_parts.append(
            f"[Document {i}] (Source: {source_info}, Page: {page_info})\n"
            f"{doc.content}\n"
        )
    
    context_text = "\n".join(context_parts)
    
    prompt = f"""You are a helpful AI assistant that answers questions based on provided context documents.

INSTRUCTIONS:
1. Answer the question using ONLY information from the provided context documents
2. If the answer is not in the context, say "I cannot answer this based on the provided documents"
3. Cite your sources using the document numbers (e.g., [Document 1])
4. Be concise but comprehensive
5. If multiple documents provide relevant information, synthesize them

CONTEXT DOCUMENTS:
{context_text}

QUESTION:
{query}

ANSWER:
"""
    
    return prompt
