# Project Handoff Document

> **Read me first if you're a new Claude session joining this project.**

## What this project is

**TaskFlow Support Agent** — a portfolio project building a customer support chatbot
for a fake SaaS called "TaskFlow" (a Trello/Asana-like PM tool). Goal: land a
Junior MLE / AI Agent role.

The agent will use:
- **RAG** over invented TaskFlow help docs (answering product questions)
- **MongoDB tools** for looking up user/ticket data
- **LangGraph** to orchestrate everything
- **FastAPI + minimal UI** to serve it
- **Eval + observability + Docker + CI** to make it portfolio-worthy

## Tech stack

- **LLM provider:** Groq (free tier). `llama-3.3-70b-versatile` for RAG, `meta-llama/llama-4-scout-17b-16e-instruct` for tool-calling agent
- **Vector DB:** ChromaDB (local, persistent)
- **Embeddings:** `all-MiniLM-L6-v2` (ChromaDB default, 384-dim)
- **Database:** MongoDB Community Server, local, database name `taskflow`
- **Agent framework:** LangGraph + LangChain core
- **Observability:** Langfuse v3 (self-hosted via docker-compose) + langfuse v4 Python SDK
- **Python:** 3.11, managed via `uv`

## Project structure

```
taskflow-support-agent/
├── agent/
│   ├── llm.py              # Groq wrapper — chat(messages, ...) -> str
│   ├── tools.py            # 5 tool functions + Pydantic schemas + LangChain wrappers
│   ├── guardrails.py       # is_out_of_scope, redact_pii, MAX_TOOL_CALLS
│   └── graph.py            # ReAct agent: guard_input → agent → tools loop, MemorySaver, Langfuse
├── rag/
│   ├── ingest.py           # Load docs → chunk → embed → ChromaDB
│   ├── retrieve.py         # retrieve(query, k) -> list of chunks
│   └── answer.py           # RAG answerer (retrieve → stuff → LLM → answer)
├── data/
│   ├── docs/               # 21 markdown files — the RAG corpus
│   ├── chroma_db/          # Persistent vector DB (gitignored)
│   └── seed_mongo.py       # Seeder: 50 users, 200 tickets, 500 events, 20 subs
├── eval/
│   ├── golden.jsonl        # 25 hand-written Q/A pairs (RAG eval)
│   ├── run_eval.py         # LLM-as-judge eval (faithfulness + relevancy)
│   ├── agent_scenarios.jsonl  # 15 scripted agent conversations (Day 17)
│   ├── run_agent_eval.py   # Trajectory + endpoint eval, deterministic assertions
│   └── results.json        # Latest eval output
├── docker-compose.yml      # Langfuse v3 stack (web + worker + postgres + clickhouse + redis + minio)
├── app/                    # Not yet used (FastAPI later)
├── tests/                  # Not yet used
├── notebooks/              # Not yet used
├── learning/concepts/      # User's self-notes on concepts learned
└── .env                    # GROQ_API_KEY + LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST (gitignored)
```

## Days completed

| Day | Focus | Status |
|-----|-------|--------|
| 1 | Repo, env, uv, folders, licenses | ✅ |
| 2 | Invent TaskFlow + write 21 help docs | ✅ |
| 3 | MongoDB seeder (local Mongo, NOT Atlas) | ✅ |
| 4 | Groq LLM wrapper (`chat()`) | ✅ |
| 5 | Minimal LangGraph agent (one node, no tools) | ✅ |
| 6 | Reflection/cleanup — skipped deliberately | ⏭️ |
| 7 | Chunking + embedding (201 chunks into ChromaDB) | ✅ |
| 8 | Retrieval function + manual testing | ✅ |
| 9 | RAG answerer with source citations | ✅ |
| 10 | Eval v1 (LLM-as-judge, 25 golden questions) | ✅ |
| 11 | Improve retrieval (chunk size, hybrid, reranking) | ✅ (reranker skipped) |
| 12 | (skipped — rolled into Day 11) | ⏭️ |
| 13 | Tool interface (function calling, Pydantic schemas) | ✅ |
| 14 | ReAct agent with LangGraph tool-calling loop | ✅ |
| 15 | Short-term conversation memory (MemorySaver checkpointer) | ✅ |
| 16 | Guardrails (refusal, PII redaction, max-tool-calls) | ✅ |
| 17 | Agent eval — 15 scripted scenarios, trajectory + endpoint assertions | ✅ |
| 18 | Observability — self-hosted Langfuse v3 via docker-compose, callback tracing | ✅ |
| 19 | FastAPI serving layer — /health, /chat, /chat/stream (SSE), /feedback, demo UI | ✅ |
| 20 | (skipped — Streamlit UI replaced by HTML+SSE in Day 19) | ⏭️ |
| 21 | (deferred — tests + CI moved to Day 23) | ⏭️ |
| 22 | Docker — multi-stage Dockerfile, env-var refactor, app service in compose | ✅ |
| 23 | CI/CD — ruff + pytest + GitHub Actions (lint + test + docker build) | ✅ |
| 24 | Cloud deploy — HF Spaces + Atlas + Langfuse Cloud, image slim, real README | ✅ |
| 25+ | Demo video, persistent checkpointer, image-size pass, scheduled agent eval | ⏳ |

### Day 11 progress so far

**Done:**
- Fixed default-argument bug in `rag/retrieve.py` — `collection_name` default was captured at def time, silently invalidating collection switching. Now read inside the function body via `TASKFLOW_COLLECTION` env var.
- Added `hit@k` retrieval-only metric to `eval/run_eval.py` (cheap, no LLM).
- Added `retrieval_only=True` mode to skip LLM judges during sweeps (saves Groq tokens — 100k TPD cap).
- Added `retriever="dense"|"hybrid"` kwarg to `run_eval` for dispatching.
- Added skip-if-exists guard in `eval/sweep.py` to avoid re-ingesting unchanged collections.
- Chunk-size sweep (5 configs, retrieval-only): baseline 500/50 wins with `hit@3=1.00`. All configs hit 1.00 on `hit@5` → **metric ceiling hit**, test set too easy to discriminate.
- Built `rag/retrieve_hybrid.py` — BM25 (`rank-bm25`) + dense + RRF fusion (k=60). Lazy-builds BM25 index in-memory from Chroma on first call, cached per collection.
- Dense vs hybrid head-to-head (full eval with judges): **hybrid REGRESSED.** Dense `hit@3=1.00, faith=5.00, relev=4.88`. Hybrid `hit@3≈0.80` (4 misses), faithfulness also dropped on Q1 (5→3) because wrong context caused LLM to hallucinate a monthly price. Clean causal chain: bad retrieval → bad answer.
- Wrote up findings + observations in `eval/RETRIEVAL_EXPERIMENTS.md`.

