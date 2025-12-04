-- Migration: Add location field to user_profiles table
-- Date: 2025-11-24
-- Description: Adds location field to store user location information

-- Add location column to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS location VARCHAR(200);

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.location IS 'User location (city, state, country, etc.)';



