from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a single message turn in conversation history."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'", examples=["user"])
    content: str = Field(..., description="Message text content", examples=["What is the return policy duration?"])


class ChatRequest(BaseModel):
    """Request payload for POST /chat endpoint."""
    tenant_id: str = Field(..., description="Unique identifier for the tenant", examples=["tenant_acme"])
    query: str = Field(..., description="User query or prompt", examples=["What is the return policy duration?"])
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional tenant persona or additional instructions appended to base grounding prompt",
        examples=["Answer in a warm tone and sign off as 'ACME Support Team'."],
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Optional provider-specific model override (e.g. 'gemini-1.5-flash', 'gpt-4o-mini', 'llama-3.3-70b-versatile')",
        examples=["gemini-1.5-flash"],
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Number of vector context chunks to retrieve from Qdrant",
        examples=[4],
    )
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation context messages",
    )
 