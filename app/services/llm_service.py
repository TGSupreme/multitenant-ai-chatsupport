from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from core.constants import (
    HEADER_LLM_API_KEY,
    PROVIDER_GEMINI,
    PROVIDER_GROQ,
    PROVIDER_OPENAI,
    SUPPORTED_LLM_PROVIDERS,
)
from core.errors import InvalidProviderException, MissingHeaderException, UpstreamProviderException


def get_llm(
    provider: str,
    api_key: str,
    model_name: Optional[str] = None,
) -> BaseChatModel:
    """Returns a LangChain BaseChatModel instance based on requested provider and per-request API key."""
    if not provider or not isinstance(provider, str):
        raise InvalidProviderException(
            provider=str(provider),
            supported_providers=list(SUPPORTED_LLM_PROVIDERS),
        )

    if not api_key or not api_key.strip():
        raise MissingHeaderException(HEADER_LLM_API_KEY)

    provider_clean = provider.strip().lower()

    try:
        if provider_clean == PROVIDER_OPENAI:
            return ChatOpenAI(
                api_key=api_key.strip(),
                model=model_name or "gpt-4o-mini",
                temperature=0.2,
            )
        elif provider_clean == PROVIDER_GEMINI:
            return ChatGoogleGenerativeAI(
                google_api_key=api_key.strip(),
                model=model_name or "gemini-1.5-flash",
                temperature=0.2,
            )
        elif provider_clean == PROVIDER_GROQ:
            return ChatGroq(
                api_key=api_key.strip(),
                model=model_name or "llama-3.3-70b-versatile",
                temperature=0.2,
            )
        else:
            raise InvalidProviderException(
                provider=provider_clean,
                supported_providers=list(SUPPORTED_LLM_PROVIDERS),
            )
    except (InvalidProviderException, MissingHeaderException):
        raise
    except Exception as e:
        raise UpstreamProviderException(
            provider_name=provider_clean.upper(),
            message=f"Failed to initialize LLM provider client: {str(e)}",
            status_code=400,
        )
