# Stateless Multi-Tenant AI Chat Support Engine

An enterprise-grade, stateless RAG (Retrieval-Augmented Generation) backend engine supporting multi-tenancy, dynamic LLM provider selection (Google Gemini, OpenAI, Groq), Jina Embeddings, and Qdrant Cloud Vector Database.

---

## 🚀 Key Features

- **Stateless Zero-Persistence Security**: No tenant API keys, LLM keys, or document bytes are persisted locally. All credentials are passed dynamically per-request via HTTP headers (`X-Jina-Api-Key`, `X-LLM-Api-Key`, `X-LLM-Provider`).
- **Multi-Tenant Vector Isolation**: A single Qdrant collection isolated by hardware-accelerated `tenant_id` and `file_name` payload indexes.
- **Dynamic LLM Factory**: Dynamically instantiates LangChain models (`gemini`, `openai`, `groq`) per HTTP call.
- **Human Support Escalation Detection**: Automatically sets `needs_escalation: true` and `escalation_reason` (`INSUFFICIENT_CONTEXT`, `HUMAN_AGENT_REQUESTED`, `NO_MATCHING_DOCUMENTS`) to trigger live agent handoffs.
- **Model Discovery API (`GET /models`)**: Query active available model IDs for any provider API key.
- **Interactive Swagger UI**: Explore and test API endpoints at `/docs` with global `Authorize` header persistence.

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

## 💻 How to Run the Server

You can run this application using either **Option A (Standard Python)** or **Option B (Docker Containers)**:

### 🐍 Option A: Running Locally with Python (Recommended for Low-Spec Machines)

#### 1. Setup Environment File
```bash
cp app/.example.env app/.env
```
Open `app/.env` and paste your Qdrant Cloud credentials:
```env
QDRANT_URL="https://your-cluster.cloud.qdrant.io:6333"
QDRANT_API_KEY="your-qdrant-api-key"
```

#### 2. Create Virtual Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

#### 3. Start Server
```bash
python3 app/main.py
```
- **Server URL**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs`

---

### 🐳 Option B: Running with Docker Containers

#### 1. Setup Environment File
```bash
cp app/.example.env app/.env
```
Fill in your `QDRANT_URL` and `QDRANT_API_KEY` in `app/.env`.

#### 2. Start Service via Docker Compose
```bash
docker compose up --build
```
- **Server URL**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs`

To stop the Docker container:
```bash
docker compose down
```

---

## 🧪 Testing the API via Swagger UI (`http://localhost:8000/docs`)

1. Open `http://localhost:8000/docs` in your browser.
2. Click the green **Authorize 🔓** button at the top right.
3. Enter your test headers:
   - `X-Jina-Api-Key`: *(your Jina API Key)*
   - `X-LLM-Api-Key`: *(your Gemini / OpenAI / Groq API Key)*
   - `X-LLM-Provider`: `gemini` *(or `openai` / `groq`)*
4. Click **Authorize** to save headers globally for all endpoint calls!
