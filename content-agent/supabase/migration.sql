-- Migracja: dodanie multi-user support do istniejącej bazy
-- Uruchom w Supabase SQL Editor jeśli tabele tasks i rag_documents już istnieją

-- 1. Nowa tabela user_profiles
create table if not exists user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  role text not null default 'user'
    check (role in ('user', 'admin')),
  created_at timestamptz default now()
);

-- 2. Dodaj user_id do tasks (jeśli nie istnieje)
alter table tasks
  add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- 3. Dodaj user_id do rag_documents (jeśli nie istnieje)
alter table rag_documents
  add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- 4. Trigger auto-tworzenia profilu przy rejestracji
create or replace function handle_new_user()
returns trigger as $$
begin
  insert into public.user_profiles (id, email, role)
  values (new.id, new.email, 'user')
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- 5. Funkcja updated_at (jeśli nie istnieje)
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- 6. Usuń stare RLS policies i ustaw właściwe

-- tasks
alter table tasks enable row level security;
drop policy if exists "allow all for now" on tasks;
drop policy if exists "tasks_own" on tasks;
create policy "tasks_own" on tasks
  for all using (auth.uid() = user_id);

-- rag_documents
alter table rag_documents enable row level security;
drop policy if exists "allow all for now" on rag_documents;
drop policy if exists "rag_documents_own" on rag_documents;
create policy "rag_documents_own" on rag_documents
  for all using (auth.uid() = user_id);

-- user_profiles
alter table user_profiles enable row level security;
drop policy if exists "user_profiles_own" on user_profiles;
create policy "user_profiles_own" on user_profiles
  for all using (auth.uid() = id);
