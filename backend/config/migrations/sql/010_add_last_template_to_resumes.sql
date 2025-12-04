-- Migration: Add last_template column to resumes table
-- This column stores the last selected template for a resume
-- 
-- INSTRUCTIONS FOR SUPABASE SQL EDITOR:
-- 1. Copy and paste the SQL below into Supabase SQL Editor
-- 2. If you get an error "column already exists", that's fine - just ignore it and continue
-- 3. The UPDATE and COMMENT statements are safe to run even if the column already exists

-- Add the column with default value
-- Note: This will fail if column already exists, but that's safe to ignore
ALTER TABLE resumes ADD COLUMN last_template VARCHAR(50) DEFAULT 'modern-indigo';

-- Update any existing NULL values (though DEFAULT should handle new rows)
UPDATE resumes SET last_template = 'modern-indigo' WHERE last_template IS NULL;

-- Add comment to document the column
COMMENT ON COLUMN resumes.last_template IS 'Last selected template for the resume (default: modern-indigo)';

