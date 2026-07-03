from fastapi import HTTPException

from ..router import AllProvidersFailedError, get_router
from ..tracking.usage import log_request


async def run_task(
    task_type: str,
    messages: list[dict],
    model: str | None = None,
    complexity: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    """Route a task through the free-model router, log usage, and shape the response."""
    router = get_router()
    try:
        result = await router.route(
            task_type,
            messages,
            model=model,
            complexity=complexity,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except AllProvidersFailedError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "All free providers failed",
                "provider_errors": exc.errors,
                "suggestion": "No free model could handle this request — Claude should handle it directly.",
            },
        ) from exc

    log_request(
        result.provider,
        result.model,
        task_type,
        result.input_tokens,
        result.output_tokens,
        result.latency_ms,
    )
    return {
        "result": result.text,
        "provider": result.provider,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": result.latency_ms,
    }
