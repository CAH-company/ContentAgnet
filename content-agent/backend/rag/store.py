import chromadb
import os
import tiktoken
import voyageai

chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8000"))
)

collection = chroma_client.get_or_create_collection(
    name="company_knowledge",
    metadata={"hnsw:space": "cosine"}
)

_voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
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


def add_document(name: str, content: str, doc_type: str, user_id: str) -> int:
    chunks = chunk_text(content)
    embeddings = _voyage.embed(chunks, model="voyage-3-lite", input_type="document").embeddings

    collection.upsert(
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
    user_count = collection.count()
    if user_count == 0:
        return []

    # Sprawdź ile chunków ma ten user
    user_docs = collection.get(where={"user_id": user_id})
    if not user_docs["ids"]:
        return []

    query_embedding = _voyage.embed([query], model="voyage-3-lite", input_type="query").embeddings[0]

    results = collection.query(
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
    results = collection.get(where={"$and": [{"source": name}, {"user_id": user_id}]})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def list_documents(user_id: str) -> list[dict]:
    results = collection.get(where={"user_id": user_id}, include=["metadatas"])
    seen = {}
    for meta in results["metadatas"]:
        src = meta["source"]
        if src not in seen:
            seen[src] = {"source": src, "doc_type": meta["doc_type"]}
    return list(seen.values())
