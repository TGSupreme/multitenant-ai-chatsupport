from typing import Optional
from fastapi import APIRouter, Header

from core.constants import HEADER_JINA_API_KEY, HEADER_LLM_API_KEY, HEADER_LLM_PROVIDER
from core.errors import MissingHeaderException
from models.request import ChatRequest
from models.response import ChatResponse
from services.rag_service import rag_service

router = APIRouter(tags=["RAG Chat System"])


@router.post("/chat", response_model=ChatResponse, summary="Execute RAG query against tenant knowledge base")
async def chat_query(
    request: ChatRequest,
    x_jina_api_key: Optional[str] = Header(None, alias=HEADER_JINA_API_KEY, description="Jina AI API key for query vectorization"),
    x_llm_api_key: Optional[str] = Header(None, alias=HEADER_LLM_API_KEY, description="API key for selected LLM provider"),
    x_llm_provider: Optional[str] = Header(None, alias=HEADER_LLM_PROVIDER, description="LLM vendor provider ('gemini' | 'openai' | 'groq')"),
) -> ChatResponse:
    """Executes a RAG query: vectorizes prompt via Jina, retrieves tenant Qdrant vectors, and generates grounded answer via chosen LLM provider."""
    if not x_jina_api_key or not x_jina_api_key.strip():
        raise MissingHeaderException(HEADER_JINA_API_KEY)
    if not x_llm_api_key or not x_llm_api_key.strip():
        raise MissingHeaderException(HEADER_LLM_API_KEY)
    if not x_llm_provider or not x_llm_provider.strip():
        raise MissingHeaderException(HEADER_LLM_PROVIDER)

    return await rag_service.process_chat_query(
        request=request,
        jina_api_key=x_jina_api_key.strip(),
        llm_api_key=x_llm_api_key.strip(),
        llm_provider=x_llm_provider.strip().lower(),
    )
