-- Add RLS policies for languages table (no IF NOT EXISTS to support older Postgres)
do $$
begin
  begin
    create policy "Users can view own languages"
      on public.languages for select
      using (exists (select 1 from public.resumes r where r.id = languages.resume_id and r.user_id = auth.uid()));
  exception when duplicate_object then null;
  end;

  begin
    create policy "Users can insert own languages"
      on public.languages for insert
      with check (exists (select 1 from public.resumes r where r.id = resume_id and r.user_id = auth.uid()));
  exception when duplicate_object then null;
  end;

  begin
    create policy "Users can update own languages"
      on public.languages for update
      using (exists (select 1 from public.resumes r where r.id = languages.resume_id and r.user_id = auth.uid()));
  exception when duplicate_object then null;
  end;

  begin
    create policy "Users can delete own languages"
      on public.languages for delete
      using (exists (select 1 from public.resumes r where r.id = languages.resume_id and r.user_id = auth.uid()));
  exception when duplicate_object then null;
  end;
end$$;
