from typing import Optional
from fastapi import APIRouter, Query

from core.errors import BaseChatSupportException
from models.response import DeleteDocumentResponse, DocumentListResponse
from services.qdrant_service import qdrant_service

router = APIRouter(tags=["Document Management"])


@router.get("/documents", response_model=DocumentListResponse, summary="List registered documents for a tenant")
async def list_documents(
    tenant_id: str = Query(..., description="Tenant identifier", examples=["tenant_acme"]),
) -> DocumentListResponse:
    """Retrieves all registered file names and chunk counts for a given tenant_id."""
    if not tenant_id or not tenant_id.strip():
        raise BaseChatSupportException(
            message="tenant_id query parameter must be provided.",
            error_code="INVALID_PARAMETER",
            status_code=400,
        )

    await qdrant_service.ensure_collection_and_index()
    docs = await qdrant_service.list_tenant_documents(tenant_id.strip())

    return DocumentListResponse(
        status="success",
        tenant_id=tenant_id.strip(),
        total_documents=len(docs),
        documents=docs,
    )


@router.delete("/documents", response_model=DeleteDocumentResponse, summary="Delete specific document or wipe all tenant documents")
async def delete_documents(
    tenant_id: str = Query(..., description="Tenant identifier", examples=["tenant_acme"]),
    file_name: Optional[str] = Query(None, description="Optional filename to delete. If omitted, wipes all tenant documents."),
) -> DeleteDocumentResponse:
    """Deletes vector points for a specific document if file_name is provided, or wipes all tenant documents if omitted."""
    if not tenant_id or not tenant_id.strip():
        raise BaseChatSupportException(
            message="tenant_id query parameter must be provided.",
            error_code="INVALID_PARAMETER",
            status_code=400,
        )

    await qdrant_service.ensure_collection_and_index()

    if file_name and file_name.strip():
        await qdrant_service.delete_document(tenant_id.strip(), file_name.strip())
        message = f"Successfully deleted document '{file_name.strip()}' for tenant '{tenant_id.strip()}'."
    else:
        await qdrant_service.delete_all_tenant_documents(tenant_id.strip())
        message = f"Successfully wiped all documents for tenant '{tenant_id.strip()}'."

    return DeleteDocumentResponse(
        status="success",
        tenant_id=tenant_id.strip(),
        message=message,
    )
