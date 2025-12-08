# Testing AI Analysis Endpoints

## Test Cases for Keyword Detection

### Test 1: Keywords in optimized_summary
**Request:**
```json
POST /api/v1/ai/analyze-resume/
{
  "resume_id": "your-resume-id",
  "job_desc": "Looking for developer with docker, aws, heroku experience."
}
```

**Expected:**
- `missing_keywords` should NOT include "docker", "aws", or "heroku" if they appear in:
  - `optimized_summary` field
  - `projects[].technologies` field
  - `certifications[].name` field
  - `skills[].name` field

### Test 2: Keywords in projects.technologies
**Setup:**
- Create a project with `technologies: "React, Docker, Heroku"`
- Job description: "Looking for React, Docker, Heroku developer"

**Expected:**
- All three keywords should be found (not in missing_keywords)
- ATS score should be high (80-100)

### Test 3: Keywords in certifications.name
**Setup:**
- Create certification with `name: "AWS Certified Developer"`
- Job description: "Looking for AWS certified developer"

**Expected:**
- "aws" should be found (fuzzy matching: "AWS" → "aws")
- Should NOT be in missing_keywords

### Test 4: Fuzzy Matching
**Setup:**
- Resume has: "Docker" (capitalized)
- Job description: "docker" (lowercase)

**Expected:**
- Should match via fuzzy matching (85% threshold)
- Should NOT be in missing_keywords

### Test 5: Score Formulas
**Test ATS Score:**
- Job keywords: ["python", "aws", "docker", "react", "kubernetes"]
- Resume keywords: ["python", "aws", "docker"]
- Expected ATS Score: (3/5) * 100 = 60

**Test Quantifiable Score:**
- Resume with 10 bullets, 7 containing numbers
- Expected Quantifiable Score: (7/10) * 100 = 70

**Test Bullet Strength:**
- Resume with 10 bullets, 8 starting with action verbs
- Expected Bullet Strength: (8/10) * 100 = 80

### Test 6: Apply Suggestions Returns Full Resume
**Request:**
```json
POST /api/v1/ai/apply-suggestions/
{
  "resume_id": "your-resume-id",
  "suggestions": [
    {"type": "keyword", "text": "Add AWS", "priority": "high"}
  ],
  "missing_keywords": ["aws"]
}
```

**Expected Response:**
```json
{
  "resume_data": {
    "id": "...",
    "full_name": "...",
    "skills": [...],  // Should include newly added AWS skill
    "experiences": [...],
    "projects": [...],
    "certifications": [...]
  },
  "optimized_text": "...",
  "changes_applied": ["Added 'AWS' to Skills section"],
  "pro_tip": "Pro ($9/mo) unlocks tailored job matches with Pinecone."
}
```

## Manual Testing Steps

1. **Start Django server:**
   ```bash
   cd backend
   poetry run python manage.py runserver
   ```

2. **Create a test resume with:**
   - `optimized_summary`: "Expert in Docker and Heroku deployment"
   - `projects[0].technologies`: "React, Node.js, Heroku"
   - `certifications[0].name`: "AWS Certified Developer"
   - `skills`: ["Python", "Docker"]

3. **Test analyze-resume:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ai/analyze-resume/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "resume_id": "YOUR_RESUME_ID",
       "job_desc": "Looking for developer with docker, aws, heroku, react experience."
     }'
   ```

4. **Verify:**
   - `missing_keywords` should NOT include "docker", "aws", "heroku", or "react"
   - ATS score should be high (all keywords found)
   - Scores should match formulas (not arbitrary)

5. **Test apply-suggestions:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ai/apply-suggestions/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "resume_id": "YOUR_RESUME_ID",
       "suggestions": [{"type": "keyword", "text": "Add Kubernetes", "priority": "high"}],
       "missing_keywords": ["kubernetes"]
     }'
   ```

6. **Verify:**
   - Response includes full `resume_data` with updated skills
   - `changes_applied` shows what was updated
   - Database (Supabase) is updated with new skill

## Automated Tests

Run the test suite:
```bash
cd backend
poetry run pytest api/tests/test_ai.py -v
```

Expected: All tests pass, including:
- `test_missing_keywords_includes_aws` - Verifies accurate keyword detection
- `test_ats_score_formula` - Verifies formula-based scoring
- `test_structured_json_parsing` - Verifies all fields are searched
- `test_fuzzy_matching` - Verifies case-insensitive matching

## Common Issues

1. **Keywords still missing despite being in resume:**
   - Check that `optimized_summary` is being searched (was missing before)
   - Check that `certifications[].name` is being searched (was missing before)
   - Verify fuzzy matching is working (case variations)

2. **Scores seem arbitrary:**
   - Check that formulas are being used (see `docs/SCORE_FORMULAS.md`)
   - Verify calculations match expected formulas

3. **Apply-suggestions doesn't update database:**
   - Check that `resume_id` is provided for authenticated users
   - Verify Supabase connection is working
   - Check that `resume_data` in response is refreshed from database



