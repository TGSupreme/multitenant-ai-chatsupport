from langchain_core.messages import AIMessage, HumanMessage

from core.constants import HEADER_JINA_API_KEY, HEADER_LLM_API_KEY, HEADER_LLM_PROVIDER
from core.errors import MissingHeaderException
from models.request import ChatRequest
from models.response import ChatResponse
from services.jina_service import jina_service
from services.llm_service import get_llm
from services.prompt_builder import PromptBuilder
from services.qdrant_service import qdrant_service


class RAGService:
    """Orchestrates stateless RAG pipeline: Query Vectorization -> Tenant Qdrant Search -> Prompt Assembly -> LangChain LLM Execution."""

    async def process_chat_query(
        self,
        request: ChatRequest,
        jina_api_key: str,
        llm_api_key: str,
        llm_provider: str,
    ) -> ChatResponse:
        """Executes full stateless RAG query lifecycle."""
        # 1. Validate mandatory HTTP header credentials
        if not jina_api_key or not jina_api_key.strip():
            raise MissingHeaderException(HEADER_JINA_API_KEY)
        if not llm_api_key or not llm_api_key.strip():
            raise MissingHeaderException(HEADER_LLM_API_KEY)
        if not llm_provider or not llm_provider.strip():
            raise MissingHeaderException(HEADER_LLM_PROVIDER)

        # 2. Vectorize user query via Jina Embeddings API
        query_vector = await jina_service.generate_query_embedding(
            query=request.query,
            jina_api_key=jina_api_key.strip(),
        )

        # 3. Retrieve relevant context chunks strictly filtered by tenant_id
        await qdrant_service.ensure_collection_and_index()
        sources = await qdrant_service.search_tenant_vectors(
            tenant_id=request.tenant_id.strip(),
            query_vector=query_vector,
            top_k=request.top_k,
        )

        # 4. Build prompt incorporating grounding rules, optional tenant instructions, and retrieved context
        assembled_prompt = PromptBuilder.build_rag_prompt(
            query=request.query,
            sources=sources,
            system_prompt=request.system_prompt,
        )

        # 5. Dynamically instantiate requested LangChain LLM provider (gemini, openai, groq)
        llm = get_llm(
            provider=llm_provider.strip().lower(),
            api_key=llm_api_key.strip(),
            model_name=request.model_name,
        )

        # 6. Build message payload including prior conversation history
        messages = []
        if request.conversation_history:
            for msg in request.conversation_history:
                if msg.role.lower() in ("assistant", "model"):
                    messages.append(AIMessage(content=msg.content))
                else:
                    messages.append(HumanMessage(content=msg.content))

        messages.append(HumanMessage(content=assembled_prompt))

        # 7. Generate grounded answer via LangChain
        response = await llm.ainvoke(messages)
        answer_text = str(response.content).strip() if response and response.content else ""

        model_used = request.model_name or getattr(llm, "model_name", getattr(llm, "model", "default"))

        return ChatResponse(
            status="success",
            tenant_id=request.tenant_id.strip(),
            provider=llm_provider.strip().lower(),
            model_name=str(model_used),
            answer=answer_text,
            sources=sources,
        )


# Singleton instance
rag_service = RAGService()
