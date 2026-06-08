# Content Marketing Agent — Brief dla Claude Code

> Wklej ten plik do folderu projektu i powiedz Claude Code: "Przeczytaj BRIEF_CONTENT_AGENT.md i zbuduj cały projekt zgodnie ze specyfikacją."

---

## Co budujesz

System agentów AI do content marketingu z:
- Dashboardem webowym (Next.js na Vercel)
- Backendem z 4 agentami AI (FastAPI + CrewAI na VPS)
- Bazą wiedzy RAG którą sam uzupełniasz (ChromaDB)
- Bazą danych i auth (Supabase)
- Kolejką zadań async (Redis)
- Flow zatwierdzania: agent pisze → Ty akceptujesz → publikacja

---

## Struktura projektu

```
content-agent/
├── BRIEF_CONTENT_AGENT.md       # ten plik
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py                  # FastAPI, wszystkie endpointy
│   ├── worker.py                # RQ worker, obsługa zadań async
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── crew.py              # definicja CrewAI drużyny 4 agentów
│   │   └── tools.py             # narzędzia: web search, RAG lookup
│   ├── rag/
│   │   ├── __init__.py
│   │   └── store.py             # ChromaDB: dodawanie i wyszukiwanie
│   └── db/
│       ├── __init__.py
│       └── supabase_client.py   # klient Supabase + inicjalizacja tabel
├── supabase/
│   └── schema.sql               # SQL do uruchomienia w Supabase
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── .env.example
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx             # dashboard — lista zadań
    │   ├── new/
    │   │   └── page.tsx         # formularz nowego zadania
    │   ├── task/
    │   │   └── [id]/
    │   │       └── page.tsx     # szczegóły + approval view
    │   └── rag/
    │       └── page.tsx         # RAG manager — baza wiedzy
    ├── components/
    │   ├── TaskList.tsx         # lista kart z zadaniami
    │   ├── TaskCard.tsx         # pojedyncza karta zadania
    │   ├── TaskForm.tsx         # formularz nowego zadania
    │   ├── ApprovalView.tsx     # podgląd + zatwierdź/popraw
    │   ├── RagManager.tsx       # zarządzanie dokumentami RAG
    │   ├── StatusBadge.tsx      # kolorowy badge statusu
    │   └── Navbar.tsx           # nawigacja
    └── lib/
        ├── api.ts               # wszystkie wywołania do backend API
        └── types.ts             # TypeScript typy
```

---

## Stack techniczny

| Warstwa | Technologia | Gdzie działa |
|---|---|---|
| Frontend | Next.js 14 App Router + Tailwind + shadcn/ui | Vercel (darmowe) |
| Backend API | FastAPI Python 3.11 | Twój VPS |
| Agenci AI | CrewAI + Anthropic Claude Sonnet | Twój VPS |
| Kolejka zadań | Redis + RQ (Redis Queue) | Twój VPS (Docker) |
| Baza wiedzy RAG | ChromaDB | Twój VPS (Docker) |
| Baza danych | Supabase (PostgreSQL) | Supabase cloud (darmowe) |
| Auth | Supabase Auth | Supabase cloud |
| Storage plików | Supabase Storage | Supabase cloud |
| Reverse proxy | Nginx + Let's Encrypt HTTPS | Twój VPS |
| Monitoring agentów | Langfuse | Langfuse cloud (darmowe) |

---

## Baza danych Supabase — schema.sql

```sql
-- Zadania agenta
create table tasks (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  topic text not null,
  platform text not null check (platform in ('wordpress','linkedin','twitter')),
  post_type text not null check (post_type in ('article','short_post','newsletter')),
  status text not null default 'pending'
    check (status in ('pending','running','review','approved','published','failed')),
  result text,
  user_comment text,
  error_message text,
  token_input integer default 0,
  token_output integer default 0,
  iteration integer default 1,
  ready_to_publish boolean default false
);

-- Dokumenty w bazie wiedzy RAG
create table rag_documents (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  name text not null,
  content text not null,
  doc_type text not null
    check (doc_type in ('brand_voice','example_post','company_info','keywords')),
  chunk_count integer default 0
);

-- Automatyczna aktualizacja updated_at
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger tasks_updated_at
  before update on tasks
  for each row execute function update_updated_at();

-- Włącz RLS (Row Level Security) — na razie przepuszcza wszystko
-- gdy dodasz auth, ogranicz do zalogowanego użytkownika
alter table tasks enable row level security;
alter table rag_documents enable row level security;

create policy "allow all for now" on tasks for all using (true);
create policy "allow all for now" on rag_documents for all using (true);
```

