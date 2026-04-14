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
| 11 | Improve retrieval (chunk size, hybrid, reranking) | 🔄 NEXT |
| 12+ | Tool use, LangGraph routing, FastAPI, eval, Docker, CI | ⏳ |

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

Working on **Day 11** — improve retrieval via chunk size sweeps, hybrid
search (BM25 + dense), and possibly reranking. The `rag/ingest.py` has
already been parameterized to accept `chunk_size`, `chunk_overlap`, and
`collection_name` from the CLI for running experiments. There's an empty
`eval/RETRIEVAL_EXPERIMENTS.md` waiting to be filled with results.
