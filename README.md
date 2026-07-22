# Stateless Multi-Tenant AI Chat Support Engine

An enterprise-grade, stateless RAG (Retrieval-Augmented Generation) backend service supporting multi-tenancy, dynamic LLM provider selection (Google Gemini, OpenAI, Groq), Jina Embeddings, and Qdrant Cloud Vector Database.

---

## 🚀 Key Features

- **Stateless Architecture**: No tenant API keys, LLM keys, or document bytes are stored locally. All keys are passed dynamically per-request via HTTP headers (`X-Jina-Api-Key`, `X-LLM-Api-Key`, `X-LLM-Provider`).
- **Multi-Tenant Vector Isolation**: A single Qdrant collection isolated by hardware-accelerated `tenant_id` payload indexes.
- **Dynamic Provider Routing**: Instantiates LangChain models dynamically per-request (`gemini`, `openai`, `groq`).
- **Structured JSON Output & Escalation Flag**: Automatically sets `needs_escalation: true` and `escalation_reason` when context is insufficient or human support is requested.
- **Model Discovery API (`GET /models`)**: Discover active available models for any provider API key.
- **Interactive Swagger UI**: Explore and test API endpoints at `/docs` with global `Authorize` headers.

---

## 🛠️ API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ingest` | Multipart PDF upload, chunking, Jina vectorization, Qdrant indexing |
| `POST` | `/chat` | Stateless RAG query execution with grounding & escalation detection |
| `GET` | `/documents` | List tenant documents and vector chunk counts |
| `DELETE` | `/documents` | Delete specific document or wipe all tenant vectors |
| `GET` | `/models` | Query active available model IDs for a provider API key |
| `GET` | `/health` | Server health check endpoint |

---

## 🐳 Running with Docker

### 1. Clone & Setup Environment
```bash
cp app/.example.env app/.env
```
Fill in your `QDRANT_URL` and `QDRANT_API_KEY` in `app/.env`.

### 2. Start Service Container
```bash
docker compose up --build
```

The API server will start on `http://localhost:8000`. Interactive docs will be available at `http://localhost:8000/docs`.

---

## 🐍 Running Locally (Without Docker)

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r app/requirements.txt
```

### 3. Run Server
```bash
python3 app/main.py
```
