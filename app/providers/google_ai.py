from .base import BaseProvider


class GoogleAIProvider(BaseProvider):
    name = "google_ai"
    # Google AI Studio's OpenAI-compatibility endpoint.
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
