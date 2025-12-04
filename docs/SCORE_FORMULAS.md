# AI Resume Analysis Score Formulas

This document details the transparent, formula-based scoring system for resume analysis.

## Score Formulas

### 1. ATS Score
**Formula:** `(matched_keywords / total_job_keywords) * 100`

- **matched_keywords**: Number of job keywords found in resume (using fuzzy matching)
- **total_job_keywords**: Total unique keywords extracted from job description
- **Fuzzy Matching**: Uses rapidfuzz (or difflib) with 85% similarity threshold
- **Range**: 0-100
- **Base Score**: 75 (when no job description provided)

**Example:**
- Job keywords: ["docker", "aws", "heroku", "python", "react"]
- Resume keywords: ["docker", "python", "react"]
- Matched: 3 (docker, python, react)
- ATS Score = (3 / 5) * 100 = 60

### 2. Readability Score
**Formula:** `Flesch-Kincaid Reading Ease (via textstat/NLTK)`

- Uses `textstat.flesch_reading_ease()` for calculation
- Normalized to 0-100 scale:
  - Score ≥ 60: `60 + (flesch_score - 60) * 2` (capped at 100)
  - Score 40-60: `40 + (flesch_score - 40)`
  - Score < 40: `flesch_score * 0.5`
- **Range**: 0-100
- **Fallback**: Sentence length heuristic if textstat unavailable

**Example:**
- Flesch score: 70
- Readability Score = 60 + (70 - 60) * 2 = 80

### 3. Quantifiable Achievements Score
**Formula:** `(bullets_with_numbers / total_bullets) * 100`

- **bullets_with_numbers**: Count of bullets containing numbers/metrics (regex: `\b\d+[%$KMB]?\b`)
- **total_bullets**: Total bullet points in resume (from text + structured data)
- **Range**: 0-100
- **Minimum**: 30 (if no bullets found)

**Example:**
- Total bullets: 10
- Bullets with numbers: 7
- Quantifiable Score = (7 / 10) * 100 = 70

### 4. Bullet Strength Score
**Formula:** `(bullets_with_action_verbs / total_bullets) * 100`

- **bullets_with_action_verbs**: Count of bullets starting with action verbs
- **total_bullets**: Total bullet points in resume
- **Action Verbs**: developed, implemented, created, managed, led, achieved, increased, improved, designed, built, optimized, reduced, delivered, executed, launched, established, generated, architected, scaled, automated, streamlined
- **Range**: 0-100
- **Minimum**: 40 (if no bullets found)

**Example:**
- Total bullets: 10
- Bullets with action verbs: 8
- Bullet Strength = (8 / 10) * 100 = 80

### 5. Keyword Score
**Formula:** `(matched_keywords / total_job_keywords) * 100`

- Same as ATS Score, but only calculated when job description provided
- **Range**: 0-100
- **Optional**: Only included in response if job_desc provided

### 6. Formatting Score
**Formula:** `50 + (sections_found * 8) + structure_bonus`

- **Base**: 50
- **sections_found**: Count of sections found (experience, education, skills, summary, projects, certifications) * 8
- **structure_bonus**: +10 for experiences, +10 for skills, +10 for educations
- **Range**: 0-100 (capped)

**Example:**
- Sections found: 5 (experience, education, skills, summary, projects)
- Structure bonus: +30 (all three present)
- Formatting Score = 50 + (5 * 8) + 30 = 120 → capped at 100

## Keyword Extraction

### Job Description Keywords
- **Method**: LangChain chain with OpenAI (fallback: regex)
- **Normalization**: All lowercase, NLTK-style stemming
- **Filtering**: Removes stop words, minimum 3 characters

### Resume Keywords
**Searches ALL fields:**
- `summary` (text)
- `optimized_summary` (text) ⚠️ **CRITICAL - was missing before**
- `experiences[].description` (text)
- `experiences[].position` (text)
- `experiences[].company` (text)
- `projects[].title` (text)
- `projects[].description` (text)
- `projects[].technologies` (comma-separated)
- `skills[].name` (direct)
- `certifications[].name` (direct) ⚠️ **CRITICAL - was missing before**
- `certifications[].issuer` (text)
- `educations[].degree` (text)
- `educations[].field_of_study` (text)
- `educations[].institution` (text)
- Plain resume text

### Fuzzy Matching
- **Library**: rapidfuzz (preferred) or difflib (fallback)
- **Threshold**: 85% similarity
- **Purpose**: Avoid false positives (e.g., "Docker" vs "docker", "AWS" vs "aws")

## Missing Keywords Detection

**Formula:** `job_keywords - (resume_keywords with fuzzy matching)`

- Uses fuzzy matching to avoid flagging keywords that are present with slight variations
- Prioritized by length and importance
- Limited to top 15 missing keywords

## Suggestions Generation

Generates 3-5 suggestions based on:
- Missing keywords (with placement ideas)
- Low quantifiable score (< 60)
- Low bullet strength (< 70)
- Missing sections (projects, certifications)
- Low ATS score (< 60)

Each suggestion includes:
- **type**: keyword, achievement, formatting, content, general
- **text**: Specific, actionable suggestion with placement ideas
- **priority**: high, medium, low


