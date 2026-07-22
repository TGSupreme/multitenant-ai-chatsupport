# Pending Tasks & Roadmap

## 📌 Project: Stateless Multi-Tenant AI Chat Support Engine

---

### Phase 1: Project Setup & Core Configuration
- [x] Initialize Python virtual environment (`.venv`) & dependencies (`FastAPI`, `qdrant-client`, `pypdf`, `httpx`, `pydantic`).
- [x] Create core configuration module (`app/core/config.py`) and `.example.env`.
- [x] Implement custom exception handlers and error response models (`app/core/errors.py`).
- [x] Create application constants module (`app/core/constants.py`).
- [x] Initialize FastAPI application entry point & server setup (`app/main.py`).

### Phase 2: Request & Response Data Models
- [x] Implement Pydantic request models (`app/models/request.py`).
- [x] Implement Pydantic response models (`app/models/response.py`).

### Phase 3: Vector DB & Embedding Infrastructure
- [x] Implement Qdrant Client Wrapper (`app/services/qdrant_service.py`) with automatic `tenant_id` payload index creation on startup.
- [x] Implement Jina Embeddings Client (`app/services/jina_service.py`) with per-request API key authentication.

### Phase 4: Dynamic LLM Provider Selection
- [x] Implement unified LangChain `get_llm()` provider factory function (`app/services/llm_service.py`) supporting Google Gemini, OpenAI, and Groq.

### Phase 5: Document Parsing & Ingestion Pipeline
- [x] Implement PDF parser & semantic text chunking utility (`app/services/ingestion.py`) using in-memory `io.BytesIO` and LangChain's `RecursiveCharacterTextSplitter`.
- [x] Implement auto-update lifecycle (purge old chunks matching `(tenant_id, file_name)` prior to upserting).
- [x] Build `POST /ingest` API endpoint (`app/api/v1/ingest.py`).

### Phase 6: RAG Query & Chat System
- [ ] Implement RAG retriever logic with Qdrant tenant payload filtering (`tenant_id`).
- [ ] Implement system prompt builder (merging default grounding rules with client dynamic system prompt).
- [ ] Build `POST /chat` API endpoint (`app/api/v1/chat.py`).

### Phase 7: Document Management CRUD
- [ ] Implement `GET /documents` endpoint (listing distinct files & chunk counts for a tenant).
- [ ] Implement `DELETE /documents` endpoint (deleting specific file or wiping all tenant documents).

### Phase 8: Verification & Testing
- [ ] Create automated API test suite for end-to-end multi-tenant RAG validation.
- [ ] Verify zero local persistence (no temporary files, no stored keys).
