-- Row Level Security Policies for Additional Tables

-- Enable RLS on all additional tables
ALTER TABLE cover_letters ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_analyses ENABLE ROW LEVEL SECURITY;

-- Cover Letters Policies
CREATE POLICY "Users can view their own cover letters"
  ON cover_letters FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own cover letters"
  ON cover_letters FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own cover letters"
  ON cover_letters FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own cover letters"
  ON cover_letters FOR DELETE
  USING (auth.uid() = user_id);

-- Interview Sessions Policies
CREATE POLICY "Users can view their own interview sessions"
  ON interview_sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own interview sessions"
  ON interview_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own interview sessions"
  ON interview_sessions FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own interview sessions"
  ON interview_sessions FOR DELETE
  USING (auth.uid() = user_id);

-- Interview Questions Policies
CREATE POLICY "Users can view questions for their sessions"
  ON interview_questions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE interview_sessions.id = interview_questions.session_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create questions for their sessions"
  ON interview_questions FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE interview_sessions.id = interview_questions.session_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update questions for their sessions"
  ON interview_questions FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE interview_sessions.id = interview_questions.session_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete questions for their sessions"
  ON interview_questions FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM interview_sessions
      WHERE interview_sessions.id = interview_questions.session_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

-- Interview Answers Policies
CREATE POLICY "Users can view answers for their questions"
  ON interview_answers FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM interview_questions
      JOIN interview_sessions ON interview_sessions.id = interview_questions.session_id
      WHERE interview_questions.id = interview_answers.question_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create answers for their questions"
  ON interview_answers FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM interview_questions
      JOIN interview_sessions ON interview_sessions.id = interview_questions.session_id
      WHERE interview_questions.id = interview_answers.question_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update answers for their questions"
  ON interview_answers FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM interview_questions
      JOIN interview_sessions ON interview_sessions.id = interview_questions.session_id
      WHERE interview_questions.id = interview_answers.question_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete answers for their questions"
  ON interview_answers FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM interview_questions
      JOIN interview_sessions ON interview_sessions.id = interview_questions.session_id
      WHERE interview_questions.id = interview_answers.question_id
      AND interview_sessions.user_id = auth.uid()
    )
  );

-- Templates Policies (public read, admin write)
CREATE POLICY "Anyone can view active templates"
  ON templates FOR SELECT
  USING (is_active = true);

-- Resume Analyses Policies
CREATE POLICY "Users can view analyses for their resumes"
  ON resume_analyses FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes
      WHERE resumes.id = resume_analyses.resume_id
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create analyses for their resumes"
  ON resume_analyses FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM resumes
      WHERE resumes.id = resume_analyses.resume_id
      AND resumes.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view all their resume analyses"
  ON resume_analyses FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM resumes
      WHERE resumes.id = resume_analyses.resume_id
      AND resumes.user_id = auth.uid()
    )
  );








