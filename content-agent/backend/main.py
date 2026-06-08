from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from redis import Redis
from rq import Queue

from db.supabase_client import supabase
from rag.store import add_document, delete_document, list_documents

load_dotenv()

app = FastAPI(title="Content Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
task_queue = Queue("content", connection=redis_conn)


class CreateTaskRequest(BaseModel):
    topic: str
    platform: str
    post_type: str

class ReviseTaskRequest(BaseModel):
    comment: str

class AddDocumentRequest(BaseModel):
    name: str
    content: str
    doc_type: str


@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest):
    result = supabase.table("tasks").insert({
        "topic": request.topic,
        "platform": request.platform,
        "post_type": request.post_type,
        "status": "pending"
    }).execute()

    task_id = result.data[0]["id"]
    task_queue.enqueue("worker.run_agent_task", task_id)

    return {"task_id": task_id, "status": "pending"}


@app.get("/api/tasks")
async def get_tasks():
    result = supabase.table("tasks")\
        .select("*")\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    result = supabase.table("tasks")\
        .select("*")\
        .eq("id", task_id)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Zadanie nie znalezione")

    return result.data


@app.post("/api/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    supabase.table("tasks").update({
        "status": "published",
        "ready_to_publish": True
    }).eq("id", task_id).execute()

    return {"status": "published", "message": "Post zatwierdzony i oznaczony do publikacji"}


@app.post("/api/tasks/{task_id}/revise")
async def revise_task(task_id: str, request: ReviseTaskRequest):
    current = supabase.table("tasks").select("iteration")\
        .eq("id", task_id).single().execute()
    current_iteration = current.data["iteration"]

    supabase.table("tasks").update({
        "status": "pending",
        "user_comment": request.comment,
        "iteration": current_iteration + 1
    }).eq("id", task_id).execute()

    task_queue.enqueue("worker.run_agent_task", task_id, revision=True)

    return {"status": "pending", "message": "Wysłano do poprawki"}


@app.post("/api/rag/documents")
async def add_rag_document(request: AddDocumentRequest):
    chunk_count = add_document(
        name=request.name,
        content=request.content,
        doc_type=request.doc_type
    )

    supabase.table("rag_documents").insert({
        "name": request.name,
        "content": request.content,
        "doc_type": request.doc_type,
        "chunk_count": chunk_count
    }).execute()

    return {"message": f"Dodano dokument ({chunk_count} chunków)"}


@app.post("/api/rag/documents/upload")
async def upload_rag_file(
    file: UploadFile = File(...),
    doc_type: str = "company_info"
):
    content = await file.read()

    if file.filename.endswith(".pdf"):
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() for page in reader.pages)
    else:
        text = content.decode("utf-8")

    chunk_count = add_document(
        name=file.filename,
        content=text,
        doc_type=doc_type
    )

    supabase.table("rag_documents").insert({
        "name": file.filename,
        "content": text[:500] + "...",
        "doc_type": doc_type,
        "chunk_count": chunk_count
    }).execute()

    return {"message": f"Wgrano {file.filename} ({chunk_count} chunków)"}


@app.get("/api/rag/documents")
async def get_rag_documents():
    result = supabase.table("rag_documents")\
        .select("id, name, doc_type, chunk_count, created_at")\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@app.delete("/api/rag/documents/{doc_id}")
async def delete_rag_document(doc_id: str):
    doc = supabase.table("rag_documents").select("name")\
        .eq("id", doc_id).single().execute()

    if doc.data:
        delete_document(doc.data["name"])

    supabase.table("rag_documents").delete().eq("id", doc_id).execute()
    return {"message": "Dokument usunięty"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
