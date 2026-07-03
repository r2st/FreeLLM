from datetime import datetime, timezone

from ..config import get_settings
from .db import get_conn


def log_request(
    provider: str,
    model: str,
    task_type: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO requests (timestamp, provider, model, task_type, input_tokens, output_tokens, latency_ms)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                provider,
                model,
                task_type,
                input_tokens,
                output_tokens,
                latency_ms,
            ),
        )


def get_usage_stats() -> dict:
    with get_conn() as conn:
        totals = conn.execute(
            "SELECT COUNT(*) AS requests,"
            " COALESCE(SUM(input_tokens), 0) AS input_tokens,"
            " COALESCE(SUM(output_tokens), 0) AS output_tokens,"
            " COALESCE(AVG(latency_ms), 0) AS avg_latency_ms"
            " FROM requests"
        ).fetchone()
        by_provider = conn.execute(
            "SELECT provider, COUNT(*) AS requests,"
            " SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens"
            " FROM requests GROUP BY provider ORDER BY requests DESC"
        ).fetchall()
        by_model = conn.execute(
            "SELECT model, COUNT(*) AS requests,"
            " SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens"
            " FROM requests GROUP BY model ORDER BY requests DESC"
        ).fetchall()
        by_task = conn.execute(
            "SELECT task_type, COUNT(*) AS requests,"
            " SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens"
            " FROM requests GROUP BY task_type ORDER BY requests DESC"
        ).fetchall()

    pricing = get_settings().claude_pricing
    input_rate = float(pricing.get("input_per_mtok", 3.0))
    output_rate = float(pricing.get("output_per_mtok", 15.0))
    savings = (
        totals["input_tokens"] / 1_000_000 * input_rate
        + totals["output_tokens"] / 1_000_000 * output_rate
    )

    return {
        "total_requests": totals["requests"],
        "total_input_tokens": totals["input_tokens"],
        "total_output_tokens": totals["output_tokens"],
        "total_tokens_routed_to_free_models": totals["input_tokens"] + totals["output_tokens"],
        "avg_latency_ms": round(totals["avg_latency_ms"], 1),
        "estimated_claude_cost_saved_usd": round(savings, 4),
        "pricing_assumption": {
            "claude_input_usd_per_mtok": input_rate,
            "claude_output_usd_per_mtok": output_rate,
        },
        "by_provider": [dict(r) for r in by_provider],
        "by_model": [dict(r) for r in by_model],
        "by_task_type": [dict(r) for r in by_task],
    }
