import json
import re

from fastapi import APIRouter
from pydantic import BaseModel

from .common import run_task

router = APIRouter()


class ReviewRequest(BaseModel):
    code: str
    context: str | None = None
    language: str | None = None
    model: str | None = None
    max_tokens: int | None = None


def _try_parse_json(text: str) -> dict | None:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


@router.post("/review")
async def review(req: ReviewRequest) -> dict:
    system = (
        "You are a senior code reviewer. Review the provided code for bugs, security "
        "issues, performance problems, and style. Respond ONLY with JSON in this exact "
        'shape: {"issues": [{"severity": "high|medium|low", "description": "..."}], '
        '"suggestions": ["..."]}'
    )
    parts = []
    if req.language:
        parts.append(f"Language: {req.language}")
    if req.context:
        parts.append(f"Context: {req.context}")
    parts.append(f"Code to review:\n\n```\n{req.code}\n```")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(parts)},
    ]
    response = await run_task(
        "review", messages, model=req.model, complexity="complex", max_tokens=req.max_tokens
    )
    parsed = _try_parse_json(response["result"])
    if parsed is not None:
        response["issues"] = parsed.get("issues", [])
        response["suggestions"] = parsed.get("suggestions", [])
    return response
