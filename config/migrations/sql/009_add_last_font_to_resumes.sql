-- Migration: Add last_font column to resumes table
-- This column stores the last selected font for a resume
-- Note: If column already exists, the ALTER TABLE will fail - that's expected and safe

-- Add the column with default value
ALTER TABLE resumes ADD COLUMN last_font VARCHAR(20) DEFAULT 'modern';

-- Update any existing NULL values (though DEFAULT should handle new rows)
UPDATE resumes SET last_font = 'modern' WHERE last_font IS NULL;

-- Add comment to document the column
COMMENT ON COLUMN resumes.last_font IS 'Last selected font for the resume (default: modern)';

