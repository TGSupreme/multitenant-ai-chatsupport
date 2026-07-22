# API Documentation

## 📌 Project Title
**Stateless Multi-Tenant AI Chat Support Engine**

**Base URL**: `http://localhost:8000/api/v1`

---

## 🔑 Request Authentication & Headers

This backend is 100% stateless. Vendor API keys and provider selections must be passed dynamically in the HTTP headers of each request:

| Header Name | Type | Description | Required For |
| :--- | :--- | :--- | :--- |
| `X-Jina-Api-Key` | String | API Key for Jina Embeddings API | `/ingest`, `/chat` |
| `X-LLM-Api-Key` | String | API Key for the chosen LLM Provider | `/chat` |
| `X-LLM-Provider` | String | LLM Provider name: `gemini` \| `openai` \| `groq` | `/chat` |

---

## 1. Ingest PDF Document

Uploads a binary PDF document, splits it into semantic chunks in RAM, vectorizes chunks using Jina Embeddings API, and stores them in Qdrant indexed by `tenant_id`.

* **Endpoint**: `POST /api/v1/ingest`
* **Content-Type**: `multipart/form-data`

### Request Headers
```http
X-Jina-Api-Key: jina_xxxxxxxxxxxxxxxxxxxxxxxx
```

### Form Parameters
* `file` (File, required): PDF document binary.
* `tenant_id` (String, required): Unique identifier for the tenant (e.g., `tenant_acme_001`).
* `file_name` (String, optional): Custom filename (defaults to uploaded PDF file name).

### Sample cURL Command
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "X-Jina-Api-Key: your_jina_api_key_here" \
  -F "tenant_id=tenant_acme_001" \
  -F "file=@/path/to/user_guide.pdf"
```

### Success Response (`200 OK`)
```json
{
  "status": "success",
  "tenant_id": "tenant_acme_001",
  "file_name": "user_guide.pdf",
  "chunks_processed": 14,
  "message": "Document successfully ingested and indexed."
}
```

---

## 2. List Tenant Documents

Retrieves a list of all documents and their chunk counts stored in Qdrant for a specific tenant.

* **Endpoint**: `GET /api/v1/documents`
* **Content-Type**: `application/json`

### Query Parameters
* `tenant_id` (String, required): Tenant ID to filter by.

### Sample cURL Command
```bash
curl -X GET "http://localhost:8000/api/v1/documents?tenant_id=tenant_acme_001"
```

### Success Response (`200 OK`)
```json
{
  "tenant_id": "tenant_acme_001",
  "total_documents": 2,
  "documents": [
    {
      "file_name": "user_guide.pdf",
      "total_chunks": 14
    },
    {
      "file_name": "faq.pdf",
      "total_chunks": 6
    }
  ]
}
```

---

## 3. Delete Tenant Document(s)

Deletes vectors from Qdrant associated with a specific file name for a tenant, or wipes all documents under that tenant ID.

* **Endpoint**: `DELETE /api/v1/documents`
* **Content-Type**: `application/json`

### Query Parameters
* `tenant_id` (String, required): Tenant ID.
* `file_name` (String, optional): Target file name to delete.
* `delete_all` (Boolean, optional, default: `false`): If `true`, deletes all documents for the specified tenant.

### Sample cURL Command (Delete Single File)
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents?tenant_id=tenant_acme_001&file_name=user_guide.pdf"
```

### Sample cURL Command (Wipe All Tenant Data)
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents?tenant_id=tenant_acme_001&delete_all=true"
```

### Success Response (`200 OK`)
```json
{
  "status": "success",
  "tenant_id": "tenant_acme_001",
  "message": "Successfully deleted document 'user_guide.pdf'."
}
```

---

## 4. Chat Support & Query (RAG)

Performs context retrieval from Qdrant for a given `tenant_id`, builds a grounded dual prompt, and queries the requested LLM vendor (`gemini`, `openai`, or `groq`).

* **Endpoint**: `POST /api/v1/chat`
* **Content-Type**: `application/json`

### Request Headers
```http
X-Jina-Api-Key: jina_xxxxxxxxxxxxxxxxxxxxxxxx
X-LLM-Api-Key: llm_xxxxxxxxxxxxxxxxxxxxxxxx
X-LLM-Provider: groq
```

### Request Body
```json
{
  "tenant_id": "tenant_acme_001",
  "query": "How do I reset my password?",
  "system_prompt": "Answer warmly and sign off as 'ACME Support Team'.",
  "model_name": "llama-3.3-70b-versatile",
  "top_k": 4,
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello!"
    },
    {
      "role": "assistant",
      "content": "Hi there! How can I assist you with ACME products today?"
    }
  ]
}
```

### Provider-Specific cURL Examples

#### A. Groq Provider Example
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-Jina-Api-Key: your_jina_key" \
  -H "X-LLM-Api-Key: gsk_your_groq_key" \
  -H "X-LLM-Provider: groq" \
  -d '{
    "tenant_id": "tenant_acme_001",
    "query": "How do I reset my password?",
    "model_name": "llama-3.3-70b-versatile"
  }'
```

#### B. Gemini Provider Example
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-Jina-Api-Key: your_jina_key" \
  -H "X-LLM-Api-Key: AIzaSy_your_gemini_key" \
  -H "X-LLM-Provider: gemini" \
  -d '{
    "tenant_id": "tenant_acme_001",
    "query": "What are your support hours?",
    "model_name": "gemini-2.5-flash"
  }'
```

#### C. OpenAI Provider Example
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-Jina-Api-Key: your_jina_key" \
  -H "X-LLM-Api-Key: sk-proj-your_openai_key" \
  -H "X-LLM-Provider: openai" \
  -d '{
    "tenant_id": "tenant_acme_001",
    "query": "What is the warranty period?",
    "model_name": "gpt-4o-mini"
  }'
```

### Success Response (`200 OK`)
```json
{
  "response": "To reset your password, navigate to the Account Settings tab on your dashboard and click 'Security'. Best regards, ACME Support Team.",
  "sources": [
    {
      "file_name": "user_guide.pdf",
      "page_number": 2,
      "text": "Password Reset Instructions: Navigate to Account Settings...",
      "score": 0.89
    }
  ]
}
```

---

## 5. HTTP Error Status Codes

| Code | Error Name | Cause & Description |
| :--- | :--- | :--- |
| `400` | Bad Request | Missing required parameters, empty PDF file, or unsupported vendor choice. |
| `401` | Unauthorized | Missing or invalid header keys (`X-Jina-Api-Key` or `X-LLM-Api-Key`). |
| `404` | Not Found | Tenant ID or specified document file name not found in vector database. |
| `429` | Too Many Requests | Upstream vendor API rate limit exceeded. |
| `500` | Internal Server Error | Server runtime exception or Qdrant connection issue. |
| `502` | Bad Gateway | Upstream failure when calling Jina API or LLM provider. |
