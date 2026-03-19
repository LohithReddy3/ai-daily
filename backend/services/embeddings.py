import google.generativeai as genai
import os
import logging
import asyncio
from typing import List, Optional

logger = logging.getLogger(__name__)

# Configure Gemini (re-using env var from llm.py approach)
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

EMBEDDING_MODEL = "models/gemini-embedding-001"

async def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a vector embedding for the given text using Gemini.
    Returns a list of floats (default 768 dimensions for text-embedding-004).
    """
    if not text or not text.strip():
        return None
        
    try:
        # Run in thread executor to avoid blocking async loop
        result = await asyncio.to_thread(
            genai.embed_content,
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document" # Best for storing in DB
        )
        
        if 'embedding' in result:
            return result['embedding']
        else:
            logger.error("Gemini embedding response missing 'embedding' key")
            return None
            
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None
