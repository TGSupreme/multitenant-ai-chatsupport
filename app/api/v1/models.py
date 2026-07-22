from typing import Optional
from fastapi import APIRouter, Header

from core.constants import HEADER_LLM_API_KEY, HEADER_LLM_PROVIDER
from core.errors import MissingHeaderException
from models.response import ModelListResponse
from services.llm_service import list_available_models

router = APIRouter(tags=["LLM Provider Models"])


@router.get("/models", response_model=ModelListResponse, summary="List available active LLM models for a provider API key")
async def list_models(
    x_llm_provider: Optional[str] = Header(None, alias=HEADER_LLM_PROVIDER, description="LLM vendor provider ('gemini' | 'openai' | 'groq')"),
    x_llm_api_key: Optional[str] = Header(None, alias=HEADER_LLM_API_KEY, description="API key for selected LLM provider"),
) -> ModelListResponse:
    """Queries provider API endpoints to return active available models for the given API key."""
    if not x_llm_provider or not x_llm_provider.strip():
        raise MissingHeaderException(HEADER_LLM_PROVIDER)
    if not x_llm_api_key or not x_llm_api_key.strip():
        raise MissingHeaderException(HEADER_LLM_API_KEY)

    models = await list_available_models(
        provider=x_llm_provider.strip().lower(),
        api_key=x_llm_api_key.strip(),
    )

    return ModelListResponse(
        status="success",
        provider=x_llm_provider.strip().lower(),
        available_models=models,
    )
