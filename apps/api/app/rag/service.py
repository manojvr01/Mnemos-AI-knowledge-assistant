import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.search import VectorSearchService
from app.rag.llm.factory import get_llm_provider
from app.rag.citations import CitationValidator
from app.schemas.search import SearchResultChunk
from app.core.config import settings

GROUNDED_SYSTEM_PROMPT = """You are Mnemos, an AI Knowledge Assistant dedicated to strictly grounded, evidence-based answers.

Instructions:
1. Base your answer EXCLUSIVELY on the provided Context passages below. Do not use outside knowledge or assumptions.
2. For EVERY claim or fact you make, cite the corresponding passage using the exact format [citation:N], where N is the integer index of the passage (e.g., [citation:1]).
3. If the context does not contain sufficient information to answer the question, or if no passages are provided, you MUST explicitly respond with:
"I don't have enough information in the uploaded documents to answer this question."
4. Never invent or hallucinate citations or document facts.
"""


class RAGService:
    """
    Orchestrates the retrieval-augmented generation pipeline:
    1. Vector retrieval of top-k passages matching query.
    2. Prompt construction with strict anti-hallucination constraints.
    3. LLM answer generation (or streaming).
    4. Citation validation and ungrounded citation stripping.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.search_service = VectorSearchService(db=db)
        self.llm_provider = get_llm_provider()
        self.citation_validator = CitationValidator()

    def build_rag_messages(
        self,
        query: str,
        retrieved_chunks: List[SearchResultChunk],
        chat_history: List[Dict[str, str]] | None = None,
    ) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": GROUNDED_SYSTEM_PROMPT}]

        # Append recent chat history if present
        if chat_history:
            messages.extend(chat_history[-6:]) # Keep last 3 turns for context

        # Format context passages
        if retrieved_chunks:
            passage_lines = []
            for i, chunk in enumerate(retrieved_chunks):
                idx = i + 1
                page_str = f" (Page {chunk.page_number})" if chunk.page_number else ""
                passage_lines.append(
                    f"--- Passage [citation:{idx}] from '{chunk.document_title}'{page_str} ---\n{chunk.content}"
                )
            context_block = "\n\n".join(passage_lines)
            user_content = f"Context passages:\n{context_block}\n\nUser Question:\n{query}"
        else:
            user_content = f"Context passages:\nNo relevant passages found.\n\nUser Question:\n{query}"

        messages.append({"role": "user", "content": user_content})
        return messages

    async def answer_question(
        self,
        workspace_id: uuid.UUID,
        query: str,
        collection_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        chat_history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """
        Executes complete RAG pipeline:
        Retrieve -> Synthesize -> Validate Citations -> Return result dict.
        """
        # 1. Retrieve passages
        chunks = await self.search_service.search(
            workspace_id=workspace_id,
            query=query,
            top_k=settings.RAG_TOP_K,
            similarity_threshold=settings.RAG_SIMILARITY_THRESHOLD,
            collection_id=collection_id,
            document_id=document_id,
        )

        # 2. Build prompt
        messages = self.build_rag_messages(query, chunks, chat_history)

        # 3. Generate answer
        llm_result = await self.llm_provider.generate_response(messages)

        # 4. Validate citations
        cleaned_content, valid_citations, insufficient = self.citation_validator.validate_and_extract_citations(
            response_text=llm_result["content"],
            retrieved_chunks=chunks,
        )

        return {
            "content": cleaned_content,
            "citations": valid_citations,
            "insufficient_evidence": insufficient,
            "model_name": llm_result["model_name"],
            "prompt_tokens": llm_result["prompt_tokens"],
            "completion_tokens": llm_result["completion_tokens"],
            "retrieved_chunks": chunks,
        }
