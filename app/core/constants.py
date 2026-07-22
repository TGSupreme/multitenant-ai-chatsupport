"""System-wide static constants for the Stateless Multi-Tenant AI Chat Support Engine."""

# Supported LLM Providers
PROVIDER_GEMINI = "gemini"
PROVIDER_OPENAI = "openai"
PROVIDER_GROQ = "groq"

SUPPORTED_LLM_PROVIDERS = (
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    PROVIDER_GROQ,
)

# Custom HTTP Header Names
HEADER_JINA_API_KEY = "X-Jina-Api-Key"
HEADER_LLM_API_KEY = "X-LLM-Api-Key"
HEADER_LLM_PROVIDER = "X-LLM-Provider"

# Document Parsing & Chunking Defaults
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100

# RAG Search Defaults
DEFAULT_TOP_K = 4

# Strict Anti-Hallucination Base System Prompt
DEFAULT_BASE_SYSTEM_PROMPT = (
    "You are a helpful, accurate AI Chat Support Assistant.\n"
    "Your primary goal is to answer customer questions strictly based on the provided context documentation below.\n\n"
    "STRICT GROUNDING RULES:\n"
    "1. Answer ONLY using the facts directly mentioned in the context.\n"
    "2. If the context does not contain sufficient information to answer the question, state clearly: "
    "\"I do not have sufficient information in my knowledge base to answer this question.\"\n"
    "3. Do NOT make assumptions, extrapolate, or invent information not supported by the context.\n"
    "4. Maintain a professional and helpful tone at all times."
)
