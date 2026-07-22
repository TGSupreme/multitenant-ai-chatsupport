import io
from typing import Any, Dict, List
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from core.errors import DocumentIngestionException
from models.response import IngestResponse
from services.jina_service import jina_service
from services.qdrant_service import qdrant_service


class IngestionService:
    """In-memory PDF document parser, LangChain text splitter, and vector ingestion pipeline."""

    def __init__(self) -> None:
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Extracts text page by page from PDF raw bytes in RAM using PyPDF."""
        if not pdf_bytes:
            raise DocumentIngestionException("Received empty PDF document bytes.")

        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            pages_data: List[Dict[str, Any]] = []

            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_data.append(
                        {
                            "page_number": page_idx + 1,
                            "text": text.strip(),
                        }
                    )

            if not pages_data:
                raise DocumentIngestionException("No readable text content found in uploaded PDF.")

            return pages_data
        except DocumentIngestionException:
            raise
        except Exception as e:
            raise DocumentIngestionException(f"Failed to parse PDF document: {str(e)}")

    def create_chunks(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Splits page text into semantic chunks using LangChain's RecursiveCharacterTextSplitter."""
        chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]

            raw_chunks = self.text_splitter.split_text(page_text)
            for chunk_text in raw_chunks:
                if chunk_text and chunk_text.strip():
                    chunks.append(
                        {
                            "chunk_index": global_chunk_idx,
                            "page_number": page_num,
                            "text": chunk_text.strip(),
                        }
                    )
                    global_chunk_idx += 1

        if not chunks:
            raise DocumentIngestionException("Failed to generate text chunks from document.")

        return chunks

    async def ingest_document(
        self,
        pdf_bytes: bytes,
        tenant_id: str,
        file_name: str,
        jina_api_key: str,
    ) -> IngestResponse:
        """Executes full stateless ingestion pipeline: RAM PDF parse -> LangChain chunk -> Jina vectorization -> Qdrant upsert."""
        if not tenant_id or not tenant_id.strip():
            raise DocumentIngestionException("tenant_id must be provided for ingestion.")

        if not file_name or not file_name.strip():
            file_name = "document.pdf"

        # 1. Parse PDF in RAM
        pages_data = self.extract_text_from_pdf_bytes(pdf_bytes)

        # 2. Chunk text using LangChain RecursiveCharacterTextSplitter
        chunks = self.create_chunks(pages_data)

        # 3. Vectorize text chunks via Jina Embeddings API
        chunk_texts = [c["text"] for c in chunks]
        embeddings = await jina_service.generate_embeddings(
            texts=chunk_texts,
            jina_api_key=jina_api_key,
            task="retrieval.passage",
        )

        # 4. Upsert vectors & metadata into Qdrant under tenant_id
        await qdrant_service.ensure_collection_and_index()
        count = await qdrant_service.upsert_chunks(
            tenant_id=tenant_id.strip(),
            file_name=file_name.strip(),
            chunks=chunks,
            embeddings=embeddings,
        )

        return IngestResponse(
            status="success",
            tenant_id=tenant_id.strip(),
            file_name=file_name.strip(),
            chunks_processed=count,
            message=f"Successfully ingested '{file_name.strip()}' with {count} indexed vector chunks.",
        )


# Singleton instance
ingestion_service = IngestionService()
