import uuid
from typing import Any, Dict, List, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from core.config import settings
from core.errors import VectorStoreException
from models.response import DocumentItem, SourceChunk


class QdrantService:
    """Service wrapper for Qdrant Cloud operations with tenant payload isolation."""

    def __init__(self) -> None:
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        try:
            if settings.QDRANT_URL:
                self.client = AsyncQdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY or None,
                )
            else:
                # Fallback to in-memory Qdrant client for local testing if QDRANT_URL is unconfigured
                self.client = AsyncQdrantClient(location=":memory:")
        except Exception as e:
            raise VectorStoreException(f"Failed to initialize Qdrant client: {str(e)}")

    async def ensure_collection_and_index(self, vector_size: int = 1024) -> None:
        """Ensures the Qdrant collection exists and initializes payload keyword indexes for tenant isolation."""
        try:
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE,
                    ),
                )

            # Create Keyword Index on tenant_id for hardware-accelerated payload filtering
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="tenant_id",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )

            # Create Keyword Index on file_name for document management operations
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="file_name",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to initialize collection or payload index: {str(e)}")

    async def upsert_chunks(
        self,
        tenant_id: str,
        file_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """Upserts text chunks and vector embeddings into Qdrant under a given tenant_id."""
        if not chunks or not embeddings:
            return 0

        if len(chunks) != len(embeddings):
            raise VectorStoreException("Mismatched chunk and embedding counts for vector upsert.")

        try:
            # First, purge any existing vectors matching (tenant_id, file_name) for auto-update lifecycle
            await self.delete_document(tenant_id=tenant_id, file_name=file_name)

            points = []
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                payload = {
                    "tenant_id": tenant_id,
                    "file_name": file_name,
                    "chunk_index": chunk.get("chunk_index", idx),
                    "page_number": chunk.get("page_number"),
                    "text": chunk.get("text", ""),
                }
                points.append(
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                )

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            return len(points)
        except Exception as e:
            raise VectorStoreException(f"Failed to upsert chunks to vector store: {str(e)}")

    async def search_tenant_vectors(
        self,
        tenant_id: str,
        query_vector: List[float],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Performs vector similarity search strictly filtered by tenant_id."""
        try:
            tenant_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id),
                    )
                ]
            )

            # Support query_points (qdrant-client v1.10+) with fallbacks for maximum compatibility
            if hasattr(self.client, "query_points"):
                query_res = await self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=tenant_filter,
                    limit=top_k,
                )
                results = query_res.points
            elif hasattr(self.client, "search"):
                results = await self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=tenant_filter,
                    limit=top_k,
                )
            else:
                results = await self.client.search_points(
                    collection_name=self.collection_name,
                    vector=query_vector,
                    query_filter=tenant_filter,
                    limit=top_k,
                )

            sources = []
            for res in results:
                payload = res.payload or {}
                sources.append(
                    {
                        "id": str(res.id),
                        "file_name": payload.get("file_name", "unknown"),
                        "page_number": payload.get("page_number"),
                        "text": payload.get("text", ""),
                        "score": round(res.score, 4) if res.score else None,
                    }
                )
            return sources
        except Exception as e:
            raise VectorStoreException(f"Failed to search tenant vectors: {str(e)}")

    async def delete_document(self, tenant_id: str, file_name: str) -> None:
        """Deletes all vector points associated with a specific document under a given tenant_id."""
        try:
            filter_condition = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id),
                    ),
                    qmodels.FieldCondition(
                        key="file_name",
                        match=qmodels.MatchValue(value=file_name),
                    ),
                ]
            )
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(filter=filter_condition),
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to delete document '{file_name}': {str(e)}")

    async def delete_all_tenant_documents(self, tenant_id: str) -> None:
        """Deletes all vector points belonging to a tenant_id."""
        try:
            filter_condition = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id),
                    )
                ]
            )
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(filter=filter_condition),
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to delete documents for tenant '{tenant_id}': {str(e)}")

    async def list_tenant_documents(self, tenant_id: str) -> List[DocumentItem]:
        """Lists distinct uploaded documents and total chunk counts for a given tenant_id."""
        try:
            tenant_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="tenant_id",
                        match=qmodels.MatchValue(value=tenant_id),
                    )
                ]
            )

            # Scroll through points matching tenant_id to aggregate chunk counts by file_name
            offset = None
            file_chunk_counts: Dict[str, int] = {}

            while True:
                scroll_result, next_offset = await self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=tenant_filter,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )

                for point in scroll_result:
                    payload = point.payload or {}
                    fn = payload.get("file_name", "unknown")
                    file_chunk_counts[fn] = file_chunk_counts.get(fn, 0) + 1

                if next_offset is None or not scroll_result:
                    break
                offset = next_offset

            return [
                DocumentItem(file_name=fn, total_chunks=count)
                for fn, count in file_chunk_counts.items()
            ]
        except Exception as e:
            raise VectorStoreException(f"Failed to list documents for tenant '{tenant_id}': {str(e)}")


# Singleton instance
qdrant_service = QdrantService()
