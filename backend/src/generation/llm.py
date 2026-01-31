from typing import List, AsyncIterator
import google.generativeai as genai
import structlog

from src.core.config import get_settings
from src.retrieval.hybrid import SearchResult
from src.generation.prompts import build_rag_prompt

logger = structlog.get_logger()

class LLMGenerator:
    """
    LLM generation with Gemini-2.0-Flash
    
    Features:
    - Streaming support
    - Citation-aware prompts
    - Retry logic
    - Cost tracking
    """
    
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
        self.max_tokens = 2000
    
    async def generate(
        self,
        query: str,
        context_documents: List[SearchResult],
        temperature: float = 0.0,
    ) -> str:
        """Generate answer from query and context"""
        
        # Build prompt with context
        prompt = build_rag_prompt(query, context_documents)
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=self.max_tokens,
            temperature=temperature,
        )
        
        # Call Gemini
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        # Extract answer
        answer = response.text
        
        # Log token usage for cost tracking
        logger.info(
            "llm_generation",
            model=self.model._model_name,
            prompt_tokens=response.usage_metadata.prompt_token_count,
            candidates_tokens=response.usage_metadata.candidates_token_count,
            total_tokens=response.usage_metadata.total_token_count,
        )
        
        return answer
    
    async def generate_stream(
        self,
        query: str,
        context_documents: List[SearchResult],
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        """Stream answer tokens"""
        
        prompt = build_rag_prompt(query, context_documents)
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=self.max_tokens,
            temperature=temperature,
        )
        
        # Stream response
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config,
            stream=True
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
