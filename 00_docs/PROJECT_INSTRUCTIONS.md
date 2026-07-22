# Stateless Multi-Tenant AI Chat Support Engine - Project Instructions & Mandates

## 1. Environment & Stateless Configuration Management
* **System Environment Variables:** Server-level configuration (e.g., `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION`, `LOG_LEVEL`) must be managed in `app/core/config.py` and mirrored in `.example.env` with sensible defaults.
* **Pre-Modification Check:** Before modifying configuration logic, always inspect `app/core/config.py` and `.example.env` to understand the configuration state.
* **Zero Persistence Security Mandate:** Tenant API keys (`X-Jina-Api-Key`, `X-LLM-Api-Key`), provider choices, system prompts, and uploaded document bytes must **NEVER** be committed, written to disk, saved to a local database, or logged in application log outputs.

## 2. Documentation Updates & Progress Tracking
* **Documentation Maintenance:** Any architectural changes, API payload modifications, or new features must be reflected across the relevant documentation files in `00_docs/` (`PRD.md`, `ARCHITECTURE.md`, `API_DOCUMENTATION.md`).
* **Pending Tasks:** Maintain `00_docs/PENDING_TASKS.md` as the single "Source of Truth" for development progress. Mark completed tasks as `[x]` and list newly identified tasks promptly.

## 3. Modular Architecture & Service Layer
* **Separation of Concerns:** Adhere strictly to the Service Layer pattern (SRP). FastAPI routers handle request validation and header extraction; service modules manage ingestion and RAG logic; client adapters handle external APIs (Qdrant, Jina, LLM providers).
* **Provider Adapters:** All LLM integrations (Google Gemini, OpenAI, Groq) must implement a unified abstract base interface (`BaseLLMAdapter`).

## 4. Stateless Vector & Ingestion Pipeline Rules
* **In-Memory PDF Ingestion:** PDF files must be parsed completely in RAM (`io.BytesIO`) without creating temporary files on the local filesystem.
* **Tenant Isolation:** Qdrant vectors must always include the `tenant_id` keyword payload field. All vector operations (search, list, delete) must be strictly filtered by `tenant_id`.
* **Auto-Update Lifecycle:** Document re-uploads matching `(tenant_id, file_name)` must automatically purge existing vectors prior to indexing new chunks.

## 5. LLM & Embedding Provider Strategy
* **Provider Agnostic:** The system supports **Google Gemini**, **OpenAI**, and **Groq**. Provider selection (`X-LLM-Provider`) and credentials (`X-LLM-Api-Key`) are passed dynamically per-request.
* **Embeddings Standard:** **Jina Embeddings API** is used for vectorizing text chunks via the `X-Jina-Api-Key` request header.

## 6. Task Execution & Autonomy
* **Wait for Instruction:** Do not jump ahead to implement new features or endpoints immediately after completing a step.
* **Explicit Approval:** Always wait for the user to explicitly say "proceed", "next task", or provide a specific directive before initiating new work.

## 7. Backend-First Scope
* **Focus:** All production efforts must focus exclusively on the high-performance FastAPI backend engine.
* **Testing Scripts / UIs:** Any frontend test clients or utility scripts are strictly for internal testing and must not be treated as production deliverables.
