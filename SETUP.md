# ContentAgent — instrukcja wdrożenia

## Wymagane konta i klucze API

| Serwis | Do czego | Darmowy tier |
|--------|----------|--------------|
| [Anthropic](https://console.anthropic.com) | Model AI (agenci) | Pay-as-you-go |
| [Voyage AI](https://dash.voyageai.com) | Embeddingi RAG | 50M tokenów/mies. |
| [Tavily](https://app.tavily.com) | Wyszukiwarka dla agentów | 1000 zapytań/mies. |
| [Supabase](https://supabase.com) | Baza danych | Free tier |
| [Vercel](https://vercel.com) | Frontend | Free tier |

---

## 1. Supabase — baza danych

1. Utwórz nowy projekt na [supabase.com](https://supabase.com)
2. Wejdź w **SQL Editor** i uruchom całą zawartość pliku `content-agent/supabase/schema.sql`
3. Zapisz z ustawień projektu:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY`

### Migracja (jeśli baza już istnieje)

```sql
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_platform_check;
ALTER TABLE tasks ADD CONSTRAINT tasks_platform_check
  CHECK (platform IN ('blog','linkedin','twitter','facebook','instagram'));

ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_post_type_check;
ALTER TABLE tasks ADD CONSTRAINT tasks_post_type_check
  CHECK (post_type IN ('article','short_post','newsletter','carousel'));
```

---

## 2. Serwer VPS — backend

### Wymagania
- Docker + Docker Compose
- Git

### Pierwsze uruchomienie

```bash
git clone https://github.com/CAH-company/ContentAgnet.git
cd ContentAgnet/content-agent

cp backend/.env.example backend/.env
nano backend/.env          # uzupełnij wszystkie klucze
```

### Zawartość `backend/.env`

```
API_SECRET_KEY=wygeneruj-dlugi-losowy-ciag-znakow
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
TAVILY_API_KEY=tvly-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
REDIS_URL=redis://redis:6379
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CORS_ORIGINS=https://twoj-projekt.vercel.app,http://localhost:3000
```

### Uruchomienie

```bash
docker-compose build
docker-compose up -d
```

### Sprawdzenie

```bash
docker-compose ps               # wszystkie kontenery "Up"
docker-compose logs api         # api startuje bez błędów
docker-compose logs worker      # worker gotowy
curl http://localhost:8000/api/health  # {"status":"ok"}
```

### Update (po zmianach w repo)

```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 3. Frontend — Vercel

1. Zaimportuj repo na [vercel.com](https://vercel.com)
2. Ustaw **Root Directory**: `content-agent/frontend`
3. Dodaj zmienne środowiskowe w ustawieniach projektu:

```
NEXT_PUBLIC_API_URL=https://twoja-domena.pl
NEXT_PUBLIC_API_SECRET_KEY=ten-sam-co-API_SECRET_KEY-w-backendzie
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

4. Deploy — Vercel automatycznie builduje po każdym pushu na `main`

---

## 4. Nginx (opcjonalnie, jeśli własna domena na VPS)

Edytuj `nginx/nginx.conf` — zamień `TWOJA_DOMENA` na rzeczywistą domenę, następnie:

```bash
apt install nginx certbot python3-certbot-nginx
certbot --nginx -d twoja-domena.pl
cp nginx/nginx.conf /etc/nginx/sites-available/content-agent
ln -s /etc/nginx/sites-available/content-agent /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## 5. Po wdrożeniu — wgraj dokumenty RAG

Wejdź na frontend → zakładka **RAG / Baza wiedzy** i wgraj:

| Typ | Co wgrać |
|-----|----------|
| `brand_voice` | Opis tonu marki, jak firma komunikuje się z odbiorcami |
| `company_info` | Opis firmy, produktów, usług |
| `example_post` | Przykładowe posty które się sprawdziły |
| `keywords` | Słowa kluczowe, frazy SEO |

Im więcej i lepszych dokumentów, tym lepszy content generują agenci.

---

## Architektura

```
Vercel (Next.js)
    ↓ HTTPS
VPS: Nginx
    ↓
    ├── FastAPI (port 8000)    — API, kolejkowanie zadań
    ├── RQ Worker              — uruchamia agentów CrewAI
    ├── Redis                  — kolejka zadań
    └── ChromaDB               — wektory RAG

Supabase                       — baza danych (zadania, dokumenty)
Anthropic API                  — modele Claude (agenci)
Voyage AI API                  — embeddingi semantyczne
Tavily API                     — wyszukiwanie internetowe dla agentów
```
