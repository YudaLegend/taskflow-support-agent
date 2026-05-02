"""Shared pytest fixtures for the test suite.

Two responsibilities:
  1. Set safe defaults for env vars so importing `app.main` doesn't try to
     contact Groq / Langfuse / Mongo with real credentials.
  2. Provide a `client` fixture that yields a FastAPI TestClient with all
     external dependencies (graph, Langfuse) replaced by fakes — so tests
     never hit a real LLM, never burn tokens, and don't need Docker running.
"""

import os
from typing import Any

# Set BEFORE importing anything from the app — agent.graph constructs a
# ChatGroq instance at module level and reads GROQ_API_KEY from env.
os.environ.setdefault("GROQ_API_KEY", "test-key-not-used")

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from app.deps import get_graph, get_langfuse, get_langfuse_client
from app.main import app


class FakeGraph:
    """Stand-in for the compiled LangGraph used in /chat tests.

    Tests can override `canned_messages` before making a request to control
    what `ainvoke()` returns. Default = a benign assistant reply with no
    tool calls.
    """

    def __init__(self) -> None:
        self.canned_messages: list[Any] = [
            HumanMessage(content="hi"),
            AIMessage(content="Hello! How can I help you with TaskFlow?"),
        ]

    async def ainvoke(self, _input: dict, config: dict | None = None) -> dict:
        # Real signature is `ainvoke(input, *, config=None, ...)` — match that
        # so the endpoint's `await graph.ainvoke(..., config=config)` call works.
        return {"messages": self.canned_messages}


@pytest.fixture
def fake_graph() -> FakeGraph:
    """A fresh fake graph per test (so canned_messages mutations don't leak)."""
    return FakeGraph()


@pytest.fixture
def client(fake_graph, monkeypatch):
    """TestClient with all external deps mocked.

    Why monkeypatch `app.main.get_graph` AND set `dependency_overrides`?
    The lifespan handler calls `get_graph()` directly (not via Depends) at
    startup — only the monkeypatch reaches that. The endpoints use Depends —
    only the override reaches those. Belt and suspenders.
    """
    monkeypatch.setattr("app.main.get_graph", lambda: fake_graph)
    # Skip the lazy RAG ingest in lifespan — tests don't need a real Chroma
    # collection (the graph is mocked anyway), and ingesting on every test
    # run would add 10-30s of model-loading overhead.
    monkeypatch.setattr("app.main._ensure_rag_index", lambda: None)
    app.dependency_overrides[get_graph] = lambda: fake_graph
    app.dependency_overrides[get_langfuse] = lambda: None
    app.dependency_overrides[get_langfuse_client] = lambda: None

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
