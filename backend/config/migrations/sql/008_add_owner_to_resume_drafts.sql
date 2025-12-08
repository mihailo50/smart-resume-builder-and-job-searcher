-- Migration: Add owner field to resume_drafts
-- Date: 2025-11-24
-- Description: Adds owner UUID field to track which user owns the draft (set on conversion)

-- Add owner column (nullable, for guest drafts)
ALTER TABLE resume_drafts
ADD COLUMN IF NOT EXISTS owner UUID;

-- Create index on owner for faster lookups
CREATE INDEX IF NOT EXISTS idx_resume_drafts_owner ON resume_drafts(owner);

-- Add comment
COMMENT ON COLUMN resume_drafts.owner IS 'Supabase user_id - set when draft is converted to a real resume';












