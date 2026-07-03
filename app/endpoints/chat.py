from fastapi import APIRouter
from pydantic import BaseModel, Field

from .common import run_task

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    model: str | None = None
    complexity: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


@router.post("/chat")
async def chat(req: ChatRequest) -> dict:
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    return await run_task(
        "chat",
        messages,
        model=req.model,
        complexity=req.complexity,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
