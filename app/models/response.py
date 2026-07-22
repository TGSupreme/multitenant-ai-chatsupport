from typing import List, Optional
from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    """Represents a retrieved source document citation reference used in RAG generation."""
    file_name: str = Field(..., description="Original filename of the document", example="return_policy.pdf")
    page_number: Optional[int] = Field(default=None, description="Page number in original document", example=1)
    score: Optional[float] = Field(default=None, description="Vector similarity score", example=0.87)


class ChatResponse(BaseModel):
    """Response payload for POST /chat endpoint."""
    status: str = Field(default="success", description="Status string", example="success")
    tenant_id: str = Field(..., description="Tenant identifier", example="tenant_acme")
    provider: str = Field(..., description="LLM provider used", example="gemini")
    model_name: str = Field(..., description="LLM model used", example="gemini-1.5-flash")
    answer: str = Field(..., description="Generated answer", example="You can return products within 30 days.")
    needs_escalation: bool = Field(
        default=False,
        description="Flag indicating if query requires human support escalation",
        example=False,
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Reason for human escalation if triggered ('NO_MATCHING_DOCUMENTS', 'LOW_CONFIDENCE_SCORE', 'INSUFFICIENT_CONTEXT', 'HUMAN_AGENT_REQUESTED')",
        example=None,
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of cited vector chunk point IDs",
        example=["c8a1b2d3-4e5f-6a7b-8c9d-0e1f2a3b4c5d"],
    )


class IngestResponse(BaseModel):
    """Response payload for POST /ingest endpoint."""
    status: str = Field(default="success", description="Status string", example="success")
    tenant_id: str = Field(..., description="Tenant identifier", example="tenant_acme")
    file_name: str = Field(..., description="Name of the processed PDF", example="return_policy.pdf")
    chunks_processed: int = Field(..., description="Total semantic chunks created and indexed", example=12)
    message: str = Field(..., description="Status message", example="Document successfully ingested and indexed.")


class DocumentItem(BaseModel):
    """Item representing a registered document for a tenant."""
    file_name: str = Field(..., description="Name of the document", example="return_policy.pdf")
    total_chunks: int = Field(..., description="Total vector chunks in database", example=12)


class DocumentListResponse(BaseModel):
    """Response payload for GET /documents endpoint."""
    status: str = Field(default="success", description="Status string", example="success")
    tenant_id: str = Field(..., description="Tenant identifier", example="tenant_acme")
    total_documents: int = Field(..., description="Count of distinct documents", example=2)
    documents: List[DocumentItem] = Field(
        default_factory=list,
        description="List of registered tenant documents and chunk counts",
    )


class DeleteDocumentResponse(BaseModel):
    """Response payload for DELETE /documents endpoint."""
    status: str = Field(default="success", description="Status string", example="success")
    tenant_id: str = Field(..., description="Tenant identifier", example="tenant_acme")
    message: str = Field(..., description="Deletion confirmation message", example="Successfully deleted document 'return_policy.pdf'.")


class ModelListResponse(BaseModel):
    """Response payload for GET /models endpoint."""
    status: str = Field(default="success", description="Status string", example="success")
    provider: str = Field(..., description="LLM provider name", example="gemini")
    available_models: List[str] = Field(
        default_factory=list,
        description="List of available active model IDs for the provided API key",
        example=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
    )
