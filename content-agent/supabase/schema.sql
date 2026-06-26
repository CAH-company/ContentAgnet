-- Profil użytkownika z rolą (tworzony automatycznie przy rejestracji)
create table user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  role text not null default 'user'
    check (role in ('user', 'admin')),
  created_at timestamptz default now()
);

-- Zadania agenta
create table tasks (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  user_id uuid not null references auth.users(id) on delete cascade,
  topic text not null,
  platform text not null check (platform in ('blog','linkedin','twitter','facebook','instagram')),
  post_type text not null check (post_type in ('article','short_post','newsletter','carousel')),
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
  user_id uuid not null references auth.users(id) on delete cascade,
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

-- Trigger: auto-tworzenie user_profiles przy rejestracji nowego użytkownika
create or replace function handle_new_user()
returns trigger as $$
begin
  insert into public.user_profiles (id, email, role)
  values (new.id, new.email, 'user');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- RLS (Row Level Security)
alter table user_profiles enable row level security;
alter table tasks enable row level security;
alter table rag_documents enable row level security;

-- user_profiles: każdy widzi tylko swój profil (backend używa service_key = widzi wszystko)
create policy "user_profiles_own" on user_profiles
  for all using (auth.uid() = id);

-- tasks: user widzi tylko swoje zadania
create policy "tasks_own" on tasks
  for all using (auth.uid() = user_id);

-- rag_documents: user widzi tylko swoje dokumenty
create policy "rag_documents_own" on rag_documents
  for all using (auth.uid() = user_id);
