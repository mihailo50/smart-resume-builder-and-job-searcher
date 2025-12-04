-- Row Level Security Policies for Resume Draft Tables
-- Drafts are accessible to guests (via guest_id cookie) and authenticated users
-- Backend service role handles all operations, so policies are permissive

-- Enable RLS on draft tables
ALTER TABLE resume_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE education_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE experience_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_drafts ENABLE ROW LEVEL SECURITY;

-- Resume Drafts Policies
-- Allow public access (guests can create/view/update their own drafts via backend)
-- Backend validates guest_id from cookie before allowing operations
CREATE POLICY "Anyone can view resume drafts"
  ON resume_drafts FOR SELECT
  USING (true);

CREATE POLICY "Anyone can insert resume drafts"
  ON resume_drafts FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Anyone can update resume drafts"
  ON resume_drafts FOR UPDATE
  USING (true);

CREATE POLICY "Anyone can delete resume drafts"
  ON resume_drafts FOR DELETE
  USING (true);

-- Education Drafts Policies
CREATE POLICY "Anyone can view education drafts"
  ON education_drafts FOR SELECT
  USING (true);

CREATE POLICY "Anyone can insert education drafts"
  ON education_drafts FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Anyone can update education drafts"
  ON education_drafts FOR UPDATE
  USING (true);

CREATE POLICY "Anyone can delete education drafts"
  ON education_drafts FOR DELETE
  USING (true);

-- Experience Drafts Policies
CREATE POLICY "Anyone can view experience drafts"
  ON experience_drafts FOR SELECT
  USING (true);

CREATE POLICY "Anyone can insert experience drafts"
  ON experience_drafts FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Anyone can update experience drafts"
  ON experience_drafts FOR UPDATE
  USING (true);

CREATE POLICY "Anyone can delete experience drafts"
  ON experience_drafts FOR DELETE
  USING (true);

-- Skill Drafts Policies
CREATE POLICY "Anyone can view skill drafts"
  ON skill_drafts FOR SELECT
  USING (true);

CREATE POLICY "Anyone can insert skill drafts"
  ON skill_drafts FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Anyone can update skill drafts"
  ON skill_drafts FOR UPDATE
  USING (true);

CREATE POLICY "Anyone can delete skill drafts"
  ON skill_drafts FOR DELETE
  USING (true);

-- Note: Actual security is enforced at the Django backend level by:
-- 1. Validating guest_id from secure cookie
-- 2. Only allowing operations on drafts that match the guest_id
-- 3. Using service role key for Supabase operations (bypasses RLS anyway)




