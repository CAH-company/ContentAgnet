import chromadb
import os
import tiktoken
import hashlib
import random

chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8001"))
)

collection = chroma_client.get_or_create_collection(
    name="company_knowledge",
    metadata={"hnsw:space": "cosine"}
)

tokenizer = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk = tokenizer.decode(chunk_tokens)
        chunks.append(chunk)
        start += max_tokens - overlap

    return chunks


def get_embedding(text: str) -> list[float]:
    # MVP: hash-based pseudo-embedding (replace with voyage-3 or sentence-transformers in prod)
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    rng = random.Random(hash_val)
    return [rng.uniform(-1, 1) for _ in range(384)]


def add_document(name: str, content: str, doc_type: str) -> int:
    chunks = chunk_text(content)

    for i, chunk in enumerate(chunks):
        chunk_id = f"{name}_{i}"
        embedding = get_embedding(chunk)

        collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{
                "source": name,
                "doc_type": doc_type,
                "chunk_index": i
            }]
        )

    return len(chunks)


def search_documents(query: str, n_results: int = 5) -> list[str]:
    if collection.count() == 0:
        return []

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas"]
    )

    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source_info = f"[Źródło: {meta['source']} | Typ: {meta['doc_type']}]"
        output.append(f"{source_info}\n{doc}")

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
