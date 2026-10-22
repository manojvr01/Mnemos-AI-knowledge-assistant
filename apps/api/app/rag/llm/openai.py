import httpx
import json
from typing import AsyncGenerator, List, Dict, Any
from app.rag.llm.base import BaseLLMProvider


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI chat completions provider (e.g. gpt-4o-mini, gpt-4o).
    Supports both standard asynchronous generation and SSE token streaming.
    """

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be provided to use OpenAILLMProvider.")
        self.api_key = api_key
        self._model_name = model_name
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI completion error ({resp.status_code}): {resp.text}")
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return {
                "content": choice["message"]["content"],
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "model_name": self._model_name,
            }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.endpoint, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    err = await response.aread()
                    raise RuntimeError(f"OpenAI streaming error ({response.status_code}): {err.decode('utf-8')}")

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