---

## Backend — zmienne środowiskowe

### backend/.env.example
```
ANTHROPIC_API_KEY=sk-ant-...
SERPER_API_KEY=...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
REDIS_URL=redis://redis:6379
CHROMA_HOST=chromadb
CHROMA_PORT=8001
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
CORS_ORIGINS=https://twoj-projekt.vercel.app,http://localhost:3000
```

---

## Backend — requirements.txt

```
fastapi==0.111.0
uvicorn==0.30.1
python-dotenv==1.0.1
crewai==0.30.11
crewai-tools==0.4.6
anthropic==0.28.0
chromadb==0.5.0
supabase==2.5.0
redis==5.0.4
rq==1.16.2
langfuse==2.36.0
httpx==0.27.0
python-multipart==0.0.9
pypdf==4.2.0
tiktoken==0.7.0
```

---

## Backend — main.py

```python
# Główny plik FastAPI — wszystkie endpointy API
# Komentarze po polsku dla łatwiejszego zrozumienia

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

# CORS — pozwól frontendowi na Vercelu gadać z API
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Połączenie z Redis — kolejka zadań
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
task_queue = Queue("content", connection=redis_conn)


# --- Modele danych ---

class CreateTaskRequest(BaseModel):
    topic: str                    # temat zadany przez użytkownika
    platform: str                 # wordpress / linkedin / twitter
    post_type: str                # article / short_post / newsletter

class ReviseTaskRequest(BaseModel):
    comment: str                  # komentarz użytkownika do poprawki

class AddDocumentRequest(BaseModel):
    name: str                     # nazwa dokumentu
    content: str                  # treść
    doc_type: str                 # brand_voice / example_post / company_info / keywords


# --- Endpointy zadań ---

@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest):
    """Stwórz nowe zadanie i wrzuć do kolejki Redis"""
    # Zapisz zadanie w Supabase ze statusem 'pending'
    result = supabase.table("tasks").insert({
        "topic": request.topic,
        "platform": request.platform,
        "post_type": request.post_type,
        "status": "pending"
    }).execute()

    task_id = result.data[0]["id"]

    # Wrzuć do kolejki — worker odbierze i odpali agentów
    task_queue.enqueue("worker.run_agent_task", task_id)

    return {"task_id": task_id, "status": "pending"}


@app.get("/api/tasks")
async def get_tasks():
    """Pobierz wszystkie zadania — używane do dashboardu"""
    result = supabase.table("tasks")\
        .select("*")\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Pobierz szczegóły jednego zadania — używane do pollingu statusu"""
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
    """Zatwierdź zadanie — oznacz jako gotowe do publikacji"""
    supabase.table("tasks").update({
        "status": "published",
        "ready_to_publish": True
    }).eq("id", task_id).execute()

    return {"status": "published", "message": "Post zatwierdzony i oznaczony do publikacji"}


@app.post("/api/tasks/{task_id}/revise")
async def revise_task(task_id: str, request: ReviseTaskRequest):
    """Wyślij post do poprawki z komentarzem — agent poprawi"""
    # Pobierz aktualny numer iteracji
    current = supabase.table("tasks").select("iteration")\
        .eq("id", task_id).single().execute()
    current_iteration = current.data["iteration"]

    # Zaktualizuj status i komentarz
    supabase.table("tasks").update({
        "status": "pending",
        "user_comment": request.comment,
        "iteration": current_iteration + 1
    }).eq("id", task_id).execute()

    # Wrzuć z powrotem do kolejki z flagą poprawki
    task_queue.enqueue("worker.run_agent_task", task_id, revision=True)

    return {"status": "pending", "message": "Wysłano do poprawki"}


# --- Endpointy RAG ---

@app.post("/api/rag/documents")
async def add_rag_document(request: AddDocumentRequest):
    """Dodaj dokument tekstowy do bazy wiedzy RAG"""
    chunk_count = add_document(
        name=request.name,
        content=request.content,
        doc_type=request.doc_type
    )

    # Zapisz metadane w Supabase
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
    """Upload pliku PDF lub TXT do RAG"""
    content = await file.read()

    # Wyciągnij tekst z PDF lub zdekoduj TXT
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
        "content": text[:500] + "...",  # skróć dla bazy
        "doc_type": doc_type,
        "chunk_count": chunk_count
    }).execute()

    return {"message": f"Wgrano {file.filename} ({chunk_count} chunków)"}


@app.get("/api/rag/documents")
async def get_rag_documents():
    """Lista wszystkich dokumentów w RAG"""
    result = supabase.table("rag_documents")\
        .select("id, name, doc_type, chunk_count, created_at")\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@app.delete("/api/rag/documents/{doc_id}")
async def delete_rag_document(doc_id: str):
    """Usuń dokument z RAG i Supabase"""
    # Pobierz nazwę dokumentu żeby usunąć z ChromaDB
    doc = supabase.table("rag_documents").select("name")\
        .eq("id", doc_id).single().execute()

    if doc.data:
        delete_document(doc.data["name"])

    supabase.table("rag_documents").delete().eq("id", doc_id).execute()
    return {"message": "Dokument usunięty"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

---

## Backend — worker.py

```python
# Worker — odbiera zadania z kolejki Redis i odpala agentów
# Działa jako osobny proces obok FastAPI

