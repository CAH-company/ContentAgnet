from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import os
from dotenv import load_dotenv
from redis import Redis
from rq import Queue

from db.supabase_client import supabase
from rag.store import add_document, delete_document, list_documents, search_documents

load_dotenv()

# Docs wyłączone w produkcji — nie ujawniaj schematu API publicznie
app = FastAPI(title="Content Agent API", docs_url=None, redoc_url=None)

cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
task_queue = Queue("content", connection=redis_conn)

MAX_FILE_SIZE = 8 * 1024 * 1024  # 8 MB
MAX_CONCURRENT_TASKS = 2          # max zadań pending/running na usera
RAG_DOCUMENT_LIMIT = 5            # max dokumentów RAG na usera


# --- Auth ---

async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Brak tokenu autoryzacji")
    token = authorization[len("Bearer "):]
    try:
        resp = supabase.auth.get_user(token)
        user = resp.user
    except Exception:
        raise HTTPException(status_code=401, detail="Nieważny token")

    if not user:
        raise HTTPException(status_code=401, detail="Nieważny token")

    profile = supabase.table("user_profiles").select("role")\
        .eq("id", user.id).single().execute()
    role = profile.data["role"] if profile.data else "user"

    return {"id": user.id, "email": user.email, "role": role}


async def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Tylko administrator")
    return user


# --- Modele ---

class CreateTaskRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    platform: Literal["blog", "linkedin", "twitter", "facebook", "instagram"]
    post_type: Literal["article", "short_post", "newsletter", "carousel"]

class ReviseTaskRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)

class AddDocumentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=100_000)
    doc_type: Literal["brand_voice", "example_post", "company_info", "keywords"]

class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


# --- Zadania ---

@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest, user: dict = Depends(get_current_user)):
    # Ogranicz liczbę jednoczesnych zadań per user
    active = supabase.table("tasks")\
        .select("id", count="exact")\
        .eq("user_id", user["id"])\
        .in_("status", ["pending", "running"])\
        .execute()
    if active.count >= MAX_CONCURRENT_TASKS:
        raise HTTPException(
            status_code=429,
            detail="Masz już zadania w toku — poczekaj aż się zakończą przed dodaniem nowego."
        )

    result = supabase.table("tasks").insert({
        "user_id": user["id"],
        "topic": request.topic,
        "platform": request.platform,
        "post_type": request.post_type,
        "status": "pending"
    }).execute()

    task_id = result.data[0]["id"]
    task_queue.enqueue("worker.run_agent_task", task_id, user["id"])

    return {"task_id": task_id, "status": "pending"}


