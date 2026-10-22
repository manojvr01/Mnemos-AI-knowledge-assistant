import httpx
import json
from typing import AsyncGenerator, List, Dict, Any
from app.rag.llm.base import BaseLLMProvider


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider (e.g. gemini-3.5-flash).
    Uses Google AI Studio Generative Language REST API.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided to use GeminiLLMProvider.")
        self.api_key = api_key
        self._model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        self.stream_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _convert_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        contents = []
        system_instruction = None

        for m in messages:
            role = m.get("role")
            text = m.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({"role": gemini_role, "parts": [{"text": text}]})

        body: Dict[str, Any] = {"contents": contents}
        if system_instruction:
            body["system_instruction"] = system_instruction
        return body

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        url = f"{self.endpoint}?key={self.api_key}"
        body = self._convert_messages(messages)
        body["generationConfig"] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini generation error ({resp.status_code}): {resp.text}")
            data = resp.json()
            candidate = data["candidates"][0]
            text = candidate["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            return {
                "content": text,
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "model_name": self._model_name,
            }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        url = f"{self.stream_endpoint}?alt=sse&key={self.api_key}"
        body = self._convert_messages(messages)
        body["generationConfig"] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=body) as response:
                if response.status_code != 200:
                    err = await response.aread()
                    raise RuntimeError(f"Gemini streaming error ({response.status_code}): {err.decode('utf-8')}")

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        try:
                            chunk = json.loads(data_str)
                            parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                yield parts[0]["text"]
                        except Exception:
                            continue
