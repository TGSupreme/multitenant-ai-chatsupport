from typing import List, Optional

from core.constants import DEFAULT_BASE_SYSTEM_PROMPT
from models.response import SourceChunk


class PromptBuilder:
    """Centralized prompt builder enforcing strict grounding and dynamic context assembly."""

    @staticmethod
    def build_rag_prompt(
        query: str,
        sources: List[SourceChunk],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Assembles base grounding rules, optional tenant instructions, context documentation, and user query."""
        prompt_parts = [DEFAULT_BASE_SYSTEM_PROMPT]

        if system_prompt and system_prompt.strip():
            prompt_parts.append("\nADDITIONAL TENANT CUSTOM RULES:")
            prompt_parts.append(system_prompt.strip())

        prompt_parts.append("\n--- CONTEXT DOCUMENTATION START ---")

        if not sources:
            prompt_parts.append("[No matching documentation context found for this tenant.]")
        else:
            for idx, source in enumerate(sources, start=1):
                page_str = f", Page {source.page_number}" if source.page_number else ""
                prompt_parts.append(
                    f"[Source {idx}: {source.file_name}{page_str} (Chunk {source.chunk_index})]\n"
                    f"{source.text}\n"
                )

        prompt_parts.append("--- CONTEXT DOCUMENTATION END ---")
        prompt_parts.append(f"\nUSER QUESTION: {query.strip()}")
        prompt_parts.append("\nASSISTANT ANSWER:")

        return "\n".join(prompt_parts)
