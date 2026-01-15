-- Migration: Add date_of_birth field to user_profiles table
-- Date: 2026-01-15
-- Description: Adds date_of_birth field to store user's birth date for resume

-- Add date_of_birth column to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS date_of_birth DATE;

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.date_of_birth IS 'User date of birth for resume personal info';
