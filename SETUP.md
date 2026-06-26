# ContentAgent — instrukcja wdrożenia

## Wymagane konta i klucze API

| Serwis | Do czego | Koszt |
|--------|----------|-------|
| [Anthropic](https://console.anthropic.com) | Model AI (agenci CrewAI) | Pay-as-you-go (~$0.03–0.15 / post) |
| [Voyage AI](https://dash.voyageai.com) | Embeddingi RAG | Darmowe 50M tokenów/mies. |
| [Supabase](https://supabase.com) | Baza danych + Auth | Free tier |
| [Vercel](https://vercel.com) | Hosting frontendu | Free tier |
| VPS | Backend + Docker | Twój własny serwer |

> SearXNG (wyszukiwarka dla agentów) działa lokalnie w Docker — nie wymaga żadnego zewnętrznego API.

---

## Krok 1 — Supabase (baza danych i auth)

1. Utwórz nowy projekt na [supabase.com](https://supabase.com)
2. Wejdź w **SQL Editor** → **New query** → wklej całą zawartość pliku `content-agent/supabase/schema.sql` → **Run**
3. Zapisz trzy wartości z **Project Settings → API**:

```
Project URL          → SUPABASE_URL
anon public          → SUPABASE_ANON_KEY
service_role secret  → SUPABASE_SERVICE_KEY
```

> `service_role` jest tajny — używany tylko na backendzie, nigdy nie trafia do frontendu.

---

## Krok 2 — VPS (backend Docker)

### 2.1 — Instalacja Docker (jednorazowo, jeśli nie ma)

```bash
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y
```

### 2.2 — Pobranie repozytorium

```bash
git clone https://github.com/CAH-company/ContentAgent.git
cd ContentAgent/content-agent
```

### 2.3 — Plik `.env` dla backendu

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Uzupełnij wszystkie wartości:

```env
ANTHROPIC_API_KEY=sk-ant-...          # z console.anthropic.com
VOYAGE_API_KEY=pa-...                 # z dash.voyageai.com
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
REDIS_URL=redis://redis:6379
CHROMA_HOST=chromadb
CHROMA_PORT=8000
SEARXNG_URL=http://searxng:8080
SEARXNG_SECRET_KEY=wygeneruj-losowy-dlugi-ciag-min-32-znaki
CORS_ORIGINS=https://twoj-projekt.vercel.app,http://localhost:3000
```

> **SEARXNG_SECRET_KEY** — wygeneruj np. przez: `openssl rand -hex 32`

### 2.4 — Uprawnienia dla SearXNG

```bash
chmod 777 searxng/
```

SearXNG musi mieć możliwość zapisu do tego folderu (tworzy własne pliki cache).

### 2.5 — Uruchomienie

```bash
docker compose build
docker compose up -d
```

### 2.6 — Weryfikacja

```bash
docker compose ps
# Oczekiwany wynik: wszystkie 5 kontenerów w stanie "Up"
# api, worker, redis, chromadb, searxng

curl http://localhost:8000/api/health
# {"status":"ok"}

curl "http://localhost:8080/search?q=test&format=json" | head -c 300
# Powinny pojawić się wyniki JSON — SearXNG działa
# Port 8080 jest dostępny tylko z poziomu VPS (127.0.0.1), nie z internetu
```

### 2.7 — Firewall (zalecane)

Upewnij się że z internetu dostępne są tylko porty 80 i 443. Reszta (8000, 8080, 6379, 8001) jest już na 127.0.0.1, ale warto zablokować na poziomie systemu:

```bash
ufw allow 22      # SSH — KONIECZNIE przed włączeniem UFW
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw enable
ufw status
```

---

## Krok 3 — Nginx + HTTPS (własna domena)

### 3.1 — Instalacja

```bash
apt install nginx certbot python3-certbot-nginx -y
```

### 3.2 — Konfiguracja

Edytuj `nginx/nginx.conf` — zamień `TWOJA_DOMENA` na swoją domenę (np. `agent.twojafirma.pl`).

```bash
cp nginx/nginx.conf /etc/nginx/sites-available/content-agent
ln -s /etc/nginx/sites-available/content-agent /etc/nginx/sites-enabled/
nginx -t                  # sprawdź czy config jest poprawny
systemctl reload nginx
```

### 3.3 — Certyfikat SSL

```bash
certbot --nginx -d twoja-domena.pl
# Postępuj zgodnie z instrukcjami — certbot sam zaktualizuje nginx.conf
systemctl reload nginx
```

### 3.4 — Test HTTPS

```bash
curl https://twoja-domena.pl/api/health
# {"status":"ok"}
```

Jeśli to działa — backend jest publicznie dostępny przez HTTPS.

---

## Krok 4 — Vercel (frontend)

1. Wejdź na [vercel.com](https://vercel.com) → **Add New Project** → zaimportuj repozytorium z GitHub
2. Ustaw **Root Directory**: `content-agent/frontend`
3. Framework: **Next.js** (Vercel wykryje automatycznie)
4. Dodaj zmienne środowiskowe w **Settings → Environment Variables**:

```
NEXT_PUBLIC_API_URL        = https://twoja-domena.pl
NEXT_PUBLIC_SUPABASE_URL   = https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJ...
```

5. Kliknij **Deploy**

Po deploymencie skopiuj URL projektu Vercel (np. `https://content-agent-xyz.vercel.app`) i:
- Dodaj go do `CORS_ORIGINS` w `backend/.env` na VPS
- Uruchom `docker compose restart api` żeby załadować nową wartość

---

## Krok 5 — Tworzenie pierwszego admina

Panel admina do tworzenia użytkowników jest dostępny tylko przez konto z rolą `admin`. Pierwszego admina trzeba ustawić ręcznie.

### 5.1 — Utwórz konto w Supabase

Wejdź na [supabase.com](https://supabase.com) → Twój projekt → **Authentication → Users → Add user**.

Wpisz swój email i hasło. Kliknij **Create User**.

### 5.2 — Nadaj rolę admin przez SQL

W **SQL Editor** wykonaj (zamień email na swój):

```sql
UPDATE user_profiles
SET role = 'admin'
WHERE email = 'twoj@email.com';
```

### 5.3 — Zaloguj się do aplikacji

Wejdź na frontend → zaloguj się swoim emailem i hasłem.

W nawigacji pojawi się zakładka **Admin**. Przez nią możesz tworzyć konta dla testujących użytkowników (email + hasło).

---

## Krok 6 — Pierwsze dokumenty RAG

Każdy użytkownik (łącznie z Tobą) musi wgrać swoje dokumenty do bazy wiedzy — **limit 3 dokumenty na użytkownika**.

Wejdź na frontend → **Baza wiedzy** i wgraj:

| Typ | Co wgrać | Format |
|-----|----------|--------|
| `brand_voice` | Jak firma komunikuje się z odbiorcami, czego unika, kim jest odbiorca | TXT lub PDF |
| `company_info` | Opis firmy, produktów, usług, wyróżniki | TXT lub PDF |
| `example_post` | 3–5 przykładowych postów które się sprawdziły | TXT |

> Skoro limit to 3 dokumenty, warto połączyć `keywords` z `company_info` w jeden plik.

---

## Zarządzanie serwerem

### Update po zmianach w kodzie

```bash
git pull origin main
docker compose build
docker compose up -d
```

### Logi

```bash
docker compose logs -f api        # logi backendu
docker compose logs -f worker     # logi agentów (tu zobaczysz co robią)
docker compose logs -f searxng    # logi wyszukiwarki
```

### Restart pojedynczego serwisu

```bash
docker compose restart api
docker compose restart worker
```

### Stop / start

```bash
docker compose down               # zatrzymaj wszystko (dane zostają w volumes)
docker compose up -d              # uruchom ponownie
```

### Sprawdzenie SearXNG

```bash
# Test wyszukiwania z poziomu VPS:
curl "http://localhost:8080/search?q=AI+content+marketing&format=json" | python3 -m json.tool | head -40
```

---

## Architektura

```
Vercel (Next.js)
    ↓ HTTPS + Supabase JWT
Nginx :80/:443 [publiczny]
    ↓
    ├─ FastAPI :8000       [tylko localhost] — API, auth JWT, kolejkowanie
    ├─ RQ Worker           — uruchamia agentów CrewAI
    ├─ Redis :6379         [tylko localhost] — kolejka zadań
    ├─ ChromaDB :8001      [tylko localhost] — wektory RAG (izolowane per user)
    └─ SearXNG :8080       [tylko localhost] — wyszukiwarka (nigdy z internetu)
         ├─ Bing
         ├─ DuckDuckGo
         ├─ Brave Search
         ├─ Startpage (proxy Google, bez ryzyka bana)
         └─ Qwant

Supabase Cloud
    ├─ PostgreSQL          — zadania, dokumenty RAG, profile userów
    └─ Auth                — logowanie email/hasło, JWT tokeny

Zewnętrzne API
    ├─ Anthropic           — modele Claude (agenci)
    └─ Voyage AI           — embeddingi semantyczne dla RAG
```

### Przepływ auth

```
User loguje się → Supabase zwraca JWT token
Frontend → każde żądanie do API: Authorization: Bearer <token>
Backend → weryfikuje token przez Supabase → wyciąga user_id
Backend → filtruje dane po user_id (każdy widzi tylko swoje)
```

---

## Rozwiązywanie problemów

**Backend nie startuje:**
```bash
docker compose logs api
# Najczęstszy powód: błędne klucze w backend/.env
```

**SearXNG nie zwraca wyników:**
```bash
docker compose logs searxng
# Sprawdź czy SEARXNG_SECRET_KEY jest ustawiony w backend/.env
# Sprawdź czy folder searxng/ ma uprawnienia: chmod 777 searxng/
# Test z VPS: curl "http://localhost:8080/search?q=test&format=json"
```

**Frontend nie łączy się z API (CORS):**
- Sprawdź czy URL Vercel jest w `CORS_ORIGINS` w `backend/.env`
- Po zmianie: `docker compose restart api`

**Użytkownik widzi "Brak dostępu" w panelu Admin:**
- Sprawdź w SQL: `SELECT * FROM user_profiles WHERE email = 'twoj@email.com';`
- Kolumna `role` powinna być `admin`

**Limit 3 dokumentów RAG:**
- To celowy limit per użytkownik — usuń stary dokument żeby dodać nowy
