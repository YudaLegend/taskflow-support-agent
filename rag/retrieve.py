"""Retrieve relevant chunks from ChromaDB"""



import os

import chromadb

CHROMA_DIR = os.getenv(
    "CHROMA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"),
)


def retrieve(query: str, k: int = 3, collection_name: str | None = None) -> list[dict]:
    """Find the k most relevant chunks for a query.

    The collection name is configurable so you can eval different chunk-size
    ingestions without touching caller code. Override globally via the
    TASKFLOW_COLLECTION env var, or per-call via the argument.

    Returns a list of dicts:[{"text": "...", "source": "", "score": 0.42}, ...]
    """
    if collection_name is None:
        collection_name = os.environ.get("TASKFLOW_COLLECTION", "taskflow_docs")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(collection_name)
    # TODO 3: Call collection.query(query_texts=[query], n_results=k)
    results = collection.query(query_texts=[query], n_results=k)
    # TODO 4: Build and return a list of result dicts
    output = []

    for text, source, score in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        strict=False,
    ):
        output.append({"text": text, "source": source["source"], "score": score})


    return output

if __name__ == "__main__":
    # Test with a few questions
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How much does Pro cost?"
    results = retrieve(query, k=3)
    print(f"\nQuery: {query}\n")
    for i, r in enumerate(results, 1):
        print(f"--- Result {i} (score: {r['score']:.4f}) ---")
        print(f"Source: {r['source']}")
        print(f"{r['text']}...")
        print()
