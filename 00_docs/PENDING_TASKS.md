# Pending Tasks & Roadmap

## 📌 Project: Stateless Multi-Tenant AI Chat Support Engine

---

### Phase 1: Project Setup & Core Configuration
- [ ] Initialize Python virtual environment & dependencies (`FastAPI`, `qdrant-client`, `pypdf`, `httpx`, `pydantic`).
- [ ] Create core configuration module (`app/core/config.py`) and `.example.env`.
- [ ] Implement custom exception handlers and error response models (`app/core/errors.py`).

### Phase 2: Vector DB & Embedding Infrastructure
- [ ] Implement Qdrant Client Wrapper (`app/services/qdrant_service.py`) with automatic `tenant_id` payload index creation on startup.
- [ ] Implement Jina Embeddings Client (`app/services/jina_service.py`) with per-request API key authentication.

### Phase 3: Dynamic LLM Provider Adapters
- [ ] Define abstract base LLM adapter interface (`app/services/llm/base.py`).
- [ ] Implement Google Gemini Provider Adapter (`app/services/llm/gemini.py`).
- [ ] Implement OpenAI Provider Adapter (`app/services/llm/openai.py`).
- [ ] Implement Groq Provider Adapter (`app/services/llm/groq.py`).
- [ ] Implement LLM Factory (`app/services/llm/factory.py`) to instantiate adapters dynamically based on `X-LLM-Provider` header.

### Phase 4: Document Parsing & Ingestion Pipeline
- [ ] Implement PDF parser & semantic text chunking utility (`app/services/ingestion.py`) using in-memory `io.BytesIO`.
- [ ] Implement auto-update lifecycle (purge old chunks matching `(tenant_id, file_name)` prior to upserting).
- [ ] Build `POST /api/v1/ingest` API endpoint.

### Phase 5: RAG Query & Chat System
- [ ] Implement RAG retriever logic with Qdrant tenant payload filtering (`tenant_id`).
- [ ] Implement system prompt builder (merging default grounding rules with client dynamic system prompt).
- [ ] Build `POST /api/v1/chat` API endpoint.

### Phase 6: Document Management CRUD
- [ ] Implement `GET /api/v1/documents` endpoint (listing distinct files & chunk counts for a tenant).
- [ ] Implement `DELETE /api/v1/documents` endpoint (deleting specific file or wiping all tenant documents).

### Phase 7: Verification & Testing
- [ ] Create automated API test suite for end-to-end multi-tenant RAG validation.
- [ ] Verify zero local persistence (no temporary files, no stored keys).
