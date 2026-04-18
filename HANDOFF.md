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

- **LLM provider:** Groq (free tier), model `llama-3.3-70b-versatile`
- **Vector DB:** ChromaDB (local, persistent)
- **Embeddings:** `all-MiniLM-L6-v2` (ChromaDB default, 384-dim)
- **Database:** MongoDB Community Server, local, database name `taskflow`
- **Agent framework:** LangGraph + LangChain core
- **Python:** 3.11, managed via `uv`

## Project structure

```
taskflow-support-agent/
├── agent/
│   ├── llm.py              # Groq wrapper — chat(messages, ...) -> str
│   └── graph.py            # Minimal one-node LangGraph agent (Day 5)
├── rag/
│   ├── ingest.py           # Load docs → chunk → embed → ChromaDB
│   ├── retrieve.py         # retrieve(query, k) -> list of chunks
│   └── answer.py           # RAG answerer (retrieve → stuff → LLM → answer)
├── data/
│   ├── docs/               # 21 markdown files — the RAG corpus
│   ├── chroma_db/          # Persistent vector DB (gitignored)
│   └── seed_mongo.py       # Seeder: 50 users, 200 tickets, 500 events, 20 subs
├── eval/
│   ├── golden.jsonl        # 25 hand-written Q/A pairs
│   ├── run_eval.py         # LLM-as-judge eval (faithfulness + relevancy)
│   └── results.json        # Latest eval output
├── app/                    # Not yet used (FastAPI later)
├── tests/                  # Not yet used
├── notebooks/              # Not yet used
├── learning/concepts/      # User's self-notes on concepts learned
└── .env                    # GROQ_API_KEY (gitignored)
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
| 16+ | Guardrails, FastAPI, eval, Docker, CI | ⏳ |

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

End of Day 15. Phase 3 (agent + tools + memory) is functional.

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

### Open issues / still pending
- `agent/llm.py` still uses `llama-3.3-70b-versatile` — fine for RAG answerer, but graph.py uses Llama 4 Scout
- Reranker skeleton (`rag/rerank.py`) still has unfilled TODOs — skipped deliberately
- Interview questions Sections 1–2 drafted but not yet revised; Sections 3–10 unanswered
- `00-product-brief.md` still indexed in ChromaDB (known from Day 10)
- `MemorySaver` is in-RAM only — conversations lost on restart (fine for dev, not prod)
- Message history grows unbounded — no trimming/summarization yet

### Next session — Day 16: Guardrails (recommended)

**Why this over long-term memory:**
- Long-term memory adds significant complexity (vector store for memories, retrieval
  strategy for past facts, eviction policy) without obvious portfolio payoff
- Guardrails is a HIGH-signal interview topic right now (prompt injection is hot
  in 2026 hiring). Every production agent needs them.
- Several guardrail pieces are easy wins on top of existing code (max-tool-calls
  is half-done via `recursion_limit`; output validation reuses Pydantic patterns
  from Day 13).

**Day 16 plan:**
- **Refusal logic** for out-of-scope questions (e.g., "write me a poem", competitor
  product questions). Add to system prompt + a check node.
- **PII redaction in logs** — emails, ticket descriptions get masked before any
  print/log. Helps for the FastAPI day too.
- **Max-tool-calls enforcement** beyond `recursion_limit` — count actual tool
  invocations per conversation, hard cap at e.g. 8.
- **Output validation** with Pydantic — agent responses for structured operations
  (e.g., create_ticket confirmations) validated before returning to user.
- **Prompt injection defense** — basic checks on user input ("ignore previous
  instructions", role-hijacking attempts).

**Concepts to study before Day 16:** prompt injection (direct vs indirect),
input validation vs output validation, defense in depth, PII handling
basics (GDPR awareness).

**Collaboration reminder:** User is learning for interviews. Explain
concepts before code. For pipeline/algo code give a skeleton + TODOs; for
scaffolding/boilerplate just write it. Be brief. Use tables.
