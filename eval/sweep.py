"""Sweep retrieval configs: ingest -> eval -> append row to the markdown table.

Usage:
    python -m eval.sweep

Edit CONFIGS below to run different experiments. Each config re-ingests into
its own named Chroma collection, runs the full eval, and appends a row to
eval/RETRIEVAL_EXPERIMENTS.md automatically.
"""

import os
from datetime import datetime

from rag import ingest
from eval.run_eval import run_eval
from chromadb import PersistentClient

EXPERIMENTS_MD = os.path.join(os.path.dirname(__file__), "RETRIEVAL_EXPERIMENTS.md")
CHROMA_DIR = os.getenv(
    "CHROMA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"),
)

CONFIGS = [
    # label, chunk_size, chunk_overlap, retriever, reranker, notes
    ("dense 500",  500, 50, "dense",  "—", "baseline"),
    ("hybrid 500", 500, 50, "hybrid", "—", "BM25 + dense + RRF"),
]



def run_one(label: str, chunk_size: int, chunk_overlap: int,
            retriever: str, reranker: str, notes: str) -> dict:
    
    collection = f"taskflow_docs_{chunk_size}_{chunk_overlap}"
    print(f"\n{'#'*60}\n# {label}  (chunk={chunk_size}, overlap={chunk_overlap})\n{'#'*60}")

    # 1. ingest

    
    client = PersistentClient(path=CHROMA_DIR)

    existing = {c.name for c in client.list_collections()}
    
    if collection not in existing:
        ingest.main(chunk_size=chunk_size, chunk_overlap=chunk_overlap, collection_name=collection)
    else:
        print(f"Collection {collection} already exists, skipping ingest.")

    # 2. point retrieve() at the new collection (read inside retrieve())
    os.environ["TASKFLOW_COLLECTION"] = collection
    summary = run_eval(retrieval_only=False, retriever=retriever)


    return {
        "label": label,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "retriever": retriever,
        "reranker": reranker,
        "notes": notes,
        **summary,
    }


def format_row(i: int, row: dict) -> str:
    faith = f"{row['faithfulness']:.2f}" if "faithfulness" in row else "—"
    relev = f"{row['relevancy']:.2f}" if "relevancy" in row else "—"
    return (
        f"| {i} | {row['label']:<18} | {row['chunk_size']} | {row['chunk_overlap']} | "
        f"{row['retriever']} | {row['reranker']} | "
        f"{row['hit@3']:.2f} | {row['hit@5']:.2f} | "
        f"{faith} | {relev} | {row['notes']} |"
    )


def append_results_to_md(rows: list[dict]):
    """Append a fresh results section to RETRIEVAL_EXPERIMENTS.md."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"\n### Run {stamp}\n",
        "| # | config | chunk_size | overlap | retriever | reranker | hit@3 | hit@5 | faith | relev | notes |",
        "|---|--------|------------|---------|-----------|----------|-------|-------|-------|-------|-------|",
    ]
    for i, row in enumerate(rows):
        lines.append(format_row(i, row))

    with open(EXPERIMENTS_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nAppended {len(rows)} rows to {EXPERIMENTS_MD}")


def main():
    rows = [run_one(*cfg) for cfg in CONFIGS]
    append_results_to_md(rows)


if __name__ == "__main__":
    main()
