-- Migration: Add email field to user_profiles table
-- Date: 2026-01-14
-- Description: Adds email field to store user's preferred contact email (separate from auth email)

-- Add email column to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.email IS 'User preferred contact email (may differ from auth email)';

-- Create index for email lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
