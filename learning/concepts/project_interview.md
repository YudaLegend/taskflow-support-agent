# Interview questions — TaskFlow Support Agent

Questions an interviewer could ask about what's been built so far (through Day 11).
Answer each in your own words, then I'll review.

> **Scope:** covers Days 1–11 — project setup, Groq wrapper, LangGraph skeleton,
> MongoDB seeding, RAG ingestion, retrieval, eval framework, chunk-size sweeps,
> hybrid retrieval (BM25 + RRF), and cross-encoder reranking.

---

## Section 1 — Project setup & architecture

1. Give me a 60-second overview of what this project does, who the user is, and what you've built so far.
2. Why did you pick Groq over OpenAI or Anthropic? What would you change to swap providers?
3. Why MongoDB (local, not Atlas)? What would break if this were a real production deployment?
4. You have a `chat()` wrapper in `agent/llm.py` instead of calling the Groq SDK directly everywhere. Why? What's the tradeoff?
5. Why LangGraph and not raw Python? If the current graph only has one node, was adding LangGraph overkill at this stage?

## Section 2 — RAG fundamentals

6. Walk me through what happens end-to-end when a user asks "How much does the Pro plan cost?" — from HTTP request to final answer (or, today, from CLI to final answer).
7. Why do we chunk docs at all? What's the tradeoff between small chunks (200 tokens) and large chunks (1000 tokens)?
8. What is an embedding? What does the number 384 refer to in your setup?
9. What does ChromaDB actually store on disk, and what does it compute at query time?
10. Why did you parameterize `chunk_size`, `chunk_overlap`, and `collection_name` in `ingest.py`?

## Section 3 — Evaluation

11. You built a golden dataset of 25 Q/A pairs. Why 25 and not 5 or 500? What are the risks of each extreme?
12. Explain `hit@k` in your own words. Why did you add it even though you already had LLM-as-judge scores?
13. What's the difference between **faithfulness** and **relevancy** in your eval? Give an example of an answer that scores high on one and low on the other.
14. LLM-as-judge is noisy — you've said this yourself. What's one concrete way you could reduce that noise?
15. In Day 11, `hit@5` was 1.00 across every chunk-size config. What does that tell you? How would you fix it?

## Section 4 — Retrieval improvements (the core of Day 11)

16. What's the difference between dense retrieval and BM25, at the representation level (not just "one is neural and one isn't")?
17. Why can a bi-encoder precompute doc vectors, but a cross-encoder cannot?
18. Explain Reciprocal Rank Fusion. Why does it use ranks instead of raw scores?
19. Your hybrid retriever *regressed* compared to dense-only on this corpus. Why? What does this tell you about when hybrid helps?
20. Cross-encoder reranking is always Stage 2, never Stage 1. Why not just use the cross-encoder directly on the whole corpus?
21. If the first-stage retriever misses the correct document entirely (not in top-20), what can the reranker do? What does this imply about how you should tune `top_n`?
22. Cross-encoder scores are "higher = better" but ChromaDB distances are "lower = better." Why is this worth being paranoid about when combining retrieval systems?

## Section 5 — Experimental methodology

23. When running retrieval sweeps, you flipped `retrieval_only=True` to skip LLM calls. What was the reasoning, and when would you flip it back on?
24. There was a subtle bug in `retrieve.py` where the default argument was captured at function-def time. Explain what was wrong and why that bug would silently invalidate every experiment.
25. If I gave you twice the Groq token budget, what experiment would you run next, and why?
26. You chose not to persist the BM25 index to disk — it rebuilds in memory each run. Why is that OK for this project, and when would it stop being OK?

## Section 6 — Systems / production thinking

27. Today you have 21 docs. What changes in your architecture at 21,000 docs? At 21 million?
28. Your RAG returns a `score` for the top chunk. Could you use that as a confidence signal for a "don't-know / escalate to human" response? What's the risk?
29. Imagine the corpus is updated hourly (new help docs published). What's your reingestion strategy? What breaks if you just re-run `ingest.py` every hour?
30. What observability/logging would you add before putting this in production? Name three specific things and why.

## Section 7 — Tradeoffs & judgment

31. You have finite time. Rank these four improvements by expected ROI for a portfolio project, and justify: (a) add 50 more golden questions, (b) add cross-encoder reranking, (c) add a streaming UI, (d) add per-doc access control.
32. What's the single biggest weakness of this project right now? How would you fix it?
33. If an interviewer said "your hit@3 is already 1.00, so this project is done — why spend Day 11 on retrieval at all?", what's your defense?
34. What's one thing you'd do differently if you were starting this project from scratch today?

---

## How to use this file

1. Pick a section per study block.
2. Write answers inline, or in a scratchpad first, then paste them here.
3. Ask Claude to review — you'll get feedback on clarity, correctness, and
   how it lands as an interview answer (concise, specific, shows tradeoffs).
4. Add more questions as you finish Days 12+.
