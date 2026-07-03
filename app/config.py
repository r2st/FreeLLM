import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.google_ai_key = os.getenv("GOOGLE_AI_KEY", "")

        config_file = BASE_DIR / "config.yaml"
        self.config: dict = yaml.safe_load(config_file.read_text()) if config_file.exists() else {}

    @property
    def fallback_order(self) -> list[str]:
        return self.config.get("fallback_order", ["openrouter", "groq", "google_ai"])

    @property
    def models(self) -> dict:
        return self.config.get("models", {})

    @property
    def timeout(self) -> float:
        return float(self.config.get("request_timeout_seconds", 60))

    @property
    def claude_pricing(self) -> dict:
        return self.config.get("claude_pricing", {"input_per_mtok": 3.0, "output_per_mtok": 15.0})


@lru_cache
def get_settings() -> Settings:
    return Settings()
