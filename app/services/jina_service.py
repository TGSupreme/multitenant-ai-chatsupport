from typing import List
import httpx

from core.config import settings
from core.constants import HEADER_JINA_API_KEY
from core.errors import MissingHeaderException, UpstreamProviderException


class JinaEmbeddingsService:
    """Service wrapper for generating text embeddings via Jina AI API using stateless per-request API keys."""

    def __init__(self) -> None:
        self.api_url = settings.JINA_EMBEDDINGS_URL
        self.model_name = settings.JINA_MODEL_NAME

    async def generate_embeddings(
        self,
        texts: List[str],
        jina_api_key: str,
        task: str = "retrieval.passage",
        batch_size: int = 32,
    ) -> List[List[float]]:
        """Generates vector embeddings for a list of text strings using the client's X-Jina-Api-Key."""
        if not jina_api_key or not jina_api_key.strip():
            raise MissingHeaderException(HEADER_JINA_API_KEY)

        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        headers = {
            "Authorization": f"Bearer {jina_api_key.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                payload = {
                    "model": self.model_name,
                    "task": task,
                    "dimensions": 1024,
                    "input": batch_texts,
                }

                try:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                    )
                except httpx.RequestError as exc:
                    raise UpstreamProviderException(
                        provider_name="Jina AI Embeddings",
                        message=f"Network communication failure: {str(exc)}",
                    )

                if response.status_code == 401:
                    raise UpstreamProviderException(
                        provider_name="Jina AI Embeddings",
                        message="Invalid or unauthorized X-Jina-Api-Key provided.",
                        status_code=401,
                    )
                elif response.status_code == 429:
                    raise UpstreamProviderException(
                        provider_name="Jina AI Embeddings",
                        message="Rate limit exceeded on Jina AI API.",
                        status_code=429,
                    )
                elif response.status_code != 200:
                    raise UpstreamProviderException(
                        provider_name="Jina AI Embeddings",
                        message=f"API returned status HTTP {response.status_code}.",
                        status_code=response.status_code,
                    )

                data = response.json()
                data_items = data.get("data", [])
                if not data_items:
                    raise UpstreamProviderException(
                        provider_name="Jina AI Embeddings",
                        message="Jina API returned an empty embedding response payload.",
                    )

                data_items_sorted = sorted(data_items, key=lambda x: x.get("index", 0))
                for item in data_items_sorted:
                    embedding = item.get("embedding")
                    if not embedding:
                        raise UpstreamProviderException(
                            provider_name="Jina AI Embeddings",
                            message="Missing vector embedding payload in response item.",
                        )
                    all_embeddings.append(embedding)

        return all_embeddings

    async def generate_query_embedding(
        self,
        query: str,
        jina_api_key: str,
    ) -> List[float]:
        """Convenience method to vectorize a single RAG search query."""
        if not query or not query.strip():
            raise UpstreamProviderException(
                provider_name="Jina AI Embeddings",
                message="Cannot generate embedding for empty search query.",
                status_code=400,
            )

        embeddings = await self.generate_embeddings(
            texts=[query],
            jina_api_key=jina_api_key,
            task="retrieval.query",
        )
        if not embeddings:
            raise UpstreamProviderException(
                provider_name="Jina AI Embeddings",
                message="Failed to generate query vector embedding.",
            )
        return embeddings[0]


# Singleton instance
jina_service = JinaEmbeddingsService()
