""" Load Taskflwo docs,chunk,embed and store in ChromaDB"""


import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")


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
            with open(os.path.join(docs_dir, filename), "r", encoding="utf-8") as f:
                content = f.read()
                docs.append({"filename": filename, "content": content})
    
    return docs


def chunk_docs(docs: list[dict]) -> tuple[list[str], list[dict]]:
    """Split docs into chunks.
    
    Returns:
        texts: list of chunk strings
        metadatas: list of dicts with "source" key (the filename)
    """
    # TODO 2:
    # Create a splitter:
    #   splitter = RecursiveCharacterTextSplitter(
    #       chunk_size=500,
    #       chunk_overlap=50,
    #       length_function=len,   # character-based for now
    #   )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
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

def store_in_chroma(texts: list[str], metadatas: list[dict]) -> None:
    """Embed and store chunks in ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name="taskflow_docs")
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=[f"chunk_{i}" for i in range(len(texts))],
    )
    print(f"Stored {collection.count()} chunks in taskflow_docs.")

def main():
    print("Loading docs...")
    docs = load_docs(DOCS_DIR)
    print(f"Loaded {len(docs)} documents.")

    print("Chunking...")
    texts, metadatas = chunk_docs(docs)
    print(f"Created {len(texts)} chunks.")

    print("Storing in ChromaDB...")
    store_in_chroma(texts, metadatas)
    print("Done!")


if __name__ == "__main__":
    main()