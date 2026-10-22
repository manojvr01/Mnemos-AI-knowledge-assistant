import asyncio
from typing import AsyncGenerator, List, Dict, Any
from app.rag.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic Mock LLM Provider for unit and integration testing.
    Synthesizes grounded responses with citations [citation:N] based directly
    on retrieved passages provided in the prompt. When no context is present,
    it returns the standard insufficient evidence statement.
    """

    def __init__(self, model_name: str = "mock-grounded-v1"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def _synthesize_answer(self, messages: List[Dict[str, str]]) -> str:
        # Find user and system messages
        combined_text = " ".join(m.get("content", "") for m in messages)

        # Check if context passages are present
        if "Context passages:" not in combined_text or "No relevant passages found" in combined_text:
            return "I don't have enough information in the uploaded documents to answer this question."

        # Extract context block
        try:
            user_question = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    content = m.get("content", "")
                    if "User Question:" in content:
                        user_question = content.split("User Question:")[-1].strip()
                    else:
                        user_question = content.strip()
                    break

            context_section = combined_text.split("Context passages:")[1]
            if "User Question:" in context_section:
                context_section = context_section.split("User Question:")[0]

            if "Passage [citation:1]" not in context_section:
                return "I don't have enough information in the uploaded documents to answer this question."

            import re
            query_words = [w.lower() for w in re.findall(r"\b\w+\b", user_question)]
            stopwords = {'what', 'who', 'where', 'when', 'why', 'how', 'is', 'are', 'the', 'a', 'an', 'in', 'of', 'for', 'to', 'and', 'or', 'about', 'can', 'you', 'tell', 'me'}
            filtered_words = [w for w in query_words if w not in stopwords] or query_words

            # Extract lines from context
            raw_lines = context_section.split("\n")
            passage_lines = []
            for l in raw_lines:
                s = l.strip()
                if not s or s.startswith("--- Passage") or s.startswith("Context passages"):
                    continue
                clean = re.sub(r"[^\x20-\x7E\n]", " ", s).strip()
                if clean:
                    passage_lines.append(clean)

            # Match lines containing query words and expand section headers
            matched = []
            for idx, pl in enumerate(passage_lines):
                pl_lower = pl.lower()
                if any(w in pl_lower for w in filtered_words):
                    if pl not in matched:
                        matched.append(pl)
                    # If this is a header or short line, include adjacent detail lines
                    if len(pl) < 35 and idx + 1 < len(passage_lines):
                        for next_l in passage_lines[idx+1:idx+5]:
                            if next_l not in matched and not (next_l.isupper() and len(next_l) < 25):
                                matched.append(next_l)

            if matched:
                formatted = "\n".join(f"- {m}" for m in matched[:8])
                return (
                    f"Based on the provided documents [citation:1]:\n\n"
                    f"{formatted}\n\n"
                    f"The details above are directly sourced from the verified passages."
                )
            else:
                sample_lines = passage_lines[:5]
                if sample_lines:
                    formatted = "\n".join(f"- {s}" for s in sample_lines)
                    return (
                        f"Based on the provided documents [citation:1]:\n\n"
                        f"{formatted}\n\n"
                        f"All responses are strictly grounded in the uploaded source documents."
                    )
                return (
                    "Based on the provided documents [citation:1], the document contains verified information "
                    "relevant to your inquiry. The knowledge assistant grounds all responses directly in source passages."
                )
        except Exception:
            return "I don't have enough information in the uploaded documents to answer this question."

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        content = self._synthesize_answer(messages)
        prompt_chars = sum(len(m.get("content", "")) for m in messages)
        return {
            "content": content,
            "prompt_tokens": max(1, prompt_chars // 4),
            "completion_tokens": max(1, len(content) // 4),
            "model_name": self._model_name,
        }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        content = self._synthesize_answer(messages)
        words = content.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)
