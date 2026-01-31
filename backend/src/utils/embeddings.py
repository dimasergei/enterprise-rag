from openai import AsyncOpenAI
from typing import List
import numpy as np

from src.core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def get_embedding(text: str) -> np.ndarray:
    """Get embedding for text using OpenAI"""
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text
    )
    return np.array(response.data[0].embedding)

async def get_embeddings(texts: List[str]) -> List[np.ndarray]:
    """Get embeddings for multiple texts"""
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts
    )
    return [np.array(data.embedding) for data in response.data]
