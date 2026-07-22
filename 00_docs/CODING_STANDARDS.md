# Stateless Multi-Tenant AI Chat Support Engine - Coding Standards & Architecture

## 1. Core Principles

* **Modular Monolith:** Organize code into clean, decoupled modules (`api/`, `services/`, `models/`, `core/`) within a single FastAPI repository.
* **Single Responsibility Principle (SRP):** Every module, class, and function must have a single clearly defined responsibility.
* **Stateless & Zero Persistence:** API keys (`X-Jina-Api-Key`, `X-LLM-Api-Key`), tenant files, and LLM credentials must **never** be saved to local disk, local databases, or written to logs.
* **Don't Over-Engineer:** Prefer clarity, maintainability, and standard library/FastAPI primitives over unnecessary abstractions.
* **Explicit over Implicit:** Use strict Python type hinting (`typing`, Pydantic models) and explicit configurations.
* **Asynchronous First:** Use `async/await` for all non-blocking I/O operations (HTTP requests via `httpx`, Qdrant async queries).

---

## 2. Folder Structure (FastAPI Service)

The `app/` directory follows a service-oriented layer architecture:

```text
app/
├── main.py                # App entry point & FastAPI middleware configuration
├── .example.env           # Template for server-level environment variables
├── requirements.txt       # Project dependencies
├── api/                   # API Route Handlers (Controllers)
│   └── v1/                # Versioned API endpoints
│       ├── chat.py        # POST /chat endpoint (Stateless RAG generation)
│       ├── ingest.py      # POST /ingest endpoint (In-memory PDF parsing & indexing)
│       └── documents.py   # GET & DELETE /documents endpoints
├── core/                  # Global Configuration & Security
│   ├── config.py          # Pydantic Settings & server environment vars
│   ├── constants.py       # System constants & default grounding prompt
│   └── errors.py          # Custom HTTP exceptions & global error handlers
├── services/              # Business Logic Layer (The "Brain")
│   ├── qdrant_service.py  # Qdrant client & tenant-filtered vector store logic
│   ├── jina_service.py    # Jina Embeddings API client wrapper
│   ├── ingestion.py       # In-memory PDF parser (io.BytesIO) & semantic chunking
│   ├── rag_service.py     # RAG retriever & context aggregation
│   ├── prompt_builder.py  # System prompt composition & grounding rules
│   └── llm/               # Multi-provider LLM Adapter layer
│       ├── base.py        # BaseLLMAdapter abstract interface
│       ├── gemini.py      # Google Gemini provider adapter
│       ├── openai.py      # OpenAI provider adapter
│       ├── groq.py        # Groq provider adapter
│       └── factory.py     # LLM Provider Factory (X-LLM-Provider routing)
├── models/                # Data Schemas (Pydantic)
│   ├── request.py         # API Request models & header schemas
│   └── response.py        # API Response & Metadata models
├── utils/                 # Shared Utilities
│   └── logger.py          # Sanitized structured logging (scrubs API keys)
└── tests/                 # Test Suite
    ├── unit/              # Service & LLM adapter unit tests
    └── integration/       # API endpoint integration tests
```

---

## 3. Implementation Guidelines

### 3.1 Naming Conventions
* **Files & Modules:** `snake_case.py`
* **Classes:** `PascalCase`
* **Functions & Variables:** `snake_case`
* **Constants:** `UPPER_SNAKE_CASE`

### 3.2 Service Layer & SRP
* **API Routers (`api/v1/`):** Responsible only for parsing request headers/bodies, delegating to services, and formatting HTTP responses.
* **Services (`services/`):** Contain all core business logic (PDF chunking, Qdrant payload search, prompt assembly, LLM dispatch).
* **Class-Based Services:** Services should be class-based to enable clean dependency injection and straightforward unit testing/mocking.

### 3.3 Error Handling & Key Security
* Use custom HTTP exceptions defined in `app/core/errors.py`.
* Implement a global FastAPI exception handler to sanitize error messages. Stack traces and error responses must **NEVER** expose raw API keys or tenant secret payloads.
* Return informative HTTP error codes:
  * `400 Bad Request`: Missing mandatory headers (`X-Jina-Api-Key`, `X-LLM-Api-Key`, `X-LLM-Provider`) or invalid payloads.
  * `401 Unauthorized` / `429 Too Many Requests`: Upstream provider authentication or rate limit errors.
  * `500 Internal Server Error`: Sanitized backend failures.

### 3.4 Multi-Provider LLM Architecture
* All LLM adapters must inherit from `BaseLLMAdapter` in `app/services/llm/base.py` and implement an `async generate_response()` method.
* The `LLMFactory` instantiates the appropriate adapter (`gemini`, `openai`, `groq`) on a per-request basis using the `X-LLM-Provider` and `X-LLM-Api-Key` HTTP headers.

### 3.5 RAG Specifics & Vector Strategy
* **Embeddings:** Vector generation is handled via the Jina Embeddings API using `X-Jina-Api-Key`.
* **Vector Isolation:** All Qdrant vector operations must enforce a `tenant_id` Keyword Payload filter.
* **Auto-Purge on Ingest:** Document re-uploads with matching `(tenant_id, file_name)` must automatically purge matching Qdrant points before inserting new chunks.
* **Source Citations:** RAG responses must return structured source citations containing `file_name`, `chunk_index`, `page_number`, and retrieved `text` snippet.

### 3.6 Type Safety & Pydantic Validation
* Use Pydantic models for all API request bodies, query parameters, headers, and responses.
* Always include explicit return type hints (`def func(...) -> ReturnType:`) across all functions and methods.

### 3.7 Prompt Engineering & Strict Grounding
* **Centralization:** All prompt formatting must reside in `app/services/prompt_builder.py`.
* **Default Base Grounding Prompt:** System prompts must include a strict default base prompt enforcing context grounding ("Answer based strictly on the provided context. If the answer cannot be found in the context, state that you do not have sufficient information.").
* **Dynamic Append:** Client-provided `system_prompt` strings in request payloads are appended below the base prompt as secondary persona rules.
