-- Migration: Add last_template column to resumes table (Simple Version)
-- This column stores the last selected template for a resume
-- 
-- INSTRUCTIONS: Run this SQL in Supabase SQL Editor
-- If you get an error "column already exists", that's fine - just ignore it.

-- Step 1: Add the column (ignore error if it already exists)
ALTER TABLE resumes ADD COLUMN last_template VARCHAR(50) DEFAULT 'modern-indigo';

-- Step 2: Update any existing NULL values
UPDATE resumes SET last_template = 'modern-indigo' WHERE last_template IS NULL;

-- Step 3: Add comment to document the column
COMMENT ON COLUMN resumes.last_template IS 'Last selected template for the resume (default: modern-indigo)';