@app.get("/api/tasks")
async def get_tasks(user: dict = Depends(get_current_user)):
    result = supabase.table("tasks")\
        .select("*")\
        .eq("user_id", user["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    result = supabase.table("tasks")\
        .select("*")\
        .eq("id", task_id)\
        .eq("user_id", user["id"])\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Zadanie nie znalezione")

    return result.data


@app.post("/api/tasks/{task_id}/approve")
async def approve_task(task_id: str, user: dict = Depends(get_current_user)):
    supabase.table("tasks").update({
        "status": "published",
        "ready_to_publish": True
    }).eq("id", task_id).eq("user_id", user["id"]).execute()

    return {"status": "published", "message": "Post zatwierdzony i oznaczony do publikacji"}


@app.post("/api/tasks/{task_id}/revise")
async def revise_task(task_id: str, request: ReviseTaskRequest, user: dict = Depends(get_current_user)):
    current = supabase.table("tasks").select("iteration")\
        .eq("id", task_id).eq("user_id", user["id"]).single().execute()

    if not current.data:
        raise HTTPException(status_code=404, detail="Zadanie nie znalezione")

    supabase.table("tasks").update({
        "status": "pending",
        "user_comment": request.comment,
        "iteration": current.data["iteration"] + 1
    }).eq("id", task_id).eq("user_id", user["id"]).execute()

    task_queue.enqueue("worker.run_agent_task", task_id, user["id"], revision=True)

    return {"status": "pending", "message": "Wysłano do poprawki"}


# --- RAG ---

@app.post("/api/rag/documents")
async def add_rag_document(request: AddDocumentRequest, user: dict = Depends(get_current_user)):
    count_result = supabase.table("rag_documents")\
        .select("id", count="exact")\
        .eq("user_id", user["id"])\
        .execute()
    if count_result.count >= RAG_DOCUMENT_LIMIT:
        raise HTTPException(status_code=400, detail=f"Limit {RAG_DOCUMENT_LIMIT} dokumentów na użytkownika")

    chunk_count = add_document(
        name=request.name,
        content=request.content,
        doc_type=request.doc_type,
        user_id=user["id"]
    )

    supabase.table("rag_documents").insert({
        "user_id": user["id"],
        "name": request.name,
        "content": request.content,
        "doc_type": request.doc_type,
        "chunk_count": chunk_count
    }).execute()

    return {"message": f"Dodano dokument ({chunk_count} chunków)"}


@app.post("/api/rag/documents/upload")
async def upload_rag_file(
    file: UploadFile = File(...),
    doc_type: str = "company_info",
    user: dict = Depends(get_current_user)
):
    if doc_type not in ("brand_voice", "example_post", "company_info", "keywords"):
        raise HTTPException(status_code=400, detail="Nieprawidłowy typ dokumentu")

    count_result = supabase.table("rag_documents")\
        .select("id", count="exact")\
        .eq("user_id", user["id"])\
        .execute()
    if count_result.count >= RAG_DOCUMENT_LIMIT:
        raise HTTPException(status_code=400, detail=f"Limit {RAG_DOCUMENT_LIMIT} dokumentów na użytkownika")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Plik za duży — maksymalnie 8 MB")

    filename = file.filename or "dokument"
    if filename.lower().endswith(".pdf"):
        import io
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Nie udało się odczytać pliku PDF")
    elif filename.lower().endswith((".txt", ".md")):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Plik musi być w kodowaniu UTF-8")
    else:
        raise HTTPException(status_code=400, detail="Dozwolone formaty: PDF, TXT, MD")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Plik jest pusty lub nie zawiera tekstu")

    chunk_count = add_document(
        name=filename,
        content=text,
        doc_type=doc_type,
        user_id=user["id"]
    )

    supabase.table("rag_documents").insert({
        "user_id": user["id"],
        "name": filename,
        "content": text[:500] + "...",
        "doc_type": doc_type,
        "chunk_count": chunk_count
    }).execute()

    return {"message": f"Wgrano {filename} ({chunk_count} chunków)"}


@app.get("/api/rag/documents")
async def get_rag_documents(user: dict = Depends(get_current_user)):
    result = supabase.table("rag_documents")\
        .select("id, name, doc_type, chunk_count, created_at")\
        .eq("user_id", user["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@app.delete("/api/rag/documents/{doc_id}")
async def delete_rag_document(doc_id: str, user: dict = Depends(get_current_user)):
    doc = supabase.table("rag_documents").select("name")\
        .eq("id", doc_id).eq("user_id", user["id"]).single().execute()

    if doc.data:
        delete_document(doc.data["name"], user_id=user["id"])

    supabase.table("rag_documents").delete()\
        .eq("id", doc_id).eq("user_id", user["id"]).execute()
    return {"message": "Dokument usunięty"}


# --- Admin ---

@app.get("/api/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    result = supabase.table("tasks")\
        .select("user_id, token_input, token_output")\
        .execute()

    stats: dict = {}
    for row in result.data:
        uid = row["user_id"]
        if uid not in stats:
            stats[uid] = {"token_input": 0, "token_output": 0}
        stats[uid]["token_input"] += row["token_input"] or 0
        stats[uid]["token_output"] += row["token_output"] or 0

    # claude-sonnet-4-5: $3/M input, $15/M output
    for uid in stats:
        inp = stats[uid]["token_input"]
        out = stats[uid]["token_output"]
        stats[uid]["cost_usd"] = round((inp * 3 + out * 15) / 1_000_000, 4)

    return stats


@app.get("/api/admin/users")
async def list_users(admin: dict = Depends(require_admin)):
    profiles = supabase.table("user_profiles")\
        .select("*")\
        .order("created_at", desc=True)\
        .execute()
    return profiles.data


@app.post("/api/admin/users")
async def create_user(body: CreateUserRequest, admin: dict = Depends(require_admin)):
    try:
        result = supabase.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True
        })
        return {"id": result.user.id, "email": result.user.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Nie możesz usunąć własnego konta")
    try:
        supabase.auth.admin.delete_user(user_id)
        return {"message": "Użytkownik usunięty"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}
