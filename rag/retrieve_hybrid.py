"""Hybrid retrieval: dense (ChromaDB) + BM25, fused with Reciprocal Rank Fusion.

Why hybrid: dense embeddings are great at paraphrases but can miss exact
keywords / rare tokens. BM25 is the opposite. Combining them covers both.

Why RRF: fusing by score requires normalizing scales (cosine vs BM25), which
is fragile. RRF fuses *ranks* instead — scale-free, robust, one-liner math.
"""

import os
import re

import chromadb
from rank_bm25 import BM25Okapi

CHROMA_DIR = os.getenv(
    "CHROMA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"),
)


# Simple tokenizer — lowercase, split on non-word chars. BM25 needs token lists.
def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


# Cache: build the BM25 index once per collection, not every query.
_bm25_cache: dict[str, dict] = {}


def _load_corpus(collection_name: str) -> dict:
    """Pull every chunk from the Chroma collection and build a BM25 index over it.

    Returns a dict with:
      - "ids":      list[str]        (chunk ids, in a fixed order)
      - "docs":     list[str]        (chunk text, same order)
      - "metadatas":list[dict]        (source metadata, same order)
      - "bm25":     BM25Okapi        (fitted on tokenized docs)
    """
    if collection_name in _bm25_cache:
        return _bm25_cache[collection_name]

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(collection_name)
    # collection.get() with no filter returns everything
    raw = collection.get(include=["documents", "metadatas"])

    # TODO 1: extract ids, docs, metadatas from `raw` into three lists (same order).
    ids = []
    docs = []
    metadatas = []
    for id, doc, meta in zip(raw["ids"], raw["documents"], raw["metadatas"], strict=False):
        ids.append(id)
        docs.append(doc)
        metadatas.append(meta)

    # TODO 2: tokenize each doc with tokenize() above -> list[list[str]]
    #         then fit BM25Okapi on it.

    bm25 = BM25Okapi([tokenize(doc) for doc in docs])

    entry = {
        "ids": ids,
        "docs": docs,
        "metadatas": metadatas,
        "bm25": bm25,
    }
    _bm25_cache[collection_name] = entry
    return entry


def _dense_ranking(query: str, collection_name: str, top_n: int) -> list[str]:
    """Return the top_n chunk ids from dense retrieval, best-first."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(collection_name)
    # TODO 3: call collection.query(query_texts=[query], n_results=top_n)
    #         and return the list of ids (results["ids"][0]).
    results = collection.query(query_texts=[query], n_results=top_n)
    return results["ids"][0]


def _bm25_ranking(query: str, collection_name: str, top_n: int) -> list[str]:
    """Return the top_n chunk ids from BM25, best-first."""
    corpus = _load_corpus(collection_name)
    # TODO 4: tokenize the query, call corpus["bm25"].get_scores(tokens)
    #         -> numpy array of scores (one per doc, in corpus order).
    #         Take indices of top_n highest scores.
    #         Map those indices back to corpus["ids"] and return.
    #         Hint: numpy argsort + slicing, or sorted(enumerate(...)).
    tokens = tokenize(query)
    scores = corpus["bm25"].get_scores(tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    top_ids = [corpus["ids"][i] for i in top_indices]
    return top_ids


def retrieve_hybrid(
    query: str,
    k: int = 3,
    top_n: int = 20,
    rrf_k: int = 60,
    collection_name: str | None = None,
) -> list[dict]:
    """Hybrid retrieval with RRF fusion.

    top_n  = how many results to pull from each retriever before fusing
             (bigger top_n = more chances for a doc to appear in both lists)
    rrf_k  = RRF smoothing constant (60 is standard)
    """
    if collection_name is None:
        collection_name = os.environ.get("TASKFLOW_COLLECTION", "taskflow_docs")

    dense_ids = _dense_ranking(query, collection_name, top_n)
    bm25_ids = _bm25_ranking(query, collection_name, top_n)

    # TODO 5: compute RRF score per id.
    #         For each retriever's ranking, for each (rank, doc_id), add
    #         1 / (rrf_k + rank) to that doc's score. rank is 1-based.
    #         Use a dict[str, float] to accumulate.
    rrf_scores = {}
    for rank, doc_id in enumerate(dense_ids, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (rrf_k + rank)
    for rank, doc_id in enumerate(bm25_ids, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (rrf_k + rank)


    # TODO 6: sort ids by fused score descending, take top k.
    sorted_ids = sorted(rrf_scores.keys(), key=lambda id: rrf_scores[id], reverse=True)[:k]

    # TODO 7: look up the text + metadata for those ids from the cached corpus
    #         and return a list[dict] shaped like retrieve.retrieve() does:
    #         [{"text": ..., "source": ..., "score": <fused_score>}, ...]
    corpus = _load_corpus(collection_name)
    id_to_doc = dict(zip(corpus["ids"], corpus["docs"], strict=False))
    id_to_meta = dict(zip(corpus["ids"], corpus["metadatas"], strict=False))
    results = []
    for doc_id in sorted_ids:
        results.append({
            "text": id_to_doc[doc_id],
            "source": id_to_meta[doc_id].get("source", "unknown"),
            "score": rrf_scores[doc_id],
        })
    return results

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How much does Pro cost?"
    results = retrieve_hybrid(q, k=3)
    print(f"\nQuery: {q}\n")
    for i, r in enumerate(results, 1):
        print(f"--- Result {i} (RRF score: {r['score']:.4f}) ---")
        print(f"Source: {r['source']}")
        print(r["text"][:200], "...")
        print()