**In progress:**
- `rag/rerank.py` scaffolded with 4 TODOs for cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`). **Not yet filled in, not yet smoke-tested, not yet wired into sweep.**
- Hybrid+rerank eval not yet run.
- Final observations not yet consolidated.

**Key Day 11 finding (interview-gold):**
> Hybrid retrieval is a tool, not a default. On a small, clean, single-domain corpus, dense was already at the ceiling and BM25 added noise — regressing both retrieval and faithfulness. Hybrid's real value shows up on noisy, heterogeneous corpora with rare tokens and mixed query styles.

### Files added/modified on Day 11
- `rag/retrieve.py` — default-arg bug fix
- `rag/retrieve_hybrid.py` — new, dense + BM25 + RRF, fully working
- `rag/rerank.py` — new, **skeleton only, TODOs unfilled**
- `eval/run_eval.py` — `retrieval_only` + `retriever` kwargs, `hit@k` metric
- `eval/sweep.py` — `CONFIGS` list, collection skip-if-exists, retriever dispatch
- `eval/RETRIEVAL_EXPERIMENTS.md` — results + observations
- `learning/concepts/project_interview.md` — new, 34 interview questions across 7 sections for self-study

## Important project decisions (don't revisit)

1. **TaskFlow is a plain PM tool** — NO built-in AI features. We deliberately
   removed that to avoid "two agents in one project" confusion. See
   `data/docs/00-product-brief.md` "Things TaskFlow is NOT" section.
2. **MongoDB is local (not Atlas)** — user has Community Server installed as
   a Windows service running on `localhost:27017`. Connection works.
3. **Groq over OpenAI** — free tier, fast, no credit card. Good enough for a
   support agent.
4. **`chat()` abstraction layer** — `agent/llm.py` hides the Groq SDK so we
   can swap providers later without touching the rest of the code.
5. **No text-to-SQL/MongoDB** — agent will use **pre-written Python tool
   functions**, not generate queries. More realistic, less risky.
6. **ChromaDB over alternatives** — simplest for learning. Document the why
   in `learning/concepts/` (user already has notes on this).
7. **Product brief may pollute RAG** — noted on Day 10; the
   `00-product-brief.md` is internal. Consider filtering it out of ingestion
   later.
8. **Eval = LLM-as-judge via Groq** — not RAGAS. Same concept, fewer deps.
9. **Judges are noisy** — a high judge score isn't proof of quality. Always
   spot-check reasoning. Low scores surface real problems.

## Collaboration style with this user

Stored in memory, but highlight:

- **User is learning AI/ML for a Junior MLE role.** Keep explanations
  concrete and interview-relevant. Use analogies to things they know.
- **Guide, don't dump code.** For anything where writing it themselves
  teaches something (logic, pipelines, algorithms), give a skeleton with
  TODOs + hints. For scaffolding/boilerplate (license, fake data, config),
  just write it directly when they ask.
- **Concepts first, code second.** Always explain *why* before *how*.
- **Be honest about tradeoffs.** Especially: "this is boilerplate with no
  learning value, I'll just write it" vs. "this is where the real learning
  happens, you should try it yourself first."
- **Be brief in responses.** The user's context is finite; dense explanations
  beat long ones. Use tables and structure.
- **Don't invent Microsoft Teams integration** 😄 — the docs explicitly say
  it's NOT supported. Same for desktop app, SMS 2FA, multi-assignee tasks.

## Open issues / known weaknesses

- `00-product-brief.md` is getting indexed into ChromaDB even though it's an
  internal doc. Causes the agent to cite it when it shouldn't (seen in Day 10
  eval for "I need to speak with a human").
- RAG system prompt says "always cite source" even when answering "I don't
  know" — leads to contradictory outputs.
- Eval judges occasionally hallucinate justifications. Known limitation of
  LLM-as-judge.

## User's current state

End of Day 24. **The agent is live in production** at https://huggingface.co/spaces/jinyuuda/taskflow-support-agent. Three external services replace the local stack: MongoDB Atlas (free M0 tier) for user/ticket data, Langfuse Cloud for observability, Groq Cloud for LLM. Image slimmed from ~3 GB → ~1.2 GB by dropping `sentence-transformers` (and torch transitively) — the reranker that needed it was deferred. README is now a recruiter-ready project doc with Mermaid architecture, tech-stack rationale, design-decision callouts, and a link to the live demo. PRs #1 (CI) and #2 (deploy) merged into main.

### Days 13–15 summary

**Day 13 — Tool interface:**
- Created `agent/tools.py` with 5 tool functions + Pydantic input schemas
- Tools: `search_docs`, `get_user`, `list_user_tickets`, `create_ticket`, `escalate_to_human`
- Each tool has a plain Python function + Pydantic model + docstring
- `TOOLS` registry maps name → (function, schema)
- Added LangChain `@tool` wrappers (`LANGCHAIN_TOOLS` list) for LangGraph integration

**Day 14 — ReAct agent:**
- Rewrote `agent/graph.py` as a ReAct-style agent with tool-calling loop
- Architecture: START → agent → should_continue? → tools → agent → ... → END
- Uses `ChatGroq` + `bind_tools()` instead of the old `chat()` wrapper
- `ToolNode` executes tool calls automatically
- System prompt defines persona + rules (always search docs first, always look up user, etc.)
- `recursion_limit=10` as safety net against infinite loops

**Model change:** Switched from `llama-3.3-70b-versatile` to
`meta-llama/llama-4-scout-17b-16e-instruct` for graph.py because Llama 3.3
on Groq has a tool-calling format bug (outputs XML-style `<function=...>`
instead of proper JSON). The old `chat()` wrapper in `llm.py` still uses
Llama 3.3 (doesn't do tool calling, so not affected).

**Smoke test results:**
- Product question ("Pro plan price?") → agent called search_docs → correct answer with source
- Account question ("tickets for X") → agent called get_user → then list_user_tickets → formatted 3 tickets

**Day 15 — Conversation memory:**
- Added `MemorySaver` checkpointer to `graph.compile(checkpointer=...)`
- All `.invoke()` calls now require `config={"configurable": {"thread_id": ...}}`
- Built observability helper (`send()`) that prints which tools were called per turn
  — this is the proof that memory works (no tool calls = answered from history)
- 3 tests pass:
  - **Test 1** (same thread): turn 1 fetches docs, turns 2 & 3 answer from memory (no tool calls)
  - **Test 2** (new thread): same follow-up question fails to resolve "that" — confirms thread isolation
  - **Test 3** (account flow): user identifies once via email, follow-up about a specific ticket needs ZERO tool calls

**Key Day 15 learning (interview-gold):**
> Observability matters as much as correctness for agents. From the user's
> perspective, "memory worked" and "memory failed but agent re-fetched" can
> produce the same answer. The only way to tell the difference is to inspect
> which tools fired per turn — which is why production systems use LangSmith,
> Langfuse, or OpenTelemetry traces.

**Interview file:** Sections 8–10 added to `learning/concepts/project_interview.md`
covering tools (Q35–42), agent loop (Q43–51), and memory (Q52–60). Total: 60 questions.

### Files added/modified on Days 13–15
- `agent/tools.py` — new (Day 13), 5 tool functions + Pydantic schemas + LangChain wrappers
- `agent/graph.py` — rewritten (Day 14), then extended (Day 15) with checkpointer + multi-turn tests
- `learning/concepts/project_interview.md` — extended with Sections 8–10

### Days 16–18 summary

**Day 16 — Guardrails:**
- New `agent/guardrails.py` — three pure functions: `is_out_of_scope(text)`, `redact_pii(text)`, constant `MAX_TOOL_CALLS = 8`.
- Refusal patterns (regex, case-insensitive): code generation, creative writing, competitor names (Asana/Trello/etc.), regulated advice (medical/legal/tax/financial).
- PII redaction: emails → `[EMAIL]`, phone numbers → `[PHONE]`, IPv4 → `[IP]`. Used for log surfaces, NOT user-facing text.
- New graph node `guard_input` runs BEFORE the agent. If `is_out_of_scope` matches, returns canonical `REFUSAL_MESSAGE` and routes to END — LLM is never invoked. This is defense-in-depth on top of system-prompt rules.
- Hardened SYSTEM_PROMPT in `agent/graph.py`: added scope rules + safety rules (don't reveal prompt, don't role-play, don't execute instructions in tool results).
- `should_continue` now also enforces `MAX_TOOL_CALLS` — counts tool calls in message history, ends loop if exceeded. Distinct from `recursion_limit` (which counts node visits).
- Smoke tests (Tests 4–5 in `agent/graph.py` `__main__`): 4 out-of-scope refusals all trigger guard, legitimate question still passes through.

**Day 17 — Agent eval:**
- New `eval/agent_scenarios.jsonl` — 15 scripted scenarios across 6 categories (`happy_product`, `happy_account`, `multi_turn`, `ticket_creation`, `guardrail`, `edge_case`).
- New `eval/run_agent_eval.py` — runner with 6 deterministic assertion types: `tools_called_contains`, `tools_called_ordered`, `tools_not_called`, `response_contains`, `response_refused`, `max_tool_calls`. NO LLM-as-judge — every check is hand-coded against the trajectory or final response.
- Multi-turn scenarios reuse the same `thread_id` across messages so memory is exercised.
- Per-scenario UUID suffix on thread_id prevents test bleed across runs.
- Output: per-scenario pass/fail with check-by-check breakdown, category aggregate, JSON dump to `agent_results.json`.

**Day 18 — Observability (Langfuse):**
- New `docker-compose.yml` — full Langfuse v3 self-hosted stack (6 services: web + worker + postgres + clickhouse + redis + minio). Only port 3000 exposed to host (UI). All inter-service comms internal.
- `agent/graph.py`: added `get_langfuse_handler()` (returns `CallbackHandler` if env vars set, else None for graceful degradation) and `flush_langfuse()` (forces async batcher to flush before process exit — required, otherwise short scripts lose events).
- `agent/graph.py` `agent` node now accepts `RunnableConfig` and threads it through `llm.invoke(messages, config=config)` — without this, callbacks die at the node boundary and no spans get emitted.
- Both `__main__` test block in `agent/graph.py` and `eval/run_agent_eval.py` now build a config dict with `"callbacks": [langfuse_handler]` and pass it to every invoke. Each scenario gets `metadata.scenario_id` + `run_name` for filtering in the Langfuse UI.
- Verified end-to-end: agent run produces nested traces (`LangGraph` → `guard_input` → `agent` (LLM call) → `tools` → ...) with token counts + latency per span.

**Key Day 16–18 learnings (interview-gold):**
> **Guardrails:** "Defense in depth" isn't a buzzword for agents — every layer (system prompt, code-level check, tool-call cap) handles a different failure mode. Refusal in the system prompt is necessary but not sufficient: prompt injection can override it. A code-level check that runs BEFORE the LLM is the only thing that survives a successful injection.
>
> **Agent eval vs RAG eval:** RAG evals need LLM-as-judge because answer correctness is fuzzy. Agent evals don't — the trajectory (which tools fired, in what order) is fully deterministic and assertable. Use the cheaper, faster, transparent test whenever you can.
>
> **Observability:** "It worked in eval" and "it works in prod" are different claims. Without traces, you debug agents by re-running and hoping. With traces, you click on yesterday's failure and see the exact prompt the LLM saw, the exact tool result it got, the latency of each step, and the token cost. This is the difference between "vibes-based debugging" and an engineering discipline.

**Stack pain points worth remembering:**
- Langfuse v2 Python SDK doesn't work with langchain 1.x (imports removed). Must use Langfuse v3+ server + v4+ SDK.
- LangGraph callbacks DO NOT auto-propagate from `graph.invoke(config=...)` into node functions if the node calls `llm.invoke(messages)` — the node must accept `RunnableConfig` and pass it through explicitly.
- Langfuse SDK is async/buffered. Always call `client.flush()` before script exit or your traces silently disappear.
- Old/orphan docker containers from earlier compose attempts can hold the port even after `docker compose down` — they share host port mappings but different service names. Check `docker ps -a` first.

### Files added/modified on Days 16–18
- `agent/guardrails.py` — new (Day 16)
- `agent/graph.py` — extended with `guard_input` node, hardened SYSTEM_PROMPT, MAX_TOOL_CALLS enforcement, Langfuse handler/flush, `RunnableConfig` thread-through
- `eval/agent_scenarios.jsonl` — new (Day 17), 15 scenarios
- `eval/run_agent_eval.py` — new (Day 17), runner + assertion checker, Langfuse-instrumented
- `docker-compose.yml` — new (Day 18), Langfuse v3 stack
- `pyproject.toml` — added `langchain-groq>=1.0.0`, `langfuse>=3.0.0`; loosened `groq` pin for langchain-groq compatibility
- `.env` — added `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`

### Day 19 summary

**FastAPI serving layer:**
- New `app/` package: `schemas.py` (Pydantic request/response models), `deps.py` (DI providers + health checks), `main.py` (FastAPI app + 5 routes), `static/index.html` (one-page chat UI).
- Routes: `GET /` (UI), `GET /health` (mongo + chroma pings), `POST /chat` (non-streaming, returns ChatResponse), `POST /chat/stream` (SSE streaming), `POST /feedback` (👍/👎 → Langfuse score).
- `lifespan` async context manager: warms `get_graph()` singleton on startup, calls `flush_langfuse()` on shutdown — fixes the Day 18 "short-lived process loses traces" issue at the FastAPI level.
- DI providers (`get_graph`, `get_langfuse`, `get_langfuse_client`) cached via `@lru_cache(maxsize=1)` so the compiled graph + Langfuse handler/client are process-wide singletons.
- `request_id == Langfuse trace_id` design: `_new_request_id()` uses `Langfuse.create_trace_id()` (32-char W3C hex). Both `/chat` and `/chat/stream` wrap `graph.ainvoke` / `astream_events` in `langfuse_client.start_as_current_observation(trace_context={"trace_id": request_id}, as_type="chain")`. The langchain CallbackHandler emits child spans inside that context, so the whole trace shares our request_id.
- `/feedback` calls `langfuse_client.create_score(trace_id=req.request_id, name="user_feedback", value=1.0|0.0, data_type="NUMERIC")` and immediately `flush()`s so the score appears in the UI without batcher delay.
- SSE wire format: `data: <json>\n\n` per frame. Frame types: `token`, `tool_start`, `tool_end`, `done` (final, carries `request_id` for /feedback). `_run_graph()` wraps `astream_events(version="v2")` in the Langfuse span; `event_stream()` filters and formats events.
- **Streaming edge case fix:** when `guard_input` refuses, no LLM is called → zero `on_chat_model_stream` events → empty bubble. Solution: count tokens in the loop; if `tokens_streamed == 0`, call `graph.aget_state({"configurable": {"thread_id": ...}})` and emit the last AIMessage's content as a single token frame before `done`.
- Demo UI (`app/static/index.html`): vanilla HTML/JS, dark theme. `thread_id = crypto.randomUUID()` per page load. Consumes `/chat/stream` via `fetch` + `ReadableStream` + manual SSE parser (EventSource only supports GET). Each assistant bubble gets 👍/👎 buttons that POST to `/feedback`.

**Stack pain points worth remembering:**
- Langfuse v4 SDK is OpenTelemetry under the hood. The v3 trick of pinning trace ID via `metadata={"langfuse_trace_id": ...}` is silently ignored in v4. The replacement is `start_as_current_observation(trace_context={"trace_id": ...})` — and the method is named `start_as_current_observation`, NOT `start_as_current_span` (that misnomer cost us 30 minutes).
- When SDK docs disagree with reality, `dir(client)` and `inspect.signature(client.method)` are the source of truth. We discovered the right method name and the `TraceContext` TypedDict shape (`{"trace_id": str}`) by introspecting the live client.
- PowerShell's `curl` is aliased to `Invoke-WebRequest` and mangles `\"` escapes in single-quoted strings. Use `Invoke-RestMethod` with `ConvertTo-Json`, or pipe JSON via stdin to `curl.exe --data-binary "@-"`.
- LangGraph's `astream_events(version="v2")` requires `async for` (it's itself an async generator). The agent makes multiple LLM calls per turn (decide-tool → answer-compose), so token frames arrive in two bursts with a tool gap between them — that's correct, not a bug.
- Mount order matters for `StaticFiles`: register specific routes BEFORE the catch-all `app.mount(...)`, otherwise the static handler shadows them.

