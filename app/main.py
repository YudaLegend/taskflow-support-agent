"""FastAPI serving layer for the TaskFlow support agent.

Run locally:
    uv run uvicorn app.main:app --reload --port 8000

Then open:
    http://localhost:8000/docs    — interactive OpenAPI explorer
    http://localhost:8000/health  — liveness check

Architecture:
    Browser  ──HTTP──>  FastAPI (this file)  ──in-process──>  LangGraph agent
                              │
                              └──callbacks──>  Langfuse (port 3000)

The FastAPI process is STATELESS — all conversation state lives in
LangGraph's MemorySaver, keyed by `thread_id` from the client. Restart
the API and conversations are lost (this is fine for dev; Day 22+ will
swap in a persistent checkpointer).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from langfuse import Langfuse

from agent.graph import flush_langfuse
from app.deps import (
    check_chroma,
    check_mongo,
    get_graph,
    get_langfuse,
    get_langfuse_client,
)
from app.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    HealthResponse,
)

load_dotenv()


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown hooks
#
# Why a lifespan instead of @app.on_event("startup")? The decorator-based
# events are deprecated. Lifespan is one async context manager: code BEFORE
# `yield` runs at startup, code AFTER runs at shutdown. Cleaner, and you can
# share state via `app.state.X` if you need to.
#
# What we do here:
#   - startup: warm the graph singleton (pay the import cost once, not on
#              the first request).
#   - shutdown: flush buffered Langfuse events (otherwise the async batcher
#               may not fire and the last few traces are lost — this is the
#               exact pain point you hit on Day 18).
# ---------------------------------------------------------------------------


def _ensure_rag_index() -> None:
    """Lazy-ingest the RAG corpus on a clean disk.

    Why this exists: HF Spaces (and any container with no bind-mounted
    persistent volume) starts with an empty Chroma directory. If we don't
    seed it, search_docs_tool fires `NotFoundError: Collection [taskflow_docs]
    does not exist` on the first chat that triggers retrieval.

    The check is a no-op when the collection already exists (local dev with
    bind-mounted data/chroma_db, or a warm restart on the same disk).
    """
    import os

    import chromadb

    chroma_path = os.getenv("CHROMA_PATH", "data/chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    if any(c.name == "taskflow_docs" for c in client.list_collections()):
        print("RAG index present, skipping ingest")
        return
    print("RAG index missing, ingesting from data/docs ...")
    # Imported lazily so a warm restart doesn't pay the import cost.
    from rag.ingest import main as ingest_main

    ingest_main()
    print("RAG ingest complete")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Compile the graph once so the first /chat doesn't pay the cost.
    get_graph()

    # Ingest the RAG corpus if the collection isn't on disk yet.
    # Adds ~10–30s to first start on a clean container; instant on warm restarts.
    _ensure_rag_index()

    print("ready")

    yield

    # Flush buffered Langfuse traces; without this short-lived processes lose them.
    flush_langfuse()


app = FastAPI(
    title="TaskFlow Support Agent",
    description="Customer support chatbot for TaskFlow. POST /chat to talk to it.",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_turn_tools(messages: list) -> list[str]:
    """Return tool names called during the most recent turn.

    Walks BACKWARDS from the end of the message list until it hits the
    user's message. Everything between is "this turn" — we collect tool
    calls from any AIMessage in that span.

    Why walk backwards? `graph.ainvoke()` returns the FULL conversation
    history (all turns ever, on this thread). We only want what changed
    THIS request — that's what tells the user (and the dashboard) whether
    the agent re-fetched or answered from memory.
    """
    tools: list[str] = []
    for m in reversed(messages):
        if m.type == "human":
            break
        if m.type == "ai" and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tools.append(tc["name"])
    return list(reversed(tools))


def _build_config(thread_id: str, request_id: str, langfuse_handler) -> dict:
    """Build the RunnableConfig dict passed to graph.ainvoke / astream.

    Carries three things the agent needs:
      - configurable.thread_id   — keys the MemorySaver checkpoint
      - recursion_limit          — safety net against infinite loops (Day 14)
      - callbacks + metadata     — Langfuse tracing (Day 18)

    Note: trace ID pinning is NOT done here — see chat() and chat_stream()
    where we wrap the graph call in a langfuse.start_as_current_observation() so
    the OTel context carries our request_id as the trace_id.
    """
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 10,
        "callbacks": [langfuse_handler] if langfuse_handler else [],
        "metadata": {
            "request_id": request_id,
            "thread_id": thread_id,
        },
        "run_name": f"chat:{thread_id[:8]}",
    }


def _new_request_id() -> str:
    """Generate an ID we use as both `request_id` (returned to client) AND
    Langfuse `trace_id` (what /feedback scores against).

    Why not uuid4? Langfuse v4 uses W3C-compatible 32-char hex trace IDs;
    a UUID4 with dashes wouldn't work as a trace_id. `Langfuse.create_trace_id`
    is a static method — works without a configured client.
    """
    return Langfuse.create_trace_id()


# ---------------------------------------------------------------------------
# GET /health — liveness + dependency check
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Cheap dependency check. Returns 200 even if degraded — the body
    tells the operator WHICH dep is down. (A pure liveness check would
    return 503 on any failure; we want a richer signal here.)
    """
    # TODO 1: Call check_mongo() and check_chroma() from app.deps.
    # Set status to "ok" only if BOTH are True, else "degraded".
    # Return a HealthResponse with the three fields populated.
    mongo_ok = check_mongo()
    chroma_ok = check_chroma()
    return HealthResponse(
        status="ok" if (mongo_ok and chroma_ok) else "degraded",
        mongo=mongo_ok,
        chroma=chroma_ok,
    )


