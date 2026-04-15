# Retrieval Experiments — Day 11

Tracking retrieval quality as we vary chunking, retriever, and re-ranking.
Run each config end-to-end through `run_eval.py` and fill a row below.

## How to run an experiment

1. **Re-ingest** with the config under test:
   ```bash
   python -m rag.ingest <chunk_size> <chunk_overlap> <collection_name>
   # e.g. python -m rag.ingest 200 20 taskflow_docs_200
   ```
2. **Point eval at that collection**:
   ```bash
   TASKFLOW_COLLECTION=taskflow_docs_200 python -m eval.run_eval
   ```
3. Copy the final averages into the table.

## Metrics

- **hit@k**: fraction of golden questions where the expected source file
  appears in the top-k retrieved chunks. Pure retrieval signal — no LLM.
- **faithfulness / relevancy**: 1–5 LLM-judge scores on the final answer.
  End-to-end signal — catches cases where retrieval is fine but the LLM
  still hallucinates, and vice versa.

## Results

| # | config              | chunk_size | overlap | retriever     | reranker          | hit@3 | hit@5 | faith | relev | notes |
|---|---------------------|------------|---------|---------------|-------------------|-------|-------|-------|-------|-------|
| 0 | baseline            | 500        | 50      | dense (Chroma)| —                 |       |       |       |       | current prod config |
| 1 | small chunks        | 200        | 20      | dense         | —                 |       |       |       |       |       |
| 2 | large chunks        | 1000       | 100     | dense         | —                 |       |       |       |       |       |
| 3 | hybrid (best chunk) | ?          | ?       | dense + BM25  | RRF (k=60)        |       |       |       |       |       |
| 4 | hybrid + rerank     | ?          | ?       | dense + BM25  | cross-encoder L-6 |       |       |       |       |       |

## Observations

<!-- After each run, write 1–2 bullets on what moved and why you think so.
     This is the part that matters for your portfolio — numbers alone don't
     tell a story. -->

- baseline:
- exp 1:
- exp 2:
- exp 3:
- exp 4:

### Run 2026-04-14 18:40

| # | config | chunk_size | overlap | retriever | reranker | hit@3 | hit@5 | faith | relev | notes |
|---|--------|------------|---------|-----------|----------|-------|-------|-------|-------|-------|
| 0 | baseline           | 500 | 50 | dense | — | 1.00 | 1.00 | — | — | current prod config |
| 1 | tiny chunks        | 200 | 20 | dense | — | 0.92 | 1.00 | — | — |  |
| 2 | small chunks       | 300 | 30 | dense | — | 0.96 | 1.00 | — | — |  |
| 3 | medium chunks      | 750 | 75 | dense | — | 0.96 | 1.00 | — | — |  |
| 4 | large chunks       | 1000 | 100 | dense | — | 0.96 | 1.00 | — | — |  |

### Run 2026-04-15 — dense vs hybrid (full eval, LLM judges ON)

| # | config     | chunk_size | overlap | retriever      | reranker | hit@3 | hit@5 | faith | relev | notes |
|---|------------|------------|---------|----------------|----------|-------|-------|-------|-------|-------|
| 0 | dense 500  | 500        | 50      | dense          | —        | 1.00  | 1.00  | 5.00  | 4.88  | baseline — 25/25 questions |
| 1 | hybrid 500 | 500        | 50      | dense + BM25 (RRF, k=60) | — | ~0.80 | ~0.95 | — | — | rate-limited after Q20; misses: Q1, Q6, Q15, Q19 |

## Observations

- **Dense is saturated on this corpus.** 21 docs, single domain, well-written → dense hit@3 = 1.00. There's no room for a second retriever to improve recall.
- **Hybrid regressed retrieval AND faithfulness.** On Q1 ("How much does the Pro plan cost?"), hybrid missed hit@3 *and* the LLM hallucinated a monthly price (faith 5 → 3). BM25 over-weighted common tokens ("plan", "Pro", "cost") and pulled competing pricing chunks, bumping the right chunk out of the top 3. The wrong context then caused the answer to drift. Clean causal chain: bad retrieval → bad answer.
- **hit@5 = 1.00 across every config so far.** Metric is saturated — the test set is too easy to discriminate. Future work: add harder/ambiguous questions, or switch to hit@1 / MRR for sharper signal.
- **Takeaway:** Hybrid retrieval is a tool, not a default. Real wins show up on noisy, heterogeneous corpora with rare tokens and mixed query styles. On a clean, small, single-domain corpus, dense alone is often enough, and BM25 adds noise.
