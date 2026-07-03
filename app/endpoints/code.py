from fastapi import APIRouter
from pydantic import BaseModel

from .common import run_task

router = APIRouter()


class CodeRequest(BaseModel):
    description: str
    language: str
    framework: str | None = None
    model: str | None = None
    max_tokens: int | None = None


@router.post("/code")
async def code(req: CodeRequest) -> dict:
    system = (
        "You are an expert software engineer. Write clean, idiomatic, production-quality "
        "code. Respond with the code in a fenced code block, followed by a brief note on "
        "usage only if necessary."
    )
    parts = [f"Language: {req.language}"]
    if req.framework:
        parts.append(f"Framework: {req.framework}")
    parts.append(f"Task: {req.description}")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(parts)},
    ]
    return await run_task(
        "code", messages, model=req.model, complexity="complex", max_tokens=req.max_tokens
    )
