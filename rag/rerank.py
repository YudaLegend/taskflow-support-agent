"""Cross-encoder reranker — Stage 2 of two-stage retrieval.

The reranker takes a shortlist from a first-stage retriever (dense, BM25,
or hybrid) and rescores each (query, chunk) pair with a cross-encoder.
Cross-encoders attend across the query and doc in one forward pass, so they
score more accurately than bi-encoders — at the cost of being ~100× slower
per pair. That's why they only see top_n, not the whole corpus.

Typical pattern:
    candidates = retrieve_hybrid(query, k=20)   # Stage 1: wide net
    top = rerank(query, candidates, k=3)        # Stage 2: sharp sort
"""

from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Load once, reuse. Loading is slow (~seconds); scoring is fast.
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    """Lazy-load the cross-encoder once per process."""
    global _model
    if _model is None:
        print(f"Loading reranker model: {MODEL_NAME} ...")
        _model = CrossEncoder(MODEL_NAME)
    return _model


def rerank(query: str, candidates: list[dict], k: int = 3) -> list[dict]:
    """Rescore candidates with the cross-encoder and return the top k.

    Args:
        query: the user's question.
        candidates: list of dicts from a first-stage retriever. Each dict
            has at least "text", "source" (and a "score" from Stage 1
            which we'll ignore — the reranker replaces it).
        k: how many to return after reranking.

    Returns:
        A list of k dicts, same shape as the input but with "score" now
        being the cross-encoder relevance score (higher = more relevant,
        unbounded — typical range roughly -10 to +10).
    """
    model = _get_model()

    # TODO 1: Build the list of (query, doc_text) pairs the model needs.
    #         Each pair is a 2-tuple of strings: (query, candidate["text"]).
    #         Shape: list[tuple[str, str]], length = len(candidates).


    # TODO 2: Call model.predict(pairs) — returns a numpy array of scores,
    #         one per pair, in the same order as `candidates`.


    # TODO 3: Attach each new score back to its candidate dict.
    #         Tip: zip(candidates, scores) and set candidate["score"] = float(s).


    # TODO 4: Sort candidates by "score" descending, return the top k.
    #         Reminder: cross-encoder scores are *higher = better*. This is
    #         OPPOSITE to Chroma's distance (lower = better) — easy to trip on.


if __name__ == "__main__":
    # Smoke test: compare hybrid alone vs hybrid + rerank on a tricky query.
    import sys
    from rag.retrieve_hybrid import retrieve_hybrid

    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How much does Pro cost?"

    stage1 = retrieve_hybrid(q, k=20)   # wide net
    stage2 = rerank(q, stage1, k=3)      # sharp sort

    print(f"\nQuery: {q}\n")
    print("=== Stage 1 (hybrid, top-5 of 20) ===")
    for i, r in enumerate(stage1[:5], 1):
        print(f"{i}. [{r['source']}] RRF={r['score']:.4f}  {r['text'][:80]}...")

    print("\n=== Stage 2 (reranked, top-3) ===")
    for i, r in enumerate(stage2, 1):
        print(f"{i}. [{r['source']}] rerank={r['score']:.3f}  {r['text'][:80]}...")
