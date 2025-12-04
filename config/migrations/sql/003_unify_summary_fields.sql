-- Migration: Unify summary fields - migrate summary to optimized_summary
-- Date: 2025-11-24
-- Description: Migrates data from summary to optimized_summary, keeps summary as alias

-- Step 1: Migrate existing summary data to optimized_summary where optimized_summary is NULL
UPDATE resumes 
SET optimized_summary = summary 
WHERE optimized_summary IS NULL OR optimized_summary = '' 
  AND summary IS NOT NULL 
  AND summary != '';

-- Step 2: Change summary column to TEXT (remove 300 char limit)
-- Note: This is a no-op if already TEXT, but ensures consistency
ALTER TABLE resumes 
ALTER COLUMN summary TYPE TEXT;

-- Add comment for documentation
COMMENT ON COLUMN resumes.summary IS 'DEPRECATED: Use optimized_summary instead. Kept for backwards compatibility.';
COMMENT ON COLUMN resumes.optimized_summary IS 'Primary summary field - full-length professional summary (unlimited length)';



