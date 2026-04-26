"""Pydantic request/response models for the FastAPI layer.

FastAPI reads the type hints on endpoint params and uses these models to:
  1. Parse + validate the incoming JSON body (a 422 is returned on bad input
     BEFORE your endpoint code runs — free input validation).
  2. Auto-generate OpenAPI docs at /docs and /redoc.
  3. Serialize the return value back to JSON.

Keep these models thin. They describe the WIRE FORMAT, not domain logic.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Body of POST /chat and POST /chat/stream."""

    thread_id: str = Field(
        min_length=1,
        max_length=128,
        description=(
            "Client-supplied conversation ID. Same thread_id = same conversation "
            "memory (LangGraph's MemorySaver keys on this). Pick a UUID per "
            "browser tab / session."
        ),
    )
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    """Body of the (non-streaming) /chat response."""

    request_id: str = Field(description="Unique ID for this request — use it in /feedback.")
    thread_id: str
    response: str
    tools_used: list[str] = Field(
        description="Names of tools called during THIS turn (empty if answered from memory)."
    )


class FeedbackRequest(BaseModel):
    """Body of POST /feedback. Thumbs-up/down on a previous /chat response."""

    request_id: str
    rating: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=2000)


class HealthResponse(BaseModel):
    """Body of GET /health."""

    status: Literal["ok", "degraded"]
    mongo: bool
    chroma: bool
