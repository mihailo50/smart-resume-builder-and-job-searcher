-- Create languages table for resume sections
create table if not exists public.languages (
  id uuid primary key default uuid_generate_v4(),
  resume_id uuid references public.resumes(id) on delete cascade,
  name text not null,
  proficiency text,
  "order" integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_languages_resume_id on public.languages(resume_id);
create index if not exists idx_languages_order on public.languages("order");

-- Enable Row Level Security
alter table public.languages enable row level security;

-- RLS policies to match other resume section tables
create policy if not exists "Users can view own languages"
  on public.languages for select
  using (exists (select 1 from public.resumes r where r.id = languages.resume_id and r.user_id = auth.uid()));

create policy if not exists "Users can insert own languages"
  on public.languages for insert
  with check (exists (select 1 from public.resumes r where r.id = resume_id and r.user_id = auth.uid()));

create policy if not exists "Users can update own languages"
  on public.languages for update
  using (exists (select 1 from public.resumes r where r.id = languages.resume_id and r.user_id = auth.uid()));

create policy if not exists "Users can delete own languages"
  on public.languages for delete
  using (exists (select 1 from public.resumes r where r.id = languages.resume_id and r.user_id = auth.uid()));
