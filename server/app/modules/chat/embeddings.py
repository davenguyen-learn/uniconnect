from google import genai
from app.core.config import settings

def generate_embedding(text: str) -> list[float] | None:
    """Generate a vector embedding for the given text using Gemini."""
    if not settings.GEMINI_API_KEY or not text.strip():
        return None

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    try:
        result = client.models.embed_content(
            model='text-embedding-004',
            contents=text,
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None