**Key Day 19 learnings (interview-gold):**
> **Trace-ID pinning is the feedback loop.** Without it, `/feedback` has no way to find the right trace — Langfuse auto-generates a trace_id the client never sees. The whole UX of "click 👎, see it on the trace in Langfuse" hinges on `request_id == trace_id`. Same pattern OpenAI uses with `response.id` for their feedback API.
>
> **Streaming UX requires zero-token-path awareness.** Any code path that returns an answer WITHOUT calling the LLM bypasses the token stream. The guard_input refusal exposed this. If your client expects tokens, you have to detect zero-token completion and synthesize a frame from the final state — otherwise the UI shows an empty bubble.
>
> **SDK introspection beats docs when docs lag.** Live `dir()` and `inspect.signature()` found `start_as_current_observation` and the exact `create_score` kwargs faster than searching docs would have. First-class debugging tool, not a fallback.

### Files added/modified on Day 19
- `app/__init__.py` — new (package marker)
- `app/schemas.py` — new, `ChatRequest/Response`, `FeedbackRequest`, `HealthResponse`
- `app/deps.py` — new, `get_graph`, `get_langfuse`, `get_langfuse_client`, `check_mongo`, `check_chroma`
- `app/main.py` — new, FastAPI app with lifespan + 5 routes (/, /health, /chat, /chat/stream, /feedback)
- `app/static/index.html` — new, one-page demo chat UI (vanilla JS, ~180 lines)
- `agent/graph.py` — added `get_langfuse_client()` exposing the raw client for /feedback's `create_score`

