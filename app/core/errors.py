from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized JSON error response model."""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class BaseChatSupportException(Exception):
    """Base exception for the Chat Support application."""
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details


class MissingHeaderException(BaseChatSupportException):
    """Raised when a required request header is missing or empty."""
    def __init__(self, header_name: str):
        super().__init__(
            message=f"Required HTTP header '{header_name}' is missing.",
            error_code="MISSING_HEADER",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidProviderException(BaseChatSupportException):
    """Raised when an unsupported LLM provider is requested."""
    def __init__(self, provider: str, supported_providers: list[str]):
        super().__init__(
            message=f"Unsupported LLM provider '{provider}'. Supported providers are: {', '.join(supported_providers)}.",
            error_code="INVALID_PROVIDER",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class UpstreamProviderException(BaseChatSupportException):
    """Raised when an external API (Jina, OpenAI, Gemini, Groq) returns an error."""
    def __init__(self, provider_name: str, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(
            message=f"Upstream service '{provider_name}' error: {message}",
            error_code="UPSTREAM_PROVIDER_ERROR",
            status_code=status_code,
        )


class VectorStoreException(BaseChatSupportException):
    """Raised when Qdrant database operations fail."""
    def __init__(self, message: str):
        super().__init__(
            message=f"Vector store operation failed: {message}",
            error_code="VECTOR_STORE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class DocumentIngestionException(BaseChatSupportException):
    """Raised when PDF ingestion, parsing, or chunking fails."""
    def __init__(self, message: str):
        super().__init__(
            message=f"Document ingestion error: {message}",
            error_code="INGESTION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers custom and global exception handlers to ensure sanitized JSON error responses."""

    @app.exception_handler(BaseChatSupportException)
    async def chat_support_exception_handler(request: Request, exc: BaseChatSupportException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
            ).model_dump(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Sanitized generic fallback for unhandled exceptions to prevent leaking stack traces or keys
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal error occurred. Please try again later.",
            ).model_dump(exclude_none=True),
        )
