from fastapi import APIRouter
from pydantic import BaseModel

from .common import run_task

router = APIRouter()


class TransformRequest(BaseModel):
    text: str
    transformation: str  # e.g. "rewrite formally", "translate to French", "format as a markdown table"
    model: str | None = None
    max_tokens: int | None = None


@router.post("/transform")
async def transform(req: TransformRequest) -> dict:
    system = (
        "You transform text exactly as instructed — rewrite, translate, or reformat. "
        "Respond with ONLY the transformed text, no preamble or explanation."
    )
    user = f"Transformation: {req.transformation}\n\n---\n\n{req.text}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return await run_task("transform", messages, model=req.model, max_tokens=req.max_tokens)
