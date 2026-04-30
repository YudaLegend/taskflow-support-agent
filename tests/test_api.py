"""Endpoint tests for app/main.py.

These hit the real FastAPI app via TestClient but with `get_graph` and
the Langfuse deps overridden to fakes — so no Groq tokens are spent and
no Docker stack is required.

Coverage:
  /health     — ok and degraded shapes
  /chat       — happy path + Pydantic validation errors
  /feedback   — 503 when Langfuse unconfigured + Pydantic validation
"""

from langchain_core.messages import AIMessage, HumanMessage


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_ok(client, monkeypatch) -> None:
    """When both deps are healthy, /health returns 200 + status='ok'."""
    monkeypatch.setattr("app.main.check_mongo", lambda: True)
    monkeypatch.setattr("app.main.check_chroma", lambda: True)

    r = client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok", "mongo": True, "chroma": True}


def test_health_degraded_when_mongo_down(client, monkeypatch) -> None:
    """One dep down = 200 with status='degraded' (NOT 503 — we want a richer signal)."""
    monkeypatch.setattr("app.main.check_mongo", lambda: False)
    monkeypatch.setattr("app.main.check_chroma", lambda: True)

    r = client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"
    assert body["mongo"] is False
    assert body["chroma"] is True


# ---------------------------------------------------------------------------
# /chat
# ---------------------------------------------------------------------------

def test_chat_happy_path(client, fake_graph) -> None:
    """A valid request returns 200 with response, request_id, and empty tools_used."""
    fake_graph.canned_messages = [
        HumanMessage(content="hi"),
        AIMessage(content="Hello, how can I help?"),
    ]

    r = client.post(
        "/chat",
        json={"thread_id": "t1", "message": "hi"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["thread_id"] == "t1"
    assert body["response"] == "Hello, how can I help?"
    assert body["tools_used"] == []
    assert isinstance(body["request_id"], str) and len(body["request_id"]) > 0


def test_chat_extracts_tools_used(client, fake_graph) -> None:
    """When the fake graph returns AIMessages with tool_calls, /chat reports them."""
    fake_graph.canned_messages = [
        HumanMessage(content="prices?"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "search_docs_tool", "args": {}, "id": "c0", "type": "tool_call"}
            ],
        ),
        AIMessage(content="The Pro plan is $12/mo."),
    ]

    r = client.post("/chat", json={"thread_id": "t2", "message": "prices?"})

    assert r.status_code == 200
    assert r.json()["tools_used"] == ["search_docs_tool"]


def test_chat_rejects_missing_thread_id(client) -> None:
    """Pydantic validates the body before our endpoint runs — missing thread_id => 422."""
    r = client.post("/chat", json={"message": "hi"})
    assert r.status_code == 422


def test_chat_rejects_empty_message(client) -> None:
    """ChatRequest declares min_length=1 on message — empty string fails validation."""
    r = client.post("/chat", json={"thread_id": "t1", "message": ""})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# /feedback
# ---------------------------------------------------------------------------

def test_feedback_returns_503_when_langfuse_unconfigured(client) -> None:
    """The `client` fixture overrides get_langfuse_client to return None — /feedback
    must respond with 503, not silently no-op or 500.
    """
    r = client.post(
        "/feedback",
        json={"request_id": "abc123", "rating": "up"},
    )
    assert r.status_code == 503
    assert "langfuse" in r.json()["detail"].lower()


def test_feedback_rejects_invalid_rating(client) -> None:
    """Rating must be Literal['up', 'down'] — anything else is 422."""
    r = client.post(
        "/feedback",
        json={"request_id": "abc123", "rating": "neutral"},
    )
    assert r.status_code == 422


def test_feedback_rejects_missing_request_id(client) -> None:
    r = client.post("/feedback", json={"rating": "down"})
    assert r.status_code == 422