# ---------------------------------------------------------------------------
# POST /chat — non-streaming
#
# This is the ONE endpoint that does the real work. It:
#   1. Generates a request_id (so /feedback can refer to this turn).
#   2. Builds the RunnableConfig with thread_id + Langfuse callback.
#   3. Calls the agent graph asynchronously.
#   4. Pulls the final assistant text + the tool names used this turn.
#   5. Returns ChatResponse.
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    graph=Depends(get_graph),
    langfuse_handler=Depends(get_langfuse),
    langfuse_client=Depends(get_langfuse_client),
) -> ChatResponse:
    """Send one user message; get one assistant reply.

    Stateless from the server's perspective — the conversation lives in
    the LangGraph checkpointer keyed by req.thread_id. To start a new
    conversation, the client just picks a new thread_id.
    """
    request_id = _new_request_id()
    config = _build_config(req.thread_id, request_id, langfuse_handler)

    # Pin the Langfuse trace ID so /feedback can score THIS trace later.
    # Langfuse v4 uses OpenTelemetry — trace IDs are set by the active span
    # context, not by metadata. Anything inside this `with` block (including
    # the langchain callbacks) becomes a child of this span and shares its
    # trace_id. That's what makes our request_id == trace_id.
    if langfuse_client is not None:
        with langfuse_client.start_as_current_observation(
            name=f"chat:{req.thread_id[:8]}",
            as_type="chain",
            trace_context={"trace_id": request_id},
        ):
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=req.message)]},
                config=config,
            )
    else:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )

    # TODO 5: Extract the assistant's reply and the tool names used.
    #     final_text = result["messages"][-1].content
    #     tools_used = _extract_turn_tools(result["messages"])
    final_text = result["messages"][-1].content
    tools_used = _extract_turn_tools(result["messages"])
    # TODO 6: Return ChatResponse(...).
    return ChatResponse(
        request_id=request_id,
        thread_id=req.thread_id,
        response=final_text,
        tools_used=tools_used,
    )


# ---------------------------------------------------------------------------
# POST /chat/stream — SSE (Server-Sent Events) token streaming
#
# Same logic as /chat, but instead of awaiting the full result and returning
# JSON, we stream events as they happen:
#   - every LLM token   → {"type":"token","content":"..."}
#   - every tool call   → {"type":"tool_start","name":"..."}
#   - every tool result → {"type":"tool_end","name":"..."}
#   - final marker      → {"type":"done","request_id":"...","tools_used":[...]}
#
# The client (browser EventSource or `curl -N`) sees tokens within ~200ms
# instead of waiting for the whole answer.
# ---------------------------------------------------------------------------


