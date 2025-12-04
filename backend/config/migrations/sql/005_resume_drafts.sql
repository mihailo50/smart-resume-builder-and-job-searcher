-- Resume Drafts Table for Guest Users
-- Allows anonymous users to create and save resume drafts before signup
-- All resume data is stored in the JSONField 'data'
-- When user signs up, draft is converted to a real Resume and deleted

-- Resume Drafts Table
CREATE TABLE IF NOT EXISTS resume_drafts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  guest_id UUID UNIQUE NOT NULL, -- Anonymous guest identifier (set via secure cookie)
  data JSONB DEFAULT '{}'::jsonb, -- All resume data stored as JSON
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add last_updated column if table exists but column doesn't (for existing tables)
-- PostgreSQL 9.6+ supports IF NOT EXISTS for ADD COLUMN
ALTER TABLE resume_drafts ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update existing rows to set last_updated if it's NULL (for rows created before column was added)
UPDATE resume_drafts SET last_updated = COALESCE(last_updated, created_at, NOW()) WHERE last_updated IS NULL;

-- Create indexes for resume_drafts
CREATE INDEX IF NOT EXISTS idx_resume_drafts_guest_id ON resume_drafts(guest_id);

-- Create index on last_updated (will work after column is ensured above)
CREATE INDEX IF NOT EXISTS idx_resume_drafts_last_updated ON resume_drafts(last_updated DESC);