### Day 22 summary

**Architecture deviations from original spec (intentional):**
- No separate UI container — UI is one HTML file served by FastAPI's `GET /` from Day 19. Splitting it into nginx would be 2 containers for 1 feature.
- No Chroma server container — using ChromaDB as an embedded library (`PersistentClient`) with a bind-mounted persistent store. Embedded is correct at single-replica scale; server mode would add a network hop with no scaling win.
- MongoDB stays on the host (Windows Service) — reached via `host.docker.internal:27017`. Avoids re-seeding into a containerized Mongo. Documented as a "swap to compose-managed Mongo before deploy" debt.

**Step 1 — env-var refactor (12-factor config):**
- Touched 7 files: `agent/tools.py`, `app/deps.py`, `rag/{retrieve,retrieve_hybrid,ingest}.py`, `eval/sweep.py`, `data/seed_mongo.py`.
- Pattern: `MONGO_URI = os.getenv("MONGO_URI", <previous_hardcoded>)` and same for `CHROMA_PATH`. Defaults preserved → host behavior unchanged.
- Why this matters: hardcoded `localhost:27017` and `data/chroma_db` would only work in dev. With env vars, the same image runs anywhere as long as you supply the right config.

**Step 2 — Dockerfile (multi-stage):**
- Builder stage: `python:3.11-slim` + uv from `ghcr.io/astral-sh/uv:latest`. Installs deps into `/app/.venv`. Layer-cached: deps install runs only when `pyproject.toml` or `uv.lock` change.
- Runtime stage: fresh `python:3.11-slim` + `libgomp1` (apt) + the venv copied from builder. Final image ~3 GB (most of it = torch + onnxruntime + sentence-transformers, all required).
- ENV: `PATH=/app/.venv/bin:$PATH`, `PYTHONUNBUFFERED=1` (so `docker logs` shows output immediately), `PYTHONDONTWRITEBYTECODE=1`.
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000` — `0.0.0.0` is mandatory inside a container; `127.0.0.1` would only listen on the container's loopback, unreachable from the bridge network.

**Step 2 — `.dockerignore`:**
- Excludes `.venv/`, `__pycache__/`, `.git/`, `.env*`, `data/chroma_db/` (bind-mounted), `notebooks/`, `learning/`, `HANDOFF.md`, eval result JSONs.
- Critical: `.env` MUST be ignored — images get pushed to registries, leaked secrets are recoverable forever from old layers even if removed in newer layers.

**Step 3 (skipped) — standalone smoke test:**
- Originally planned `docker run --env-file .env -e MONGO_URI=... -e LANGFUSE_HOST=... -v ./data:/app/data taskflow-agent` to verify the image works in isolation.
- Skipped because Docker Desktop went unhealthy mid-process; image blob got corrupted during a Desktop restart. Pruned + moved Docker storage from C: to E: (more disk space) and went straight to Step 4 instead. Step 4 verifies the same thing through compose with one less debugging round.

**Step 4 — `docker-compose.yml` extension:**
- Added `app:` service: `build: .` (uses local Dockerfile), `image: taskflow-agent` (tag), `depends_on: langfuse-web`, ports `8000:8000`.
- `env_file: - .env` for secrets (Groq + Langfuse keys), `environment:` block for compose-network-specific overrides (`MONGO_URI=mongodb://host.docker.internal:27017`, `LANGFUSE_HOST=http://langfuse-web:3000`).
- `extra_hosts: - "host.docker.internal:host-gateway"` — makes `host.docker.internal` work on Linux too (no-op on Win/Mac, but defensive).
- Bind mount `./data:/app/data` for ChromaDB index. Named volume `hf_cache:/root/.cache/huggingface` for sentence-transformers model cache (survives `docker compose down`, first-start downloads happen once).
- Verified: `docker compose up --build -d` brings up 7 containers, `/health` returns `mongo:true,chroma:true`, chat UI works at `http://localhost:8000/`, traces appear in Langfuse, /feedback scores show on traces.

