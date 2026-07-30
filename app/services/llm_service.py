from typing import List, Optional
import httpx
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from core.config import settings
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


async def list_available_models(provider: str, api_key: str) -> List[str]:
    """Retrieves available model IDs for a given provider and API key."""
    if not provider or not isinstance(provider, str):
        raise InvalidProviderException(
            provider=str(provider),
            supported_providers=list(SUPPORTED_LLM_PROVIDERS),
        )

    if not api_key or not api_key.strip():
        raise MissingHeaderException(HEADER_LLM_API_KEY)

    provider_clean = provider.strip().lower()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if provider_clean == PROVIDER_OPENAI:
                url = f"{settings.OPENAI_MODELS_API_BASE.rstrip('/')}/models"
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key.strip()}"},
                )
                if response.status_code != 200:
                    raise UpstreamProviderException(
                        provider_name="OpenAI",
                        message=f"Failed to list models: HTTP {response.status_code}",
                        status_code=response.status_code,
                    )
                data = response.json().get("data", [])
                models = [
                    m["id"]
                    for m in data
                    if isinstance(m, dict) and "id" in m and ("gpt" in m["id"] or "o1" in m["id"] or "o3" in m["id"])
                ]
                return sorted(list(set(models)))

            elif provider_clean == PROVIDER_GROQ:
                url = f"{settings.GROQ_MODELS_API_BASE.rstrip('/')}/models"
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key.strip()}"},
                )
                if response.status_code != 200:
                    raise UpstreamProviderException(
                        provider_name="Groq",
                        message=f"Failed to list models: HTTP {response.status_code}",
                        status_code=response.status_code,
                    )
                data = response.json().get("data", [])
                models = [
                    m["id"]
                    for m in data
                    if isinstance(m, dict) and "id" in m and m.get("active", True)
                ]
                return sorted(list(set(models)))

            elif provider_clean == PROVIDER_GEMINI:
                url = f"{settings.GEMINI_MODELS_API_BASE.rstrip('/')}/models?key={api_key.strip()}"
                response = await client.get(url)
                if response.status_code != 200:
                    raise UpstreamProviderException(
                        provider_name="Google Gemini",
                        message=f"Failed to list models: HTTP {response.status_code}",
                        status_code=response.status_code,
                    )
                raw_models = response.json().get("models", [])
                res = []
                for m in raw_models:
                    name = m.get("name", "").replace("models/", "")
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods and "gemini" in name:
                        res.append(name)
                return sorted(list(set(res)))

            else:
                raise InvalidProviderException(
                    provider=provider_clean,
                    supported_providers=list(SUPPORTED_LLM_PROVIDERS),
                )
        except (InvalidProviderException, MissingHeaderException, UpstreamProviderException):
            raise
        except Exception as e:
            raise UpstreamProviderException(
                provider_name=provider_clean.upper(),
                message=f"Failed to query available models: {str(e)}",
            )