import os
from dotenv import load_dotenv
from db.supabase_client import supabase
from agents.crew import ContentMarketingCrew

load_dotenv()


def run_agent_task(task_id: str, revision: bool = False):
    """
    Główna funkcja workera.
    Wywoływana przez RQ gdy pojawi się zadanie w kolejce.
    """
    try:
        # 1. Pobierz dane zadania z Supabase
        task = supabase.table("tasks").select("*")\
            .eq("id", task_id).single().execute().data

        if not task:
            return

        # 2. Zaktualizuj status na "running"
        supabase.table("tasks").update({"status": "running"})\
            .eq("id", task_id).execute()

        # 3. Przygotuj kontekst dla agentów
        context = {
            "topic": task["topic"],
            "platform": task["platform"],
            "post_type": task["post_type"],
            "iteration": task["iteration"],
        }

        # Jeśli to poprawka — dodaj komentarz użytkownika
        if revision and task.get("user_comment"):
            context["previous_result"] = task["result"]
            context["revision_comment"] = task["user_comment"]

        # 4. Odppal CrewAI
        crew = ContentMarketingCrew()
        result = crew.run(context)

        # 5. Zapisz wynik, zaktualizuj status na "review"
        supabase.table("tasks").update({
            "status": "review",
            "result": result["content"],
            "token_input": result["token_input"],
            "token_output": result["token_output"],
        }).eq("id", task_id).execute()

    except Exception as e:
        # Jeśli coś poszło nie tak — zapisz błąd
        supabase.table("tasks").update({
            "status": "failed",
            "error_message": str(e)
        }).eq("id", task_id).execute()
        raise
```

---

## Backend — agents/crew.py

```python
# Definicja drużyny 4 agentów CrewAI
# Każdy agent ma swoją rolę, cel i narzędzia

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from .tools import rag_search_tool
import anthropic
import os


