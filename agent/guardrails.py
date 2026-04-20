"""Guardrails for the TaskFlow support agent.

Three concerns, kept separate so they can be tested independently:
  1. is_out_of_scope(text)  → Should we refuse this question outright?
  2. redact_pii(text)        → Strip emails / phone numbers from text before logging.
  3. MAX_TOOL_CALLS          → Hard cap on how many tools one conversation can trigger.

Design principle: every guardrail is a pure function (input → decision/output).
No side effects, no state. This makes them trivial to unit-test and reason about.
"""

import re

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Max tool calls per conversation (defense against cost abuse / loops).
# This is enforced in graph.py via a tool-call counter, separate from
# LangGraph's recursion_limit (which counts node visits, not tool calls).
MAX_TOOL_CALLS = 8

# Topics / patterns that should be refused even if the LLM "wants" to help.
# These are explicit, hard-coded refusal rules — defense in depth on top of
# the system prompt. If the LLM gets talked out of refusing, this catches it.
OUT_OF_SCOPE_PATTERNS = [
    # Code generation — support bot is not a coding tool
    r"\b(write|generate|code|script).*(python|javascript|sql|bash)\b",
    # Creative writing — way off-scope
    r"\b(write|compose|create).*(poem|song|essay|story|joke)\b",
    # Competitor comparisons — we don't recommend rivals
    r"\b(asana|trello|monday\.com|jira|notion|clickup)\b",
    # Regulated advice — liability risk
    r"\b(medical|legal|tax|financial)\s+advice\b",
]


# Patterns to redact from logs / outbound-facing text (PII).
PII_PATTERNS = {
    # TODO 2: Add regex patterns to find PII. Each pattern maps to a
    #         replacement string.
    #
    # Suggestions:
      "email": (r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]"),
      "phone_us": (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]"),
      "ipv4":  (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP]"),
    #
    # Note: these are intentionally simple. Real PII detection is a hard
    # ML problem (presidio, spaCy NER, etc.). For a portfolio project, a
    # regex baseline is honest — just be ready to explain its limits.
}


# ---------------------------------------------------------------------------
# Guardrail 1 — refusal for out-of-scope questions
# ---------------------------------------------------------------------------

def is_out_of_scope(text: str) -> tuple[bool, str | None]:
    """Check if a user message matches any out-of-scope pattern.

    Returns (True, matched_pattern) if it does, else (False, None).
    The matched pattern is returned so the caller can log WHY it refused —
    important for debugging and for telling the user a useful message.
    """
    # TODO 3: Iterate through OUT_OF_SCOPE_PATTERNS, do a case-insensitive
    #         search on `text`. If any pattern matches, return (True, pattern).
    #         Otherwise return (False, None).
    #
    # Hint: re.search(pattern, text, re.IGNORECASE)
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return (True, pattern)
    return (False, None)


REFUSAL_MESSAGE = (
    "I'm the TaskFlow support assistant — I can help with questions about "
    "TaskFlow's features, pricing, your account, or your support tickets. "
    "I can't help with that particular request, but I'd be happy to help "
    "with anything TaskFlow-related."
)


# ---------------------------------------------------------------------------
# Guardrail 2 — PII redaction for logs
# ---------------------------------------------------------------------------

def redact_pii(text: str) -> str:
    """Replace PII matches in text with their corresponding placeholders.

    Use this BEFORE printing or logging anything that may contain user data.
    Does not modify the agent's internal state — only the surface form
    that gets exported (logs, error messages, traces).
    """
    # TODO 4: For each (pattern, replacement) in PII_PATTERNS.values(),
    #         use re.sub(pattern, replacement, text) to replace matches.
    #         Return the cleaned text.
    #
    # Hint: re.sub(pattern, repl, text)  — apply each one in turn.
    for pattern, replacement in PII_PATTERNS.values():
        text = re.sub(pattern, replacement, text)
    return text



# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Out-of-scope checks ===")
    test_inputs = [
        "How much does the Pro plan cost?",                     # OK
        "Write me a Python script to scrape websites",          # should refuse
        "Compose a poem about kanban boards",                   # should refuse
        "Is Asana better than TaskFlow?",                       # should refuse (competitor)
        "Can you give me legal advice about my contract?",      # should refuse
        "Show me my open tickets",                              # OK
    ]
    for t in test_inputs:
        refused, why = is_out_of_scope(t)
        verdict = f"REFUSE ({why})" if refused else "ALLOW"
        print(f"  [{verdict:35}] {t}")

    print("\n=== PII redaction ===")
    samples = [
        "User william.johnson@example.org reported a bug.",
        "Call me at 415-555-1234 if needed.",
        "The request came from IP 192.168.1.42.",
        "TF-1101 is a perfectly normal ticket ID and shouldn't get touched.",
    ]
    for s in samples:
        print(f"  before: {s}")
        print(f"   after: {redact_pii(s)}\n")
