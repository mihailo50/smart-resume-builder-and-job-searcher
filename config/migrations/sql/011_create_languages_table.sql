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
