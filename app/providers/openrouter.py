from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"

    def extra_headers(self) -> dict:
        # OpenRouter uses these for app attribution / rankings.
        return {"HTTP-Referer": "http://localhost:8100", "X-Title": "FreeLLM"}
