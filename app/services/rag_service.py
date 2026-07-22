import json
import re
from typing import Any, Dict, List, Tuple
from langchain_core.messages import AIMessage, HumanMessage

from core.constants import (
    DEFAULT_SIMILARITY_THRESHOLD,
    ESCALATION_HUMAN_REQUESTED,
    ESCALATION_INSUFFICIENT_CONTEXT,
    ESCALATION_LOW_CONFIDENCE,
    ESCALATION_NO_MATCHING_DOCS,
    HEADER_JINA_API_KEY,
    HEADER_LLM_API_KEY,
    HEADER_LLM_PROVIDER,
    HUMAN_INTENT_KEYWORDS,
    STANDARD_FALLBACK_ANSWER,
)
from core.errors import MissingHeaderException
from models.request import ChatRequest
from models.response import ChatResponse
from services.jina_service import jina_service
from services.llm_service import get_llm
from services.prompt_builder import PromptBuilder
from services.qdrant_service import qdrant_service


class RAGService:
    """Orchestrates stateless RAG pipeline: Early-Exit Guardrail -> Vector Search -> Prompt Assembly -> LLM Execution -> JSON Parser."""

    def _check_human_intent(self, query: str) -> bool:
        """Checks if the user query explicitly requests a human agent/representative."""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in HUMAN_INTENT_KEYWORDS)

    def _parse_llm_json_response(self, raw_text: str) -> Tuple[str, bool, str | None]:
        """Safely parses JSON output from LLM, extracting answer, needs_escalation, and escalation_reason."""
        if not raw_text or not raw_text.strip():
            return STANDARD_FALLBACK_ANSWER, True, ESCALATION_INSUFFICIENT_CONTEXT

        # 1. Attempt direct JSON load
        try:
            data = json.loads(raw_text.strip())
            if isinstance(data, dict):
                answer = data.get("answer", "").strip() or STANDARD_FALLBACK_ANSWER
                needs_esc = bool(data.get("needs_escalation", False))
                esc_reason = data.get("escalation_reason")
                if needs_esc and not esc_reason:
                    esc_reason = ESCALATION_INSUFFICIENT_CONTEXT
                return answer, needs_esc, esc_reason
        except Exception:
            pass

        # 2. Regex fallback to extract JSON object inside ```json ... ``` fences or raw text
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    answer = data.get("answer", "").strip() or STANDARD_FALLBACK_ANSWER
                    needs_esc = bool(data.get("needs_escalation", False))
                    esc_reason = data.get("escalation_reason")
                    if needs_esc and not esc_reason:
                        esc_reason = ESCALATION_INSUFFICIENT_CONTEXT
                    return answer, needs_esc, esc_reason
            except Exception:
                pass

        # 3. Clean fallback if LLM returned plain text despite instructions
        clean_text = raw_text.strip()
        is_fallback = STANDARD_FALLBACK_ANSWER.lower() in clean_text.lower() or "not have sufficient information" in clean_text.lower()
        return (
            clean_text,
            is_fallback,
            ESCALATION_INSUFFICIENT_CONTEXT if is_fallback else None,
        )

    async def process_chat_query(
        self,
        request: ChatRequest,
        jina_api_key: str,
        llm_api_key: str,
        llm_provider: str,
    ) -> ChatResponse:
        """Executes full stateless RAG query lifecycle with Early-Exit Guardrail & Structured JSON Parsing."""
        # 1. Validate mandatory HTTP header credentials
        if not jina_api_key or not jina_api_key.strip():
            raise MissingHeaderException(HEADER_JINA_API_KEY)
        if not llm_api_key or not llm_api_key.strip():
            raise MissingHeaderException(HEADER_LLM_API_KEY)
        if not llm_provider or not llm_provider.strip():
            raise MissingHeaderException(HEADER_LLM_PROVIDER)

        # 2. Pre-Check: Detect explicit human agent request intent
        if self._check_human_intent(request.query):
            llm = get_llm(provider=llm_provider, api_key=llm_api_key, model_name=request.model_name)
            model_used = request.model_name or getattr(llm, "model_name", getattr(llm, "model", "default"))
            return ChatResponse(
                status="success",
                tenant_id=request.tenant_id.strip(),
                provider=llm_provider.strip().lower(),
                model_name=str(model_used),
                answer="I understand you would like to speak to a human representative. I am transferring your request to a customer support agent.",
                needs_escalation=True,
                escalation_reason=ESCALATION_HUMAN_REQUESTED,
                sources=[],
            )

        # 3. Vectorize user query via Jina Embeddings API
        query_vector = await jina_service.generate_query_embedding(
            query=request.query,
            jina_api_key=jina_api_key.strip(),
        )

        # 4. Retrieve relevant context chunks strictly filtered by tenant_id
        await qdrant_service.ensure_collection_and_index()
        sources = await qdrant_service.search_tenant_vectors(
            tenant_id=request.tenant_id.strip(),
            query_vector=query_vector,
            top_k=request.top_k,
        )

        # 5. Build RAG prompt incorporating grounding rules, optional tenant instructions, and retrieved context
        assembled_prompt = PromptBuilder.build_rag_prompt(
            query=request.query,
            sources=sources,
            system_prompt=request.system_prompt,
        )

        # 7. Instantiate requested LangChain LLM provider (gemini, openai, groq)
        llm = get_llm(
            provider=llm_provider.strip().lower(),
            api_key=llm_api_key.strip(),
            model_name=request.model_name,
        )

        # 8. Build message payload including prior conversation history
        messages = []
        if request.conversation_history:
            for msg in request.conversation_history:
                if msg.role.lower() in ("assistant", "model"):
                    messages.append(AIMessage(content=msg.content))
                else:
                    messages.append(HumanMessage(content=msg.content))

        messages.append(HumanMessage(content=assembled_prompt))

        # 9. Generate answer via LangChain
        response = await llm.ainvoke(messages)
        raw_output = str(response.content).strip() if response and response.content else ""

        # 10. Parse structured JSON output & extract escalation flags
        answer_text, needs_esc, esc_reason = self._parse_llm_json_response(raw_output)

        model_used = request.model_name or getattr(llm, "model_name", getattr(llm, "model", "default"))
        point_ids = [s["id"] for s in sources if "id" in s]

        return ChatResponse(
            status="success",
            tenant_id=request.tenant_id.strip(),
            provider=llm_provider.strip().lower(),
            model_name=str(model_used),
            answer=answer_text,
            needs_escalation=needs_esc,
            escalation_reason=esc_reason,
            sources=point_ids,
        )


# Singleton instance
rag_service = RAGService()
