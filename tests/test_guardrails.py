"""Tests for agent/guardrails.py.

Pure-function tests — no LLM, no DB, no Docker. These run in milliseconds
and verify the regex patterns + redaction logic that defend against
out-of-scope questions and PII leaks in logs.
"""

import pytest

from agent.guardrails import is_out_of_scope, redact_pii

# ---------------------------------------------------------------------------
# is_out_of_scope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Write me a Python script to scrape websites",
        "generate javascript code that does X",
        "Compose a poem about kanban boards",
        "create a story about my project",
        "Is Asana better than TaskFlow?",
        "How does Trello compare?",
        "Can you give me legal advice about my contract?",
        "I need medical advice for my team",
    ],
)
def test_refuses_out_of_scope(text: str) -> None:
    """Each of these should match an OUT_OF_SCOPE pattern."""
    refused, pattern = is_out_of_scope(text)
    assert refused is True
    assert pattern is not None


@pytest.mark.parametrize(
    "text",
    [
        "How much does the Pro plan cost?",
        "Show me my open tickets",
        "What integrations does TaskFlow support?",
        "Can I upgrade my plan?",
        "How do I invite a teammate?",
    ],
)
def test_allows_in_scope(text: str) -> None:
    """Legitimate TaskFlow questions must NOT be refused."""
    refused, pattern = is_out_of_scope(text)
    assert refused is False
    assert pattern is None


def test_case_insensitive() -> None:
    """Refusal patterns must match regardless of casing — users don't capitalize consistently."""
    refused, _ = is_out_of_scope("WRITE ME A PYTHON SCRIPT")
    assert refused is True


# ---------------------------------------------------------------------------
# redact_pii
# ---------------------------------------------------------------------------


def test_redacts_email() -> None:
    """Emails must be replaced with [EMAIL]."""
    result = redact_pii("Contact william.johnson@example.org for help.")
    assert "william.johnson@example.org" not in result
    assert "[EMAIL]" in result


def test_redacts_phone() -> None:
    """US-style phone numbers must be replaced with [PHONE]."""
    result = redact_pii("Call me at 415-555-1234 anytime.")
    assert "415-555-1234" not in result
    assert "[PHONE]" in result


def test_redacts_ipv4() -> None:
    """IPv4 addresses must be replaced with [IP]."""
    result = redact_pii("Request came from 192.168.1.42.")
    assert "192.168.1.42" not in result
    assert "[IP]" in result


def test_idempotent_on_clean_text() -> None:
    """Text without PII must come out unchanged — no false-positive redactions."""
    text = "TF-1101 is a perfectly normal ticket ID."
    assert redact_pii(text) == text


def test_redacts_multiple_pii_types_in_one_string() -> None:
    """All redaction patterns must apply, not just the first match."""
    text = "User a@b.com from 10.0.0.1 called 555-123-4567."
    result = redact_pii(text)
    assert "[EMAIL]" in result
    assert "[IP]" in result
    assert "[PHONE]" in result
