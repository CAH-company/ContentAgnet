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
alter table tasks enable row level security;
alter table rag_documents enable row level security;

create policy "allow all for now" on tasks for all using (true);
create policy "allow all for now" on rag_documents for all using (true);
