from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings


def get_llm(
    temperature: float = 0.3,
    model: str = "gemini-2.5-flash"
):
    """
    Gemini LLM for tutoring, explanations, reasoning
    """
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
    )
def get_embeddings():
    """
    Free & stable embeddings for RAG (no API key required)
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