**Stack pain points worth remembering:**
- **Image size 3 GB, not 400 MB.** ML wheels are huge: torch ~800 MB, onnxruntime ~300 MB, sentence-transformers + langchain stack add the rest. Multi-stage saved ~1 GB vs single-stage but you can't slim past the deps. Real optimization later: CPU-only torch wheel (`pip install torch --index-url https://download.pytorch.org/whl/cpu`), drop sentence-transformers if Chroma's default suffices.
- **Build time was 2.5 hours first build** — Windows + WSL2 + huge wheels + slow disk. Subsequent rebuilds use layer cache and are much faster IF source-only changes (deps stay cached).
- **`--env-file` vs Python `dotenv` strictness:** Docker's `--env-file` rejects spaces around `=`. The line `GROQ_API_KEY = "..."` (works fine in dotenv) crashed `docker run` with "variable 'GROQ_API_KEY ' contains whitespaces". Standard convention: no spaces.
- **`docker compose restart` does NOT re-read `env_file`.** It restarts the process inside the existing container. To pick up new `.env` values you must `docker compose up -d --force-recreate <service>` or `docker compose down && up`. Famous junior-trip-up.
- **Docker Desktop disk on C:** runs out of space fast on a small SSD. Move it to a bigger drive in Settings → Resources → Advanced → Disk image location. The move wipes Docker data, so prune first.
- **Docker Desktop instability** during long builds — the WSL2 backend can corrupt image blobs if it's restarted mid-extract. Symptoms: `input/output error` on a blob hash that exists in `docker images`. Fix: rm + rebuild.

**Key Day 22 learnings (interview-gold):**
> **Dockerfile vs docker-compose.yml is the standard interview question.** A Dockerfile builds ONE image. Compose orchestrates a multi-service stack — which images, what env vars, what ports, what volumes, how they network. Complementary, not substitutes. Our project: Dockerfile builds the agent image; compose runs it alongside 6 off-the-shelf images (Postgres, Redis, ClickHouse, MinIO, Langfuse-web, Langfuse-worker).
>
> **Container networking has three rules:** (1) `--host 0.0.0.0` mandatory inside containers, (2) `localhost` inside a container = the container itself, NOT the host — use `host.docker.internal` to reach the host's network on Win/Mac, (3) services in the same compose network find each other by service name (Docker's embedded DNS), no IP addresses needed.
>
> **Layer caching is the difference between a 30s rebuild and a 30min rebuild.** Always `COPY pyproject.toml uv.lock` BEFORE `COPY . .`. The deps layer only invalidates when those two files change, not on every source edit.
>
> **Multi-stage builds let you ship without build tools.** Stage 1 has uv, gcc, dev headers. Stage 2 (the final image) has only Python + the installed venv + the runtime libs. Saves ~1 GB and reduces attack surface — no compilers in production.

