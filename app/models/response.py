from typing import List, Optional
from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    """Represents a retrieved source document citation reference used in RAG generation."""
    file_name: str = Field(..., description="Original filename of the document", examples=["return_policy.pdf"])
    page_number: Optional[int] = Field(default=None, description="Page number in original document", examples=[1])
    score: Optional[float] = Field(default=None, description="Vector similarity score", examples=[0.87])


class ChatResponse(BaseModel):
    """Response payload for POST /chat endpoint."""
    status: str = Field(default="success", description="Status string", examples=["success"])
    tenant_id: str = Field(..., description="Tenant identifier", examples=["tenant_acme"])
    provider: str = Field(..., description="LLM provider used", examples=["gemini"])
    model_name: str = Field(..., description="LLM model used", examples=["gemini-1.5-flash"])
    answer: str = Field(..., description="Generated answer", examples=["You can return products within 30 days."])
    needs_escalation: bool = Field(
        default=False,
        description="Flag indicating if query requires human support escalation",
        examples=[False],
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Reason for human escalation if triggered ('NO_MATCHING_DOCUMENTS', 'LOW_CONFIDENCE_SCORE', 'INSUFFICIENT_CONTEXT', 'HUMAN_AGENT_REQUESTED')",
        examples=[None],
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of cited vector chunk point IDs",
        examples=[["c8a1b2d3-4e5f-6a7b-8c9d-0e1f2a3b4c5d"]],
    )


class IngestResponse(BaseModel):
    """Response payload for POST /ingest endpoint."""
    status: str = Field(default="success", description="Status string", examples=["success"])
    tenant_id: str = Field(..., description="Tenant identifier", examples=["tenant_acme"])
    file_name: str = Field(..., description="Name of the processed PDF", examples=["return_policy.pdf"])
    chunks_processed: int = Field(..., description="Total semantic chunks created and indexed", examples=[12])
    message: str = Field(..., description="Status message", examples=["Document successfully ingested and indexed."])


class DocumentItem(BaseModel):
    """Item representing a registered document for a tenant."""
    file_name: str = Field(..., description="Name of the document", examples=["return_policy.pdf"])
    total_chunks: int = Field(..., description="Total vector chunks in database", examples=[12])


class DocumentListResponse(BaseModel):
    """Response payload for GET /documents endpoint."""
    status: str = Field(default="success", description="Status string", examples=["success"])
    tenant_id: str = Field(..., description="Tenant identifier", examples=["tenant_acme"])
    total_documents: int = Field(..., description="Count of distinct documents", examples=[2])
    documents: List[DocumentItem] = Field(
        default_factory=list,
        description="List of registered tenant documents and chunk counts",
    )


class DeleteDocumentResponse(BaseModel):
    """Response payload for DELETE /documents endpoint."""
    status: str = Field(default="success", description="Status string", examples=["success"])
    tenant_id: str = Field(..., description="Tenant identifier", examples=["tenant_acme"])
    message: str = Field(..., description="Deletion confirmation message", examples=["Successfully deleted document 'return_policy.pdf'."])


class ModelListResponse(BaseModel):
    """Response payload for GET /models endpoint."""
    status: str = Field(default="success", description="Status string", examples=["success"])
    provider: str = Field(..., description="LLM provider name", examples=["gemini"])
    available_models: List[str] = Field(
        default_factory=list,
        description="List of available active model IDs for the provided API key",
        examples=[["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]],
    )
