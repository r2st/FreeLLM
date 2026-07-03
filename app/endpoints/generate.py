from fastapi import APIRouter
from pydantic import BaseModel

from .common import run_task

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    model: str | None = None
    complexity: str | None = None  # "simple" | "complex"
    max_tokens: int | None = None
    temperature: float | None = None


@router.post("/generate")
async def generate(req: GenerateRequest) -> dict:
    messages: list[dict] = []
    if req.system_prompt:
        messages.append({"role": "system", "content": req.system_prompt})
    messages.append({"role": "user", "content": req.prompt})
    return await run_task(
        "generate",
        messages,
        model=req.model,
        complexity=req.complexity,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
