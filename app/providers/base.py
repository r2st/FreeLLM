import time
from dataclasses import dataclass

import httpx


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class ProviderError(Exception):
    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        self.message = message
        super().__init__(f"{provider}: {message}")


class BaseProvider:
    """Provider speaking the OpenAI-compatible /chat/completions protocol.

    OpenRouter, Groq, and Google AI Studio all expose this protocol, so
    subclasses only need to set `name`, `base_url`, and optional headers.
    """

    name = "base"
    base_url = ""

    def __init__(self, api_key: str, timeout: float = 60.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def extra_headers(self) -> dict:
        return {}

    async def generate(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GenerationResult:
        if not self.available:
            raise ProviderError(self.name, "no API key configured")

        payload: dict = {"model": model, "messages": messages}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature

        headers = {"Authorization": f"Bearer {self.api_key}", **self.extra_headers()}

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"request failed: {exc}") from exc
        latency_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            raise ProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(self.name, f"unexpected response shape: {str(data)[:300]}") from exc

        usage = data.get("usage") or {}
        return GenerationResult(
            text=text,
            provider=self.name,
            model=data.get("model", model),
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
        )
