from google import genai
from google.genai import types
from app.core.config import settings

def generate_embedding(text: str) -> list[float] | None:
    """Generate a 768-dimensional vector embedding for the given text using Gemini."""
    if not settings.GEMINI_API_KEY or not text.strip():
        return None

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    try:
        result = client.models.embed_content(
            model='gemini-embedding-001',
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None