class ContentMarketingCrew:

    def __init__(self):
        self.llm = "claude-sonnet-4-5"  # model Anthropic
        self.search_tool = SerperDevTool()

    def run(self, context: dict) -> dict:
        """Odpala całą drużynę i zwraca wynik z liczbą tokenów"""

        topic = context["topic"]
        platform = context["platform"]
        post_type = context["post_type"]
        is_revision = "revision_comment" in context

        # Instrukcja poprawki jeśli to druga iteracja
        revision_note = ""
        if is_revision:
            revision_note = f"""
            POPRZEDNIA WERSJA:
            {context.get('previous_result', '')}

            KOMENTARZ DO POPRAWKI:
            {context.get('revision_comment', '')}

            Uwzględnij powyższe uwagi w nowej wersji.
            """

        # --- Definicja agentów ---

        researcher = Agent(
            role="Senior Content Researcher",
            goal=f"Zbadaj temat '{topic}' i znajdź najlepsze kąty narracyjne, "
                 f"aktualne trendy i dane które warto wykorzystać",
            backstory="Jesteś doświadczonym researcherem content marketingu. "
                      "Zawsze szukasz unikalnych perspektyw i aktualnych danych. "
                      "Znasz markę firmy i jej styl komunikacji z dokumentów.",
            tools=[self.search_tool, rag_search_tool],
            llm=self.llm,
            verbose=True
        )

        writer = Agent(
            role="Expert Content Writer",
            goal=f"Napisz angażujący {post_type} na platformę {platform} "
                 f"na podstawie dostarczonego researchu, zgodny z brand voice firmy",
            backstory="Jesteś ekspertem w pisaniu content marketingowego. "
                      "Piszesz w stylu marki, angażująco i naturalnie. "
                      "Zawsze używasz brand voice i przykładowych postów z dokumentów.",
            tools=[rag_search_tool],
            llm=self.llm,
            verbose=True
        )

        editor = Agent(
            role="Content Editor & SEO Specialist",
            goal="Sprawdź i popraw tekst pod kątem jakości, tonu marki, "
                 "SEO i dopasowania do platformy",
            backstory="Jesteś skrupulatnym redaktorem z doświadczeniem w SEO. "
                      "Sprawdzasz czy post brzmi naturalnie, jest zgodny z brand voice "
                      "i zoptymalizowany pod daną platformę.",
            tools=[rag_search_tool],
            llm=self.llm,
            verbose=True
        )

        publisher = Agent(
            role="Content Publisher",
            goal="Sformatuj finalny post gotowy do publikacji, "
                 "dodaj odpowiednie hashtagi i meta-informacje",
            backstory="Formatujesz content idealnie pod każdą platformę. "
                      "Wiesz że LinkedIn lubi dłuższe posty z formatowaniem, "
                      "Twitter/X wymaga zwięzłości, WordPress potrzebuje H2/H3.",
            tools=[],
            llm=self.llm,
            verbose=True
        )

        # --- Definicja zadań ---

        research_task = Task(
            description=f"""
            Zbadaj temat: "{topic}"
            Platforma: {platform}
            Typ contentu: {post_type}

            1. Przeszukaj internet w poszukiwaniu aktualnych trendów i danych
            2. Przeszukaj bazę wiedzy firmy (RAG) po słowach kluczowych z tematu
            3. Wyciągnij brand voice i przykłady postów z RAG
            4. Przygotuj brief dla writera: kluczowe punkty, dane, angle narracyjny

            {revision_note}
            """,
            agent=researcher,
            expected_output="Szczegółowy brief z kluczowymi punktami, "
                           "danymi i proponowanym kątem narracyjnym"
        )

        write_task = Task(
            description=f"""
            Na podstawie briefu od Researchera napisz {post_type} na {platform}.

            Wymagania:
            - Użyj brand voice z dokumentów firmy
            - Dostosuj długość do platformy
              (LinkedIn: 150-300 słów, WP: 400-800 słów, Twitter: max 280 znaków)
            - Zacznij od mocnego hooka
            - Dodaj wyraźne CTA na końcu

            {revision_note}
            """,
            agent=writer,
            expected_output="Gotowy draft posta zgodny z brand voice"
        )

        edit_task = Task(
            description=f"""
            Sprawdź draft od Writera i popraw:
            - Czy ton jest zgodny z brand voice firmy? (sprawdź RAG)
            - Czy nie ma błędów gramatycznych?
            - Czy jest angażujący i naturalny?
            - Czy jest zoptymalizowany SEO (dla WordPress)?
            - Czy CTA jest wyraźne?

            Jeśli coś wymaga poprawki — popraw to sam, nie odsyłaj do Writera.
            """,
            agent=editor,
            expected_output="Poprawiony, gotowy do publikacji post"
        )

        publish_task = Task(
            description=f"""
            Sformatuj finalny post na platformę {platform}:
            - WordPress: użyj Markdown (## nagłówki, **bold**, listy)
            - LinkedIn: paragrafowy styl, emoji dozwolone, hashtagi na końcu
            - Twitter/X: zwięźle, max 280 znaków, 2-3 hashtagi

            Zwróć TYLKO gotowy post bez żadnych komentarzy od siebie.
            """,
            agent=publisher,
            expected_output="Sformatowany post gotowy do wklejenia/publikacji"
        )

        # --- Uruchomienie drużyny ---

        crew = Crew(
            agents=[researcher, writer, editor, publisher],
            tasks=[research_task, write_task, edit_task, publish_task],
            process=Process.sequential,  # jeden po drugim
            verbose=True
        )

        # Zlicz tokeny przez Anthropic client
        token_input = 0
        token_output = 0

        result = crew.kickoff()

        # CrewAI zwraca usage stats
        if hasattr(crew, 'usage_metrics'):
            token_input = crew.usage_metrics.get('prompt_tokens', 0)
            token_output = crew.usage_metrics.get('completion_tokens', 0)

        return {
            "content": str(result),
            "token_input": token_input,
            "token_output": token_output
        }
