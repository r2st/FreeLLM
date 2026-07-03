from datetime import datetime, timezone

from .config import Settings, get_settings
from .providers import (
    BaseProvider,
    GenerationResult,
    GoogleAIProvider,
    GroqProvider,
    OpenRouterProvider,
    ProviderError,
)

# Task types that don't need a big model.
SIMPLE_TASKS = {"summarize", "transform"}


class AllProvidersFailedError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors) or "no providers configured")


class SmartRouter:
    """Routes requests to free models with tier selection and provider failover."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        timeout = settings.timeout
        self.providers: dict[str, BaseProvider] = {
            "openrouter": OpenRouterProvider(settings.openrouter_api_key, timeout),
            "groq": GroqProvider(settings.groq_api_key, timeout),
            "google_ai": GoogleAIProvider(settings.google_ai_key, timeout),
        }
        self.status: dict[str, dict] = {
            name: {"last_success": None, "last_error": None} for name in self.providers
        }

    def classify(self, task_type: str, complexity: str | None = None) -> str:
        if complexity in ("simple", "complex"):
            return complexity
        return "simple" if task_type in SIMPLE_TASKS else "complex"

    def _candidates(self, tier: str, requested_model: str | None) -> list[tuple[BaseProvider, list[str]]]:
        """(provider, models-to-try) pairs in fallback order."""
        out: list[tuple[BaseProvider, list[str]]] = []
        for name in self.settings.fallback_order:
            provider = self.providers.get(name)
            if provider is None or not provider.available:
                continue
            model_cfg = self.settings.models.get(name, {})
            if requested_model:
                known = [m for tier_models in model_cfg.values() for m in tier_models]
                if requested_model in known:
                    out.append((provider, [requested_model]))
                continue
            models = model_cfg.get(tier) or model_cfg.get("complex") or model_cfg.get("simple") or []
            if models:
                out.append((provider, models))
        if requested_model and not out:
            # Model not in config — try it verbatim on the first available provider.
            for name in self.settings.fallback_order:
                provider = self.providers.get(name)
                if provider is not None and provider.available:
                    out.append((provider, [requested_model]))
                    break
        return out

    async def route(
        self,
        task_type: str,
        messages: list[dict],
        model: str | None = None,
        complexity: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GenerationResult:
        tier = self.classify(task_type, complexity)
        errors: list[str] = []
        for provider, models in self._candidates(tier, model):
            for m in models:
                try:
                    result = await provider.generate(m, messages, max_tokens, temperature)
                except ProviderError as exc:
                    errors.append(f"{exc} (model={m})")
                    self.status[provider.name]["last_error"] = exc.message
                    continue
                self.status[provider.name]["last_success"] = datetime.now(timezone.utc).isoformat()
                return result
        if not errors:
            errors.append("no providers configured — set OPENROUTER_API_KEY, GROQ_API_KEY, or GOOGLE_AI_KEY in .env")
        raise AllProvidersFailedError(errors)


_router: SmartRouter | None = None


def get_router() -> SmartRouter:
    global _router
    if _router is None:
        _router = SmartRouter(get_settings())
    return _router
