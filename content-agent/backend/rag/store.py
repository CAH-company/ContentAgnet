import chromadb
import os
import time
import tiktoken
import voyageai

_chroma_client = None
_collection = None

_voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
tokenizer = tiktoken.get_encoding("cl100k_base")


def _get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    for attempt in range(12):
        try:
            _chroma_client = chromadb.HttpClient(host=host, port=port)
            _collection = _chroma_client.get_or_create_collection(
                name="company_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            return _collection
        except Exception:
            if attempt == 11:
                raise
            time.sleep(5)


def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunks.append(tokenizer.decode(tokens[start:end]))
        start += max_tokens - overlap
    return chunks


def add_document(name: str, content: str, doc_type: str, user_id: str) -> int:
    chunks = chunk_text(content)
    embeddings = _voyage.embed(chunks, model="voyage-3-lite", input_type="document").embeddings

    _get_collection().upsert(
        ids=[f"{user_id}_{name}_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{
            "source": name,
            "doc_type": doc_type,
            "chunk_index": i,
            "user_id": user_id
        } for i in range(len(chunks))]
    )
    return len(chunks)


def search_documents(query: str, user_id: str, n_results: int = 5) -> list[str]:
    col = _get_collection()
    user_count = col.count()
    if user_count == 0:
        return []

    user_docs = col.get(where={"user_id": user_id})
    if not user_docs["ids"]:
        return []

    query_embedding = _voyage.embed([query], model="voyage-3-lite", input_type="query").embeddings[0]

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, len(user_docs["ids"])),
        where={"user_id": user_id},
        include=["documents", "metadatas"]
    )

    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append(f"[Źródło: {meta['source']} | Typ: {meta['doc_type']}]\n{doc}")
    return output


def delete_document(name: str, user_id: str):
    col = _get_collection()
    results = col.get(where={"$and": [{"source": name}, {"user_id": user_id}]})
    if results["ids"]:
        col.delete(ids=results["ids"])


def list_documents(user_id: str) -> list[dict]:
    results = _get_collection().get(where={"user_id": user_id}, include=["metadatas"])
    seen = {}
    for meta in results["metadatas"]:
        src = meta["source"]
        if src not in seen:
            seen[src] = {"source": src, "doc_type": meta["doc_type"]}
    return list(seen.values())
