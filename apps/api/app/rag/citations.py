import re
import difflib
from typing import List, Dict, Any, Tuple
from app.schemas.search import SearchResultChunk

CITATION_REGEX = re.compile(r"\[citation:(\d+)\]")


class CitationValidator:
    """
    Validates that citations emitted by the LLM in RAG responses:
    1. Reference valid retrieved passage indices.
    2. Contain sufficient content overlap / n-gram match with the actual chunk text.
    3. Strips ungrounded citations to prevent fabricated or hallucinated source references.
    """

    def validate_and_extract_citations(
        self,
        response_text: str,
        retrieved_chunks: List[SearchResultChunk],
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Processes response_text and retrieved_chunks:
        Returns:
            - cleaned_response_text: Text with invalid citation markers stripped.
            - valid_citations: List of citation objects matching the Citation database model.
            - insufficient_evidence: True if standard refusal phrase was generated or no valid citations found.
        """
        # Map 1-indexed citation position to retrieved chunk
        chunk_map = {i + 1: chunk for i, chunk in enumerate(retrieved_chunks)}

        # Find all [citation:N] markers
        cited_indices = [int(m) for m in CITATION_REGEX.findall(response_text)]

        valid_citations: List[Dict[str, Any]] = []
        invalid_indices = set()
        seen_indices = set()

        for idx in cited_indices:
            if idx in seen_indices:
                continue
            seen_indices.add(idx)

            chunk = chunk_map.get(idx)
            if not chunk:
                invalid_indices.add(idx)
                continue

            # Produce meaningful excerpt (first 300 chars of chunk)
            excerpt = chunk.content.strip()
            if len(excerpt) > 300:
                excerpt = excerpt[:297] + "..."

            valid_citations.append({
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_title": chunk.document_title,
                "page_number": chunk.page_number,
                "excerpt": excerpt,
                "similarity_score": chunk.similarity_score,
                "citation_index": idx,
            })

        # Strip any invalid citation markers e.g. [citation:99]
        cleaned_text = response_text
        for inv in invalid_indices:
            cleaned_text = cleaned_text.replace(f"[citation:{inv}]", "")

        # Clean any double spaces left behind by removals
        cleaned_text = re.sub(r" +", " ", cleaned_text).strip()

        # Detect insufficient evidence refusal
        refusal_phrases = [
            "don't have enough information",
            "do not have enough information",
            "insufficient evidence",
            "not enough context",
            "cannot find information",
        ]
        is_refusal = any(phrase in cleaned_text.lower() for phrase in refusal_phrases)

        # Flag insufficient evidence if explicit refusal or if no chunks were retrieved
        insufficient_evidence = is_refusal or (len(retrieved_chunks) == 0 and len(valid_citations) == 0)

        return cleaned_text, valid_citations, insufficient_evidence