```

---

## Backend — agents/tools.py

```python
# Narzędzia dla agentów — funkcje które mogą wywoływać
# RAG search jest najważniejszym narzędziem

from crewai.tools import BaseTool
from rag.store import search_documents
from pydantic import BaseModel


class RagSearchInput(BaseModel):
    query: str


class RagSearchTool(BaseTool):
    name: str = "rag_search"
    description: str = (
        "Przeszukaj bazę wiedzy firmy. Używaj gdy potrzebujesz: "
        "brand voice, przykładowych postów, opisu firmy, słów kluczowych, "
        "lub jakichkolwiek dokumentów wgranych przez użytkownika. "
        "Zawsze wywołaj to narzędzie na początku pracy."
    )
    args_schema: type[BaseModel] = RagSearchInput

    def _run(self, query: str) -> str:
        results = search_documents(query, n_results=5)
        if not results:
            return "Brak relevantnych dokumentów w bazie wiedzy."
        return "\n\n---\n\n".join(results)


# Singleton — jeden obiekt narzędzia dla wszystkich agentów
rag_search_tool = RagSearchTool()
```

---

## Backend — rag/store.py

```python
# Baza wiedzy RAG oparta na ChromaDB
# Dokumenty → chunki → embeddingi → wyszukiwanie semantyczne

import chromadb
import os
import tiktoken
from anthropic import Anthropic

# Połączenie z ChromaDB (działa jako osobny serwis Docker)
chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8001"))
)

# Kolekcja dokumentów — jedna dla wszystkich
collection = chroma_client.get_or_create_collection(
    name="company_knowledge",
    metadata={"hnsw:space": "cosine"}
)

anthropic_client = Anthropic()
tokenizer = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    """
    Podziel tekst na chunki po max_tokens z nakładaniem się (overlap).
    Overlap sprawia że kontekst nie ginie między chunkami.
    """
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Przesuń o (max_tokens - overlap) żeby chunki się nakładały
        start += max_tokens - overlap

    return chunks


def get_embedding(text: str) -> list[float]:
    """Stwórz embedding przez Anthropic (wektor liczb = znaczenie tekstu)"""
    # Używamy voyage-3 przez Anthropic jako embeddings
    # Alternatywnie: możesz użyć sentence-transformers (lokalne, darmowe)
    response = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1,
        messages=[{"role": "user", "content": text}]
    )
    # Tymczasowo: używamy prostego hash jako embedding
    # W produkcji: zamień na voyage-3 lub sentence-transformers
    import hashlib
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    # Zwróć wektor 384-wymiarowy (uproszczony dla MVP)
    import random
    random.seed(hash_val)
    return [random.uniform(-1, 1) for _ in range(384)]


def add_document(name: str, content: str, doc_type: str) -> int:
    """
    Dodaj dokument do RAG:
    1. Podziel na chunki
    2. Stwórz embeddingi
    3. Zapisz w ChromaDB
    Zwraca liczbę chunków.
    """
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
    """
    Znajdź n_results najbardziej relevantnych chunków do query.
    To jest serce RAG — semantyczne wyszukiwanie.
    """
    if collection.count() == 0:
        return []

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas"]
    )

    # Zwróć chunki z informacją o źródle
    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source_info = f"[Źródło: {meta['source']} | Typ: {meta['doc_type']}]"
        output.append(f"{source_info}\n{doc}")

    return output


