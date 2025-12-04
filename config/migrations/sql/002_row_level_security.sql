-- Row Level Security (RLS) Policies for Supabase Tables
-- This file enables RLS and creates policies for all tables

-- Enable Row Level Security on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE educations ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiences ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_searches ENABLE ROW LEVEL SECURITY;

-- Job postings can be viewed by everyone (public read)
ALTER TABLE job_postings ENABLE ROW LEVEL SECURITY;

-- User Profiles Policies
-- Users can view and manage their own profile
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
  ON user_profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile"
  ON user_profiles FOR DELETE
  USING (auth.uid() = user_id);

-- Resumes Policies
-- Users can view and manage their own resumes
CREATE POLICY "Users can view own resumes"
  ON resumes FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own resumes"
  ON resumes FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own resumes"
  ON resumes FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own resumes"
  ON resumes FOR DELETE
  USING (auth.uid() = user_id);

-- Education Policies
-- Users can manage education entries for their resumes
CREATE POLICY "Users can view education for own resumes"
  ON educations FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = educations.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert education for own resumes"
  ON educations FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = educations.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update education for own resumes"
  ON educations FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = educations.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete education for own resumes"
  ON educations FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = educations.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

-- Experience Policies
-- Same pattern as education
CREATE POLICY "Users can view experience for own resumes"
  ON experiences FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = experiences.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert experience for own resumes"
  ON experiences FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = experiences.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update experience for own resumes"
  ON experiences FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = experiences.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete experience for own resumes"
  ON experiences FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = experiences.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

-- Skills Policies
CREATE POLICY "Users can view skills for own resumes"
  ON skills FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = skills.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert skills for own resumes"
  ON skills FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = skills.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update skills for own resumes"
  ON skills FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = skills.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete skills for own resumes"
  ON skills FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = skills.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

-- Projects Policies
CREATE POLICY "Users can view projects for own resumes"
  ON projects FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = projects.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert projects for own resumes"
  ON projects FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = projects.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update projects for own resumes"
  ON projects FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = projects.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete projects for own resumes"
  ON projects FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = projects.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

-- Certifications Policies
CREATE POLICY "Users can view certifications for own resumes"
  ON certifications FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = certifications.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert certifications for own resumes"
  ON certifications FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = certifications.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update certifications for own resumes"
  ON certifications FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = certifications.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete certifications for own resumes"
  ON certifications FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM resumes 
      WHERE resumes.id = certifications.resume_id 
      AND resumes.user_id = auth.uid()
    )
  );

-- Job Postings Policies
-- Everyone can view active job postings
CREATE POLICY "Anyone can view active job postings"
  ON job_postings FOR SELECT
  USING (is_active = TRUE);

-- Service role can manage job postings (for scraping/admin)
-- Note: This requires service role key, typically done from backend

-- Applications Policies
-- Users can view and manage their own applications
CREATE POLICY "Users can view own applications"
  ON applications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own applications"
  ON applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own applications"
  ON applications FOR UPDATE
  USING (auth.uid() = user_id);

-- Employers can view applications for their job postings (if implemented)
-- This would require a user-company relationship table

-- Saved Jobs Policies
CREATE POLICY "Users can view own saved jobs"
  ON saved_jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own saved jobs"
  ON saved_jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own saved jobs"
  ON saved_jobs FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved jobs"
  ON saved_jobs FOR DELETE
  USING (auth.uid() = user_id);

-- Job Searches Policies
CREATE POLICY "Users can view own job searches"
  ON job_searches FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own job searches"
  ON job_searches FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own job searches"
  ON job_searches FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own job searches"
  ON job_searches FOR DELETE
  USING (auth.uid() = user_id);