### Files added/modified on Day 22
- `Dockerfile` — new, multi-stage build (builder + runtime), uv-based dep install, `libgomp1` runtime dep
- `.dockerignore` — new, excludes secrets (`.env*`), large state (`data/chroma_db`), VCS, dev artifacts
- `docker-compose.yml` — extended with `app:` service (build local Dockerfile, env_file + overrides, bind mount + named volume) + `hf_cache` volume
- `agent/tools.py` — `MONGO_URI` and `DB_NAME` from env vars (defaults preserved)
- `app/deps.py` — `check_mongo` and `check_chroma` read env vars
- `rag/retrieve.py`, `rag/retrieve_hybrid.py`, `rag/ingest.py`, `eval/sweep.py` — `CHROMA_DIR` from env var
- `data/seed_mongo.py` — `MONGO_URI` and `DB_NAME` from env vars
- `.env` — normalized line 1 (removed spaces around `=` so Docker's `--env-file` accepts it)
- `learning/concepts/project_interview.md` — added Section 14 (FastAPI, Q85–103) and Section 15 (Docker, Q104–124)

### Day 23 summary

**Branching strategy used (worth keeping for future days):**
- Created feature branch `day-23-ci`
- Three logical commits (`chore:` ruff config + auto-fixes, `test:` pytest suite, `ci:` GHA workflow) — clean history, each commit independently revertable
- Two `fix(ci):` commits for issues surfaced by the first run (format misses, lowercase-tag rule, runner disk space)
- Opened PR #1, squash-merged into main with branch deletion

**Step 2 — ruff config (one tool replaces flake8 + black + isort + pyupgrade):**
- `[tool.ruff]` block in `pyproject.toml` — line length 100, target py311, exclude `.venv` / `data/chroma_db` / `notebooks`
- Rule families: E/W (pycodestyle), F (pyflakes — real bugs), I (import order), B (bugbear), UP (pyupgrade)
- `[tool.ruff.lint.flake8-bugbear].extend-immutable-calls` whitelists FastAPI's `Depends`, `Query`, `Path`, `Body`, `Header` — otherwise B008 fires on every endpoint signature (the standard FastAPI pattern would be marked as "function call in default")
- Per-file ignores: `tests/*` relaxes F401/F811 (unused-fixture noise); `eval/*` relaxes E/B (experiment scripts); `rag/rerank.py` ignores F841 (skeleton with unfilled TODOs per HANDOFF)
- Auto-fix pass touched 17 files: import sorting, `datetime.UTC` modernization, `zip(..., strict=False)` to silence B905
- Manual fixes for E402: per-line `# noqa` on intentional late imports in `agent/graph.py` (Langfuse below explanatory comment block) and `agent/tools.py` (`@tool` decorator wraps the functions defined above)

**Step 3 — pytest suite (33 tests, ~0.5s wall):**
- `tests/conftest.py`: sets `GROQ_API_KEY=test-key-not-used` BEFORE importing app code (agent.graph constructs ChatGroq at module level). `FakeGraph` class with `async def ainvoke()` returning canned messages. `client` fixture wraps FastAPI's `TestClient`, monkeypatches `app.main.get_graph` (for the lifespan call) AND sets `app.dependency_overrides[get_graph] = lambda: fake_graph` (for the `Depends` calls in endpoints) — belt and suspenders.
- `tests/test_guardrails.py`: 9 tests. Parametrized in/out-of-scope cases, case-insensitivity, PII redaction (email/phone/IPv4 with idempotency check on clean text).
- `tests/test_helpers.py`: 5 tests for `_extract_turn_tools`. Most important: `test_only_walks_back_to_last_human_message` — ensures past-turn tool calls don't bleed into the current turn's `tools_used`.
- `tests/test_api.py`: 9 endpoint tests. /health (ok + degraded), /chat (happy path + tool extraction + 422 validation for missing thread_id and empty message), /feedback (503 when langfuse_client is None + 422 for invalid rating + missing request_id).
- **Deliberately NOT in CI**: the agent eval (`eval/run_agent_eval.py`) — it costs Groq tokens and is flaky on LLM-judgment edges. Belongs in a scheduled / manual workflow, not on every PR.

**Step 5 — GitHub Actions workflow (`.github/workflows/ci.yml`):**
- Triggers: `push` on every branch + `pull_request` against main. Concurrency group cancels in-flight runs when newer commits land — saves runner minutes during rapid pushes.
- Three jobs run in parallel (wall time = slowest, not sum):
  - **lint**: `astral-sh/setup-uv@v5` + `uv sync --dev --frozen` + `uv run ruff check .` + `uv run ruff format --check .` (~35s)
  - **test**: same uv setup + `uv run pytest` with `GROQ_API_KEY=test-key-not-used` (~50s)
  - **docker-build**: `jlumbroso/free-disk-space@main` step strips ~10 GB of preinstalled tooling (Android SDK, .NET, Haskell), then `docker/build-push-action@v6` with `cache-from/to: type=gha` for layer caching across runs. Pushes to GHCR with both `:latest` and `:${{ github.sha }}` tags only on push to main, NOT on PRs (~30 min cold cache).
- Trick: GitHub usernames are mixed-case (`YudaLegend`) but OCI registry tags must be lowercase. A pre-step computes `IMAGE=ghcr.io/${GITHUB_REPOSITORY,,}` (bash lowercase expansion) into `$GITHUB_ENV` for use in subsequent steps.

**Issues surfaced by CI runs (the realistic experience):**

| Round | Failure | Root cause | Fix |
|---|---|---|---|
| 1 | `lint` failed at `ruff check` | Forgot to `ruff format` the new test files; `tests/test_api.py` and `tests/test_guardrails.py` had unsorted imports | `ruff check --fix` + `ruff format` |
| 1 | `docker-build` failed on `tags:` step | `invalid tag "ghcr.io/YudaLegend/...": repository name must be lowercase` | Add `IMAGE=ghcr.io/${GITHUB_REPOSITORY,,}` env step |
| 2 | `docker-build` crashed at 4m21s | "No space left on device" — 3 GB image + intermediates exhausted the runner's ~14 GB free | Add `jlumbroso/free-disk-space` step before checkout |
| 3 | All green ✓ | — | — |

**Stack pain points worth remembering:**
- **`asyncio_mode = "auto"`** in `[tool.pytest.ini_options]` makes any `async def test_*` runnable without `@pytest.mark.asyncio` decoration. Saves boilerplate.
- **FastAPI `app.dependency_overrides` is per-app, not per-test.** Always `app.dependency_overrides.clear()` in fixture teardown or earlier tests' overrides leak.
- **Lifespan handler runs for `TestClient`.** If your lifespan calls `get_graph()` directly (not via `Depends`), the dependency override won't reach it — must `monkeypatch.setattr("app.main.get_graph", ...)` separately.
- **GitHub Actions runners have ~14 GB free**, not 80 GB or whatever you remember. ML images often need disk-cleanup steps. `jlumbroso/free-disk-space` is the canonical workaround.
- **Docker registry tag rules are stricter than git ref rules.** Tags must be lowercase + alnum + `._/-`. Use `${VAR,,}` bash lowercase OR `tr '[:upper:]' '[:lower:]'` to convert.
- **`docker/build-push-action` with `cache-from/to: type=gha`** caches layers in GitHub's Actions cache (per-repo, ~10 GB limit). Subsequent builds skip dep installs when `pyproject.toml` and `uv.lock` are unchanged.
- **PR-from-fork has no GHCR write access** — that's why we gate the push step on `github.event_name == 'push' && github.ref == 'refs/heads/main'`. Forks still build (validates the Dockerfile parses) without trying to push.

**Key Day 23 learnings (interview-gold):**
> **CI is a contract, not a chore.** "Lint + test + build pass" means the code on this branch satisfies the team's quality bar. A failing CI BLOCKS merge — that's the gate's whole point. A vacuous CI ("pytest runs against an empty test suite") is decorative and worse than no CI.
>
> **Two test layers, two cost profiles.** Pure-function tests (guardrails, helpers) are free, fast, and run on every commit. API tests with mocked deps cost ~1s and run on every commit. Agent eval (real LLM, real Langfuse) costs tokens + minutes and is flaky — belongs in a scheduled or manual workflow, not per-PR. Knowing which test goes where is the difference between "CI takes 2 minutes" and "CI takes 30 and burns through your Groq quota."
>
> **Layer caching saves both Docker builds AND CI minutes.** The same `COPY pyproject.toml uv.lock` BEFORE `COPY . .` trick that we used in Dockerfile (Day 22) also benefits GHA via `type=gha` cache backend (Day 23). One mental model, applied at two layers.
>
> **CI/CD is iterative.** First green run is normal to take 2-3 attempts. Each "fix(ci):" commit teaches a real lesson: line-ending differences (Windows CRLF vs Linux LF), tag-naming rules, runner disk constraints. Reading these failures and fixing them in a tight loop IS the skill.

### Files added/modified on Day 23
**Added:**
- `tests/__init__.py` — package marker
- `tests/conftest.py` — `FakeGraph`, `client` fixture, env-var setup
- `tests/test_guardrails.py` — 9 pure-function tests for `is_out_of_scope` and `redact_pii`
- `tests/test_helpers.py` — 5 tests for `_extract_turn_tools` (the backwards walk)
- `tests/test_api.py` — 9 endpoint tests (/health, /chat, /feedback)
- `.github/workflows/ci.yml` — three parallel jobs (lint, test, docker-build) with GHA cache + GHCR push gate

**Modified:**
- `pyproject.toml` — added `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.flake8-bugbear]`, `[tool.ruff.lint.per-file-ignores]`, `[tool.pytest.ini_options]`. New dev deps: `ruff`, `httpx`, `pytest-asyncio`
- `uv.lock` — locked the new dev deps
- 17 source files touched by `ruff format` + `ruff check --fix`: import sorting, `datetime.UTC` modernization, `strict=False` on `zip()`, per-line `# noqa: E402` for intentional late imports

### Day 24 summary

**External services chosen (all free tiers):**

| Service | Plan | Why |
|---|---|---|
| **MongoDB Atlas** M0 | Free forever, 512 MB, AWS Paris | Replaces local Mongo Service. Seed data fits easily (50 users + 200 tickets + 500 events + 20 subs). |
| **Langfuse Cloud** Hobby | Free, EU region | Replaces self-hosted langfuse-web. Cloud + self-hosted Langfuse can coexist (different DBs); we picked Cloud for the deployed agent so traces survive past local docker-compose lifetimes. |
| **Hugging Face Spaces** Docker SDK, CPU basic | Free, 16 GB RAM, 50 GB disk, never sleeps | Most generous free tier for ML images. Builds from `Dockerfile`, deploys via `git push`. Other free tiers (Render 512 MB, Fly.io 256 MB, Railway $5/mo credit) wouldn't fit a 1+ GB image. |

**Step-by-step (the realistic friction):**

| Step | Hit | Fix |
|---|---|---|
| Atlas cluster | Smooth — M0, AWS Paris, automate security setup | — |
| Atlas Network Access | Initially had only home IP whitelisted | Added `0.0.0.0/0` (HF Spaces has no static egress IP — can't whitelist). Documented as a "swap to VPC peering before real prod" debt. |
| Atlas seed | `seed_mongo.py` didn't load `.env`, ran against localhost by default | User added `load_dotenv()` to the script (cleaner than always passing `--env-file`) |
| Langfuse Cloud signup | Easy — GitHub auth, create org + project, generate keys | — |
| First local test against Cloud Langfuse | `python-dotenv could not parse statement starting at line 4` + `Failed to export span batch` | Two issues on `.env` line 4: var renamed to `LANGFUSE_BASE_URL` (intentional, code aligned) BUT had a stray `·` (U+00B7) at end of line. Also re-aligned `docker-compose.yml`'s env block which still set `LANGFUSE_HOST`. |
| Image slim | Drop `sentence-transformers` to remove torch (~800 MB) | Made `from sentence_transformers import CrossEncoder` lazy in `rag/rerank.py` (skeleton). 3 GB → 1.2 GB. |
| First HF push | `error: remote hf already exists`, then `Repository not found` | Wrong username assumed (`YudaLegend` GitHub vs `jinyuuda` HF). Used `git remote set-url hf` to fix. |
| Second HF push | `! [rejected] (fetch first)` | Force push (`--force`). Safe because the only thing on HF was the auto-generated placeholder README. |
| Third HF push | `Sorry, your push was rejected during YAML metadata verification: "short_description" length must be less than or equal to 60 characters` | Shortened the YAML frontmatter `short_description`. |
| First chat after deploy | `chromadb.errors.NotFoundError: Collection [taskflow_docs] does not exist` | Local `data/chroma_db` only had sweep variants (`taskflow_docs_500_50` etc.), not the default-named collection. Solution: lazy-ingest in lifespan handler. Idempotent — runs once on a clean container, no-op on warm restarts. Adds ~30s to first request after deploy. |
| Account-question chat | `pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed: TLSV1_ALERT_INTERNAL_ERROR` against Atlas | Atlas closes TLS handshake without explanation when source IP isn't whitelisted. Added `0.0.0.0/0` to Network Access (was previously only home IP). |
| All five canonical scenarios | ✅ greeting, RAG product question, multi-tool account question, conversation memory follow-up, guardrail refusal — all working in production | — |

**Stack pain points worth remembering:**
- **HF Spaces git remote URL** uses your HF username, not your GitHub username. Different identity systems entirely. Check the URL on your HF profile page if a push fails with "Repository not found."
- **Atlas Network Access blocks at TLS layer**, not at auth. Symptoms look like an SSL bug (`TLSV1_ALERT_INTERNAL_ERROR`) — actually firewall. Fix: ensure `0.0.0.0/0` is on the allowlist for any cloud deploy without static egress IPs.
- **HF Spaces YAML frontmatter rules**: `short_description` ≤ 60 chars; `app_port` must match what your container actually listens on; `sdk: docker` requires a Dockerfile in repo root.
- **`docker compose restart` and `docker compose stop/start` do NOT re-read `.env`** — they restart the existing container with cached env. Use `docker compose up -d --force-recreate <svc>` to re-load. Same trap exists across most container orchestrators; well-known but easy to forget.
- **HF Secrets vs `.env` parsing**: HF's UI form takes the literal string value; quotes you'd write in `.env` (which dotenv strips) become part of the value in HF (which has no parser stripping). Easy 401 if you copy with quotes.
- **Lazy first-start ingest is cleaner than baking the index in.** Image stays smaller, no dependency on the developer's local Chroma state being correct, idempotent across redeploys. Cost: ~30s on cold start (download embedder + chunk + embed 21 docs).
- **`from __future__ import annotations`** + lazy `import sentence_transformers` inside a function = the file imports cleanly without the dep installed. Useful pattern for "feature is scaffolded but not yet enabled."
- **TestClient triggers `lifespan`**, so any side effects there (lazy ingest, get_graph) need to be mocked in conftest or the test suite slows down dramatically. Used `monkeypatch.setattr("app.main._ensure_rag_index", lambda: None)`.

**Key Day 24 learnings (interview-gold):**
> **A free-tier deploy isn't free of design choices.** "Pick a platform" is the headline; the real work is figuring out which dependencies leave the host (Mongo? Yes, to Atlas. Langfuse? Yes, to Cloud. ChromaDB? No, embedded with lazy-ingest), what slimming you need to fit (drop torch via dropping sentence-transformers — the reranker was unfilled scaffold anyway), and how to swap the env-var topology between dev (compose service-name DNS) and prod (real public hostnames). Each decision is a real interview talking point.
>
> **Multi-environment env-var management is its own discipline.** The same agent code runs three ways: locally without docker (reads `.env`), locally with compose (compose's `environment:` block overrides `.env`), and on HF Spaces (Secrets in the UI override anything else). The pattern: code reads `os.getenv("X", <local-default>)`, dev defaults work for laptop runs, compose overrides for in-network DNS, prod platform Secrets win in deploy. The same env-var name flows through three layers.
>
> **TLS errors are often firewall errors in disguise.** `TLSV1_ALERT_INTERNAL_ERROR` from Atlas = "your IP isn't on my allowlist," not "your TLS is broken." Cloud databases prefer to fail the handshake silently rather than tell you why. Lesson: when a TLS error keeps coming back even after retries and the cert is fine, suspect the firewall first.
>
> **Lazy ingest beats baked-in state for portability.** Shipping the Chroma index in the image looked simpler at first, but it depended on the developer's local state being correct. Switching to "if collection missing on startup, ingest from data/docs" made the deploy reproducible from any clean clone — same image, any disk, works.

### Files added/modified on Day 24
**Added:**
- `.env.example` — template with comments per env var, where to get keys, graceful-degradation notes

**Modified:**
- `pyproject.toml`, `uv.lock` — dropped `sentence-transformers` from runtime deps
- `Dockerfile` — unchanged (still multi-stage), but final image now ~1.2 GB instead of ~3 GB due to the dep removal
- `.dockerignore` — restored `data/chroma_db/` exclusion (lazy ingest replaces it)
- `docker-compose.yml` — `LANGFUSE_HOST` → `LANGFUSE_BASE_URL` to match the renamed code var
- `.env` — added `MONGO_URI` (Atlas SRV string), updated `LANGFUSE_*` to Cloud values, renamed `LANGFUSE_HOST` → `LANGFUSE_BASE_URL`
- `agent/graph.py` — `os.getenv("LANGFUSE_HOST", ...)` → `os.getenv("LANGFUSE_BASE_URL", ...)`
- `app/main.py` — added `_ensure_rag_index()` and called from lifespan (lazy first-start ingest)
- `data/seed_mongo.py` — added `load_dotenv()` so it picks up Atlas URI without `--env-file`
- `rag/rerank.py` — `from sentence_transformers import CrossEncoder` made lazy (inside `_get_model`) so the module imports cleanly without the dep
- `tests/conftest.py` — `monkeypatch.setattr("app.main._ensure_rag_index", lambda: None)` so tests don't trigger ingest
- `README.md` — full rewrite (badges, mermaid arch diagram, tech stack table, three quickstart paths, project tree, eval design, observability loop, 7 design-decision callouts, roadmap, links)

### Open issues / still pending
- `agent/llm.py` still uses `llama-3.3-70b-versatile` — fine for RAG answerer, but graph.py uses Llama 4 Scout
- Reranker skeleton (`rag/rerank.py`) still has unfilled TODOs — skipped deliberately
- Interview questions Sections 1–2 drafted but not yet revised; Sections 3–15 unanswered
- `00-product-brief.md` still indexed in ChromaDB (known from Day 10)
- `MemorySaver` is in-RAM only — conversations lost on restart, AND two requests on the same `thread_id` at once will race the checkpointer (no per-thread locking). Acceptable for dev, must be swapped (PostgresSaver) before deploy.
- Message history grows unbounded — no trimming/summarization yet
- Docker-compose uses dev-only secrets (`ENCRYPTION_KEY=00...`, hardcoded Postgres creds). Fine for local, must be swapped before anything leaves localhost.
- Agent eval is not wired into CI yet — currently a manual `uv run python -m eval.run_agent_eval`
- Some agent-eval scenarios may be flaky on LLM judgment edges (e.g. `edge_unknown_user`, `multiturn_ticket_followup`). If CI flaps, tighten assertions or accept flake and tag `@flaky`.
- `/feedback` always returns 204 even if `trace_id` doesn't exist in Langfuse — `create_score` doesn't validate, it just creates an orphan score. Could surface this as 404 by querying first, but adds latency.
- Demo UI has no message-history persistence — page refresh = new `thread_id` = lost conversation. Same statelessness as the server, by design.
- FastAPI service has no auth, no rate limiting, no CORS config — fine for `localhost`, blocks public deploy.
- **Docker image is ~3 GB** — torch + onnxruntime + sentence-transformers dominate. Optimization path: CPU-only torch wheel via `--index-url https://download.pytorch.org/whl/cpu` (saves ~600 MB), or drop sentence-transformers if Chroma's default embedder suffices.
- **MongoDB still on host** (Windows Service), reached via `host.docker.internal`. Fine for local single-machine dev. Before deploy: add a `mongo:` service to compose, run a one-time `seed_mongo.py` against it, point `MONGO_URI` at the service name.
- **Dockerfile runs as root.** Production hardening: add `RUN useradd -r appuser && chown -R appuser:appuser /app` and `USER appuser` near the end of the runtime stage.
- **No image pinning.** `python:3.11-slim` floats — should be `python:3.11.X-slim-bookworm@sha256:...` for reproducibility before any prod deploy.
- **No healthcheck instruction in the Dockerfile** — compose could declare one against `/health`, but we didn't.
- **Docker job is the slowest CI step (~30 min cold).** The free-disk-space step adds ~30s. Improvement levers: switch to a CPU-only torch wheel (~600 MB smaller), or split the build into a separate workflow that only triggers on Dockerfile/dependency changes (currently runs on every commit).
- **Agent eval not wired to CI yet.** `eval/run_agent_eval.py` costs Groq tokens and is flaky on LLM-judgment edges — belongs in a scheduled workflow, not per-PR. Day 24 candidate D.
- **No README + no CI badge.** Recruiters scan repo READMEs first; ours is still the placeholder. Day 24 candidate A.

### Next session — Day 25 candidates (pick one with user)

**A. Demo video (highest portfolio-value-per-hour, smallest scope):**
- 60-90s screen recording: load the live HF Space, ask a product question (RAG), ask an account question (Mongo), click 👎, switch to Langfuse and show the trace + score, switch to GitHub and show the CI badge / commit history
- Tools: OBS Studio (free) or Windows Game Bar (Win+G, built-in). Trim with Clipchamp/iMovie.
- Upload unlisted to YouTube, embed in README via thumbnail+link. The TODO comment is already in place near the demo section of README.

**B. Persistent checkpointer (PostgresSaver):**
- Swap `MemorySaver()` → `PostgresSaver(conn_string=...)` in `agent/graph.py`
- For the cloud deploy, point at a free Neon or Supabase Postgres (or reuse the Langfuse Atlas-equivalent). For local compose, add a `taskflow-postgres` service.
- Conversations now survive `docker compose down/up` AND HF Space restarts; multi-replica deploy becomes possible.
- Concepts: connection pooling, schema migration on first start, idempotent setup. Tests in CI get more interesting (real DB or testcontainers).

**C. Image-size pass + production hardening:**
- Add `USER appuser` for non-root runtime
- Pin base image to a SHA digest for reproducibility
- Add a `HEALTHCHECK` instruction to the Dockerfile (compose already references `/health`)
- Add `trivy` or `docker scout` scan as a fourth CI job
- Try Chroma's bundled onnx model directly — possibly another ~100 MB off
- Concepts: SBOM, image scanning, reproducibility, supply-chain security.

**D. Scheduled agent eval workflow:**
- New `.github/workflows/agent-eval.yml` triggered weekly + manual `workflow_dispatch`
- Runs `eval/run_agent_eval.py` against real Groq + Langfuse Cloud (via secrets)
- Posts results as a commit comment or release note
- Concepts: secrets management in GHA (envs, OIDC), scheduled workflows, "test on every PR vs eval on a schedule" split.

**Collaboration reminder:** User is learning for interviews. Explain concepts before code. For pipeline/algo code give a skeleton + TODOs; for scaffolding/boilerplate just write it. Be brief. Use tables. The TaskFlow project is now in the Interview-Ready Shape phase — focus on polishing what exists rather than adding new agent capabilities.
