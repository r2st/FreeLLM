from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .endpoints import chat, code, generate, review, summarize, transform
from .router import get_router
from .tracking.db import init_db
from .tracking.usage import get_usage_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="FreeLLM",
    description="Local AI gateway that routes routine tasks to free LLM APIs to save Claude tokens.",
    version="0.1.0",
    lifespan=lifespan,
)

for module in (generate, summarize, code, review, transform, chat):
    app.include_router(module.router)


@app.get("/health")
async def health() -> dict:
    r = get_router()
    providers = {
        name: {"configured": provider.available, **r.status[name]}
        for name, provider in r.providers.items()
    }
    any_configured = any(p.available for p in r.providers.values())
    return {
        "status": "ok" if any_configured else "degraded",
        "service": "FreeLLM",
        "providers": providers,
        "fallback_order": get_settings().fallback_order,
    }


@app.get("/models")
async def models() -> dict:
    settings = get_settings()
    r = get_router()
    out = []
    for provider_name, tiers in settings.models.items():
        provider = r.providers.get(provider_name)
        available = provider.available if provider else False
        for tier, model_list in tiers.items():
            for m in model_list or []:
                out.append(
                    {"provider": provider_name, "model": m, "tier": tier, "available": available}
                )
    return {"models": out, "fallback_order": settings.fallback_order}


@app.get("/usage")
async def usage() -> dict:
    return get_usage_stats()
