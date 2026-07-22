from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import uvicorn

from api.v1.chat import router as chat_router
from api.v1.documents import router as documents_router
from api.v1.ingest import router as ingest_router
from api.v1.models import router as models_router
from core.config import settings
from core.constants import HEADER_JINA_API_KEY, HEADER_LLM_API_KEY, HEADER_LLM_PROVIDER
from core.errors import register_exception_handlers

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom & Global Exception Handlers
register_exception_handlers(app)

# Mount API Routers Directly
app.include_router(ingest_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(models_router)


def custom_openapi() -> Dict[str, Any]:
    """Generates custom OpenAPI schema adding global Authorize header schemes to Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Stateless Multi-Tenant AI Chat Support Engine API Specification",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        HEADER_JINA_API_KEY: {
            "type": "apiKey",
            "in": "header",
            "name": HEADER_JINA_API_KEY,
            "description": "API Key for Jina Embeddings API",
        },
        HEADER_LLM_API_KEY: {
            "type": "apiKey",
            "in": "header",
            "name": HEADER_LLM_API_KEY,
            "description": "API Key for chosen LLM Vendor (Gemini, OpenAI, or Groq)",
        },
        HEADER_LLM_PROVIDER: {
            "type": "apiKey",
            "in": "header",
            "name": HEADER_LLM_PROVIDER,
            "description": "Selected LLM Vendor Provider ('gemini' | 'openai' | 'groq')",
        },
    }

    # Apply global security headers so Swagger UI includes them across all endpoints
    openapi_schema["security"] = [
        {
            HEADER_JINA_API_KEY: [],
            HEADER_LLM_API_KEY: [],
            HEADER_LLM_PROVIDER: [],
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", tags=["Health Check"])
async def root():
    """Root health check endpoint."""
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
