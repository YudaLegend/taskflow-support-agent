"""Load Taskflwo docs,chunk,embed and store in ChromaDB"""

import os

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "docs")
CHROMA_DIR = os.getenv(
    "CHROMA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"),
)


def load_docs(docs_dir: str) -> list[dict]:
    """Read all .md files from docs_dir.

    Return a list of dicts: [{"filename": "pricing-plans.md", "content": "..."}, ...]
    """
    # TODO 1:
    # Loop through all files in docs_dir
    # For each .md file, read its content
    # Append {"filename": filename, "content": text} to a list
    # Return the list
    docs = []
    for filename in os.listdir(docs_dir):
        if filename.endswith(".md"):
            with open(os.path.join(docs_dir, filename), encoding="utf-8") as f:
                content = f.read()
                docs.append({"filename": filename, "content": content})

    return docs


def chunk_docs(
    docs: list[dict],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> tuple[list[str], list[dict]]:
    """Split docs into chunks.

    Returns:
        texts: list of chunk strings
        metadatas: list of dicts with "source" key (the filename)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    # For each doc, split the content:
    #   chunks = splitter.split_text(doc["content"])
    #
    texts = []
    metadatas = []
    for doc in docs:
        chunks = splitter.split_text(doc["content"])
        metadatas.extend([{"source": doc["filename"]}] * len(chunks))
        texts.extend(chunks)
    # For each chunk, add the text to a "texts" list
    # and {"source": doc["filename"]} to a "metadatas" list
    #
    return (texts, metadatas)


def store_in_chroma(
    texts: list[str],
    metadatas: list[dict],
    collection_name: str = "taskflow_docs",
) -> None:
    """Embed and store chunks in ChromaDB. Resets the collection first."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    # TODO D1: Delete the collection if it already exists, so re-ingest
    # doesn't append duplicate IDs. Hint: client.delete_collection(name=...)
    # inside a try/except (it raises if missing).
    try:
        client.delete_collection(name=collection_name)
    except chromadb.errors.NotFoundError:
        pass  # collection didn't exist, no need to delete
    collection = client.get_or_create_collection(name=collection_name)
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=[f"chunk_{i}" for i in range(len(texts))],
    )
    print(f"Stored {collection.count()} chunks in {collection_name}.")


def main(chunk_size: int = 500, chunk_overlap: int = 50, collection_name: str = "taskflow_docs"):
    print(f"Loading docs... (chunk_size={chunk_size}, overlap={chunk_overlap})")
    docs = load_docs(DOCS_DIR)
    print(f"Loaded {len(docs)} documents.")

    print("Chunking...")
    texts, metadatas = chunk_docs(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Created {len(texts)} chunks.")

    print("Storing in ChromaDB...")
    store_in_chroma(texts, metadatas, collection_name=collection_name)
    print("Done!")


if __name__ == "__main__":
    # Usage: python -m rag.ingest [chunk_size] [chunk_overlap] [collection_name]
    # TODO D2: Parse sys.argv so you can sweep configs from the CLI,
    # e.g. `python -m rag.ingest 200 20 taskflow_docs_200`
    import sys

    args = sys.argv[1:]
    if args:
        chunk_size = int(args[0])
        chunk_overlap = int(args[1]) if len(args) > 1 else max(chunk_size // 10, 1)
        collection_name = args[2] if len(args) > 2 else f"taskflow_docs_{chunk_size}"
        main(chunk_size, chunk_overlap, collection_name)
    else:
        main()
