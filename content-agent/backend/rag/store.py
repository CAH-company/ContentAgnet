import chromadb
import os
import tiktoken
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8000"))
)

embedding_fn = DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="company_knowledge",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

tokenizer = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunks.append(tokenizer.decode(tokens[start:end]))
        start += max_tokens - overlap
    return chunks


def add_document(name: str, content: str, doc_type: str) -> int:
    chunks = chunk_text(content)
    collection.upsert(
        ids=[f"{name}_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": name, "doc_type": doc_type, "chunk_index": i} for i in range(len(chunks))]
    )
    return len(chunks)


def search_documents(query: str, n_results: int = 5) -> list[str]:
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas"]
    )

    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append(f"[Źródło: {meta['source']} | Typ: {meta['doc_type']}]\n{doc}")
    return output


def delete_document(name: str):
    results = collection.get(where={"source": name})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def list_documents() -> list[dict]:
    results = collection.get(include=["metadatas"])
    seen = {}
    for meta in results["metadatas"]:
        src = meta["source"]
        if src not in seen:
            seen[src] = {"source": src, "doc_type": meta["doc_type"]}
    return list(seen.values())
