"""Dependency-injection providers for the FastAPI app.

Why a thin DI layer? Two reasons:
  1. Endpoints stay easy to test — override these in pytest with monkeypatch.
  2. Expensive resources (the compiled LangGraph, the Langfuse client) are
     built ONCE at startup, not per-request.

Use them in routes via:    def my_route(graph = Depends(get_graph)): ...
"""

import os
from functools import lru_cache

from chromadb import PersistentClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from agent.graph import (
    build_graph,
    get_langfuse_handler,
)
from agent.graph import (
    get_langfuse_client as _agent_langfuse_client,
)

# ---------------------------------------------------------------------------
# Heavyweight singletons — built once, reused for the lifetime of the process.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_graph():
    """Return the compiled LangGraph agent (singleton).

    build_graph() compiles a StateGraph and creates a MemorySaver checkpointer.
    Both must be process-wide singletons — if we rebuilt per request, every
    conversation would start from scratch (no memory).
    """
    return build_graph()


@lru_cache(maxsize=1)
def get_langfuse():
    """Return the Langfuse CallbackHandler if configured, else None.

    Returns None when LANGFUSE_* env vars aren't set so the API still works
    in environments without observability (e.g. CI smoke tests).
    """
    return get_langfuse_handler()


@lru_cache(maxsize=1)
def get_langfuse_client():
    """Return the raw Langfuse client (for /feedback's create_score), or None.

    Distinct from get_langfuse() — that's the LangChain CallbackHandler used
    DURING a run. The raw client is needed AFTER a run to attach scores
    (👍/👎 feedback) to an existing trace by trace_id.
    """
    return _agent_langfuse_client()


# ---------------------------------------------------------------------------
# Health checks — cheap pings for /health.
# ---------------------------------------------------------------------------


def check_mongo() -> bool:
    """Return True if MongoDB is reachable. Bounded by a 500ms timeout."""
    try:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        client = MongoClient(uri, serverSelectionTimeoutMS=500)
        client.admin.command("ping")
        return True
    except (PyMongoError, Exception):
        return False


def check_chroma() -> bool:
    """Return True if the ChromaDB persistent store opens cleanly."""
    try:
        path = os.getenv("CHROMA_PATH", os.path.join("data", "chroma_db"))
        client = PersistentClient(path=path)
        client.list_collections()
        return True
    except Exception:
        return False