def _sse(payload: dict) -> str:
    """Format a dict as one SSE 'data:' frame.

    The double `\\n\\n` is REQUIRED — a single newline won't flush the event
    on the client side. Keep payloads small; we send one event per token.
    """
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    graph=Depends(get_graph),
    langfuse_handler=Depends(get_langfuse),
    langfuse_client=Depends(get_langfuse_client),
) -> StreamingResponse:
    """Stream the agent's response as Server-Sent Events.

    No `response_model=` here — the body is a stream of SSE frames, not a
    single JSON object, so the OpenAPI docs UI won't render it nicely.
    Test with `curl -N` or the browser UI we'll add next.
    """
    request_id = _new_request_id()
    config = _build_config(req.thread_id, request_id, langfuse_handler)
    tools_used: list[str] = []

    async def _run_graph() -> AsyncIterator:
        """Internal helper: yield graph events, optionally wrapped in a Langfuse
        span so the trace_id matches our request_id. Same trick as /chat."""
        if langfuse_client is not None:
            with langfuse_client.start_as_current_observation(
                name=f"chat:{req.thread_id[:8]}",
                as_type="chain",
                trace_context={"trace_id": request_id},
            ):
                async for event in graph.astream_events(
                    {"messages": [HumanMessage(content=req.message)]},
                    config=config,
                    version="v2",
                ):
                    yield event
        else:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=req.message)]},
                config=config,
                version="v2",
            ):
                yield event

    async def event_stream() -> AsyncIterator[str]:
        """Yield SSE frames as the agent runs.

        graph.astream_events(..., version="v2") emits a typed event for
        every step inside the graph. We filter for the three kinds we
        care about, format each as an SSE frame, and yield. uvicorn
        writes each yielded string to the open HTTP connection
        immediately — that's the streaming.
        """
        # _run_graph wraps astream_events in a Langfuse span (when configured)
        # so the trace_id matches our request_id — same trick as /chat.
        tokens_streamed = 0
        async for event in _run_graph():
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:  # may be empty for tool-call chunks
                    tokens_streamed += 1
                    yield _sse({"type": "token", "content": chunk.content})

            elif kind == "on_tool_start":
                name = event["name"]  # e.g. "search_docs_tool"
                tools_used.append(name)
                yield _sse({"type": "tool_start", "name": name})

            elif kind == "on_tool_end":
                yield _sse({"type": "tool_end", "name": event["name"]})

        # Edge case: if NO tokens were streamed, the final message came from a
        # node that doesn't call the LLM (e.g. the guard_input refusal). Pull
        # it from the graph state and emit it as a single token frame so the
        # client bubble isn't empty.
        if tokens_streamed == 0:
            state = await graph.aget_state({"configurable": {"thread_id": req.thread_id}})
            messages = state.values.get("messages", [])
            if messages and messages[-1].type == "ai" and messages[-1].content:
                yield _sse({"type": "token", "content": messages[-1].content})

        # Final marker so the client knows it's safe to close the connection.
        yield _sse(
            {
                "type": "done",
                "request_id": request_id,
                "thread_id": req.thread_id,
                "tools_used": tools_used,
            }
        )

    # StreamingResponse takes the async generator and streams whatever it
    # yields to the client. media_type sets Content-Type; X-Accel-Buffering
    # tells nginx (if anyone proxies us later) NOT to buffer this response.
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


# ---------------------------------------------------------------------------
# POST /feedback — thumbs-up/down on a previous response
#
# The client passes back the `request_id` it received from /chat (or the
# final SSE `done` frame from /chat/stream) along with a 👍/👎 rating.
# We attach that as a SCORE to the matching Langfuse trace.
#
# In the Langfuse UI: filter traces by `score=user_feedback,value=0` to
# find every conversation a user marked thumbs-down. That's your triage
# queue — open the trace, see the exact prompt, tool calls, and answer
# that the user disliked. Closes the prod-eval feedback loop.
# ---------------------------------------------------------------------------


@app.post("/feedback", status_code=204)
async def feedback(
    req: FeedbackRequest,
    langfuse_client=Depends(get_langfuse_client),
) -> None:
    """Attach a user score to a previous /chat response's Langfuse trace.

    Returns 204 No Content on success — there's no body to give back, the
    write is fire-and-forget. 503 if Langfuse isn't configured.
    """
    if langfuse_client is None:
        raise HTTPException(
            status_code=503,
            detail="Langfuse not configured — set LANGFUSE_PUBLIC_KEY/SECRET_KEY in .env",
        )

    # Numeric value: 1 = good, 0 = bad. Numeric (not categorical) so the UI
    # can show an aggregate "thumbs-up rate" gauge over time.
    langfuse_client.create_score(
        trace_id=req.request_id,
        name="user_feedback",
        value=1.0 if req.rating == "up" else 0.0,
        comment=req.comment,
        data_type="NUMERIC",
    )
    # Flush eagerly so the score shows up in the UI immediately.
    # (Otherwise it sits in the async batcher for ~5s.)
    langfuse_client.flush()


# ---------------------------------------------------------------------------
# Static UI — minimal one-page chat client
#
# GET /          → returns app/static/index.html (the chat UI)
# GET /static/*  → any other static asset (none yet, but ready for it)
#
# Mount order matters: register specific routes BEFORE the catch-all mount,
# otherwise StaticFiles would shadow /chat, /health, etc.
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the demo chat UI."""
    return FileResponse("app/static/index.html")


app.mount("/static", StaticFiles(directory="app/static"), name="static")
