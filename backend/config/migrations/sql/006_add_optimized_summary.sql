-- Add optimized_summary field to existing resumes table
-- This field stores full-length AI-optimized resume text (no character limit)
-- while summary field remains for short display version (500 char limit)

ALTER TABLE resumes
ADD COLUMN IF NOT EXISTS optimized_summary TEXT;

-- Add comment to clarify field purpose
COMMENT ON COLUMN resumes.optimized_summary IS 'Full-length AI-optimized resume summary text (no character limit). Use summary field for short display version (500 char limit).';