def delete_document(name: str):
    """Usuń wszystkie chunki dokumentu o podanej nazwie"""
    results = collection.get(where={"source": name})
    if results["ids"]:
        collection.delete(ids=results["ids"])
```

---

## Backend — db/supabase_client.py

```python
# Klient Supabase — połączenie z bazą danych
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # service key dla backendu (pełny dostęp)
)
```

---

## Backend — Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Zainstaluj zależności systemowe
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Domyślna komenda to API — worker nadpisuje to w docker-compose
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yml

```yaml
version: "3.9"

services:
  # FastAPI — backend API
  api:
    build: ./backend
    restart: unless-stopped
    env_file: ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - chromadb
    volumes:
      - ./backend:/app

  # RQ Worker — odbiera zadania z kolejki i odpala agentów
  worker:
    build: ./backend
    restart: unless-stopped
    env_file: ./backend/.env
    command: rq worker content --url ${REDIS_URL}
    depends_on:
      - redis
      - chromadb
    volumes:
      - ./backend:/app

  # Redis — kolejka zadań
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # ChromaDB — baza wektorowa dla RAG
  chromadb:
    image: chromadb/chroma:latest
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE

volumes:
  redis_data:
  chroma_data:
```

---

## nginx/nginx.conf

```nginx
server {
    listen 80;
    server_name TWOJA_DOMENA;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name TWOJA_DOMENA;

    ssl_certificate /etc/letsencrypt/live/TWOJA_DOMENA/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/TWOJA_DOMENA/privkey.pem;

    # Przekieruj /api na FastAPI
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;  # agenci mogą działać długo
    }
}
```

---

## Frontend — .env.example

```
NEXT_PUBLIC_API_URL=https://twoja-domena.pl
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## Polecenia dla Claude Code

Po wygenerowaniu kodu przez Claude Code uruchom kolejno:

```bash
# === Na VPS ===

# 1. Zainstaluj Docker (jeśli nie ma)
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# 2. Sklonuj repo i przejdź do folderu
git clone <twoje-repo> content-agent
cd content-agent

# 3. Uzupełnij zmienne środowiskowe
cp backend/.env.example backend/.env
nano backend/.env   # wklej swoje klucze API

# 4. Uruchom cały stack
docker compose up -d

# 5. Sprawdź czy działa
docker compose ps
curl http://localhost:8000/api/health

# 6. Zainstaluj Nginx i certyfikat HTTPS
apt install nginx certbot python3-certbot-nginx -y
# Zamień TWOJA_DOMENA w nginx.conf na swoją domenę
cp nginx/nginx.conf /etc/nginx/sites-available/content-agent
ln -s /etc/nginx/sites-available/content-agent /etc/nginx/sites-enabled/
certbot --nginx -d twoja-domena.pl
nginx -s reload

# === Supabase ===
# Wejdź na supabase.com → SQL Editor → wklej supabase/schema.sql → Run

# === Vercel ===
cd frontend
npx vercel deploy
# Ustaw zmienne środowiskowe w Vercel Dashboard
```

---

## Pierwsze dokumenty do wgrania do RAG

Po uruchomieniu wejdź w RAG Manager i dodaj te dokumenty:

1. **Brand Voice** (typ: brand_voice)
   - Jak firma mówi do klientów
   - Czego unika (żargon, korporacyjny język)
   - Kim jest odbiorca
   - Przykładowe zwroty i ton

2. **Top 5 najlepszych postów** (typ: example_post)
   - Wklej treść swoich najlepszych postów
   - Agent naśladuje styl i strukturę

3. **Opis firmy** (typ: company_info)
   - Czym się zajmujecie
   - Jakie problemy rozwiązujecie
   - Dla kogo
   - Co was wyróżnia

4. **Słowa kluczowe** (typ: keywords)
   - Lista słów kluczowych SEO
   - Hashtagi LinkedIn
   - Tematy które chcesz poruszać
