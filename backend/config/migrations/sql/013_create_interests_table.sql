-- Create interests table
CREATE TABLE IF NOT EXISTS public.interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.interests ENABLE ROW LEVEL SECURITY;

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_interests_resume_id ON public.interests(resume_id);

-- Policies already exist, just ensure table is created
SELECT 1;



