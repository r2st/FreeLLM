from fastapi import APIRouter
from pydantic import BaseModel

from .common import run_task

router = APIRouter()


class SummarizeRequest(BaseModel):
    text: str
    instructions: str | None = None  # e.g. "3 bullet points", "one paragraph"
    model: str | None = None
    max_tokens: int | None = None


@router.post("/summarize")
async def summarize(req: SummarizeRequest) -> dict:
    system = (
        "You are a precise summarizer. Produce a concise, faithful summary of the "
        "provided content. Do not add information that is not in the source."
    )
    user = req.text
    if req.instructions:
        user = f"Summarization instructions: {req.instructions}\n\n---\n\n{req.text}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return await run_task("summarize", messages, model=req.model, max_tokens=req.max_tokens)
