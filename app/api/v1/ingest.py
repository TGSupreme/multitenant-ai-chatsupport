from typing import Optional
from fastapi import APIRouter, File, Form, Header, UploadFile

from core.constants import HEADER_JINA_API_KEY
from core.errors import DocumentIngestionException, MissingHeaderException
from models.response import IngestResponse
from services.ingestion import ingestion_service

router = APIRouter(tags=["Document Ingestion"])


@router.post("/ingest", response_model=IngestResponse, summary="Ingest PDF document into tenant vector store")
async def ingest_document(
    file: UploadFile = File(..., description="PDF file to ingest"),
    tenant_id: str = Form(..., description="Tenant identifier"),
    file_name: Optional[str] = Form(None, description="Optional filename override"),
    x_jina_api_key: Optional[str] = Header(None, alias=HEADER_JINA_API_KEY, description="Jina AI API key for embeddings"),
) -> IngestResponse:
    """Parses uploaded PDF in RAM, creates semantic chunks via LangChain, vectorizes via Jina, and upserts to Qdrant."""
    if not x_jina_api_key or not x_jina_api_key.strip():
        raise MissingHeaderException(HEADER_JINA_API_KEY)

    if not file.filename.lower().endswith(".pdf"):
        raise DocumentIngestionException("Only PDF files (.pdf) are supported for document ingestion.")

    pdf_bytes = await file.read()
    target_filename = file_name.strip() if file_name and file_name.strip() else file.filename

    return await ingestion_service.ingest_document(
        pdf_bytes=pdf_bytes,
        tenant_id=tenant_id.strip(),
        file_name=target_filename,
        jina_api_key=x_jina_api_key.strip(),
    )
