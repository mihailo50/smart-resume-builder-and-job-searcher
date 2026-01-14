"""
Enhanced ATS Analyzer Service with LangChain and transparent scoring.

Uses LangChain for accurate keyword extraction, fuzzy matching, and provides transparent,
formula-based scoring for ATS compatibility. Searches ALL resume fields including
optimized_summary, certifications, projects, etc.
"""
import re
import json
import logging
from typing import Dict, Any, Optional, List, Set
from collections import Counter
from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy-loaded LangChain components (loaded only when AI analysis is needed)
_langchain_chat_openai = None
_langchain_prompt_template = None
_langchain_checked = False
_langchain_available = None

def _ensure_langchain():
    """Lazy-load LangChain only when AI features are actually needed."""
    global _langchain_chat_openai, _langchain_prompt_template, _langchain_checked, _langchain_available
    
    if _langchain_checked:
        return _langchain_available
    
    _langchain_checked = True
    try:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        _langchain_chat_openai = ChatOpenAI
        _langchain_prompt_template = ChatPromptTemplate
        _langchain_available = True
        logger.info("LangChain loaded successfully for AI analysis")
        return True
    except (ImportError, OSError) as e:
        _langchain_available = False
        logger.warning(f"LangChain not available: {e}")
        return False

# Try to import fuzzy matching libraries
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    try:
        from difflib import SequenceMatcher
        RAPIDFUZZ_AVAILABLE = False
    except ImportError:
        RAPIDFUZZ_AVAILABLE = False
        SequenceMatcher = None


class EnhancedATSAnalyzerService:
    """Enhanced service for analyzing resumes with LangChain and transparent scoring."""
    
    def __init__(self):
        self.logger = logger
        self._llm = None
        self._llm_initialized = False
    
    @property
    def llm(self):
        """Lazy-load the LLM only when needed."""
        if self._llm_initialized:
            return self._llm
        
        self._llm_initialized = True
        try:
            if settings.OPENAI_API_KEY and _ensure_langchain():
                self._llm = _langchain_chat_openai(
                    model="gpt-3.5-turbo",
                    temperature=0,
                    api_key=settings.OPENAI_API_KEY
                )
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
        
        return self._llm
    
    def analyze(
        self,
        resume_data: Optional[Dict[str, Any]] = None,
        resume_text: Optional[str] = None,
        job_desc: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a resume for ATS compatibility with transparent scoring.
        Uses FULL structured JSON including optimized_summary, certifications, etc.
        """
        # Always extract fresh text from structured data if available
        if resume_data:
            resume_text = self._extract_text_from_data(resume_data)
        
        if not resume_text:
            raise ValueError("Either resume_data or resume_text must be provided")
        
        # Extract keywords from job description using LangChain
        job_keywords: Set[str] = set()
        if job_desc:
            job_keywords = self._extract_job_keywords_langchain(job_desc)
        
        # Extract resume keywords from ALL fields (text + full structured data)
        resume_keywords = self._extract_resume_keywords_comprehensive(resume_text, resume_data)
        
        # Calculate ATS score with fuzzy matching: (matched_keywords / total_job_keywords) * 100
        ats_score, matched_keywords = self._calculate_ats_score_fuzzy(job_keywords, resume_keywords)
        
        # Find missing keywords (using fuzzy matching to avoid false positives)
        missing_keywords = self._find_missing_keywords_fuzzy(job_keywords, resume_keywords)
        # Prioritize by length and importance
        missing_keywords = sorted(
            missing_keywords,
            key=lambda x: (len(x), x.lower() not in ['the', 'and', 'for', 'with']),
            reverse=True
        )[:15]
        
        # Calculate readability score using NLTK/textstat Flesch-Kincaid
        readability_score = self._calculate_readability_score(resume_text)
        
        # Calculate quantifiable achievements score (% of bullets with numbers/metrics)
        quantifiable_score = self._calculate_quantifiable_score(resume_text, resume_data)
        
        # Calculate bullet strength (% of bullets starting with action verbs)
        bullet_strength = self._calculate_bullet_strength(resume_text, resume_data)
        
        # Calculate keyword score (if job_desc provided)
        keyword_score = None
        if job_desc:
            matched_count = len(matched_keywords)
            total_job = len(job_keywords) if job_keywords else 1
            keyword_score = int((matched_count / total_job) * 100)
        
        # Generate intelligent suggestions
        suggestions = self._generate_suggestions(
            resume_text=resume_text,
            resume_data=resume_data,
            missing_keywords=missing_keywords,
            ats_score=ats_score,
            quantifiable_score=quantifiable_score,
            bullet_strength=bullet_strength
        )
        
        return {
            'ats_score': max(0, min(100, ats_score)),
            'missing_keywords': missing_keywords,
            'suggestions': suggestions,
            'readability_score': readability_score,
            'bullet_strength': bullet_strength,
            'quantifiable_achievements': quantifiable_score,
            'keyword_score': keyword_score,
            'formatting_score': self._calculate_formatting_score(resume_text, resume_data),
            'detailed_analysis': {
                'total_words': len(resume_text.split()),
                'total_job_keywords': len(job_keywords),
                'matched_keywords_count': len(matched_keywords),
                'has_contact_info': bool(resume_data and resume_data.get('email')),
                'has_experience': bool(resume_data and resume_data.get('experiences')),
                'has_projects': bool(resume_data and resume_data.get('projects')),
                'has_certifications': bool(resume_data and resume_data.get('certifications')),
            }
        }
    
    def _extract_job_keywords_langchain(self, job_desc: str) -> Set[str]:
        """Extract unique keywords from job description using LangChain."""
        if not self.llm or not _langchain_available:
            return self._extract_keywords_regex(job_desc)
        
        try:
            prompt = _langchain_prompt_template.from_messages([
                ("system", "You are an expert at extracting technical keywords and skills from job descriptions. "
                          "Extract only unique, relevant keywords (technologies, tools, skills, frameworks). "
                          "Use NLTK-style stemming to normalize (e.g., 'docker' not 'Docker', 'aws' not 'AWS'). "
                          "Return a JSON array of strings, no duplicates, all lowercase."),
                ("human", "Extract unique keywords from this job description:\n\n{job_desc}\n\n"
                         "Return only a JSON array of keyword strings, lowercase, no duplicates, normalized.")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"job_desc": job_desc})
            
            content = response.content.strip()
            if '```' in content:
                content = re.sub(r'```json\n?', '', content)
                content = re.sub(r'```\n?', '', content)
                content = content.strip()
            
            try:
                keywords = json.loads(content)
                if isinstance(keywords, list):
                    keywords = [
                        k.lower().strip()
                        for k in keywords
                        if isinstance(k, str) and len(k) >= 3
                    ]
                    return set(keywords)
            except json.JSONDecodeError:
                keywords = re.findall(r'"([^"]+)"', content)
                return set(k.lower().strip() for k in keywords if len(k) >= 3)
        
        except Exception as e:
            logger.warning(f"LangChain keyword extraction failed: {e}, using regex fallback")
        
        return self._extract_keywords_regex(job_desc)
    
    def _extract_keywords_regex(self, text: str) -> Set[str]:
        """Fallback regex-based keyword extraction."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her',
            'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
            'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with', 'this',
            'that', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much',
            'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long',
            'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were',
            'what', 'work', 'year', 'years', 'will', 'would', 'could', 'should',
            'ability', 'abilities', 'experience', 'skills', 'skill'
        }
        keywords = {w for w in words if w not in stop_words and len(w) >= 3}
        return keywords
    
    def _extract_resume_keywords_comprehensive(
        self,
        resume_text: str,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> Set[str]:
        """
        Extract keywords from ALL resume fields:
        - summary, optimized_summary
        - experiences (position, description)
        - projects (title, description, technologies)
        - skills (name)
        - certifications (name)
        - educations (degree, field_of_study, institution)
        - plain text
        """
        keywords = set()
        
        # Extract from plain text
        text_keywords = self._extract_keywords_regex(resume_text)
        keywords.update(text_keywords)
        
        # Extract from structured data - ALL fields
        if resume_data:
            # Summary and optimized_summary (CRITICAL - was missing before)
            if resume_data.get('summary'):
                summary_keywords = self._extract_keywords_regex(resume_data['summary'])
                keywords.update(summary_keywords)
            if resume_data.get('optimized_summary'):
                opt_summary_keywords = self._extract_keywords_regex(resume_data['optimized_summary'])
                keywords.update(opt_summary_keywords)
            
            # Skills
            for skill in resume_data.get('skills', []):
                if skill.get('name'):
                    keywords.add(skill['name'].lower().strip())
            
            # Projects - ALL fields
            for project in resume_data.get('projects', []):
                if project.get('technologies'):
                    techs = [t.strip().lower() for t in project['technologies'].split(',')]
                    keywords.update(techs)
                if project.get('title'):
                    title_keywords = self._extract_keywords_regex(project['title'])
                    keywords.update(title_keywords)
                if project.get('description'):
                    desc_keywords = self._extract_keywords_regex(project['description'])
                    keywords.update(desc_keywords)
            
            # Experience descriptions and positions
            for exp in resume_data.get('experiences', []):
                if exp.get('description'):
                    desc_keywords = self._extract_keywords_regex(exp['description'])
                    keywords.update(desc_keywords)
                if exp.get('position'):
                    pos_keywords = self._extract_keywords_regex(exp['position'])
                    keywords.update(pos_keywords)
                if exp.get('company'):
                    company_keywords = self._extract_keywords_regex(exp['company'])
                    keywords.update(company_keywords)
            
            # Certifications (CRITICAL - was missing before)
            for cert in resume_data.get('certifications', []):
                if cert.get('name'):
                    keywords.add(cert['name'].lower().strip())
                if cert.get('issuer'):
                    issuer_keywords = self._extract_keywords_regex(cert['issuer'])
                    keywords.update(issuer_keywords)
            
            # Education
            for edu in resume_data.get('educations', []):
                if edu.get('degree'):
                    degree_keywords = self._extract_keywords_regex(edu['degree'])
                    keywords.update(degree_keywords)
                if edu.get('field_of_study'):
                    field_keywords = self._extract_keywords_regex(edu['field_of_study'])
                    keywords.update(field_keywords)
                if edu.get('institution'):
                    inst_keywords = self._extract_keywords_regex(edu['institution'])
                    keywords.update(inst_keywords)
        
        return keywords
    
    def _fuzzy_match(self, keyword1: str, keyword2: str, threshold: float = 0.85) -> bool:
        """Check if two keywords match using fuzzy matching."""
        if keyword1.lower() == keyword2.lower():
            return True
        
        if RAPIDFUZZ_AVAILABLE:
            ratio = fuzz.ratio(keyword1.lower(), keyword2.lower()) / 100.0
            return ratio >= threshold
        elif SequenceMatcher:
            ratio = SequenceMatcher(None, keyword1.lower(), keyword2.lower()).ratio()
            return ratio >= threshold
        else:
            # Fallback: simple case-insensitive comparison
            return keyword1.lower() == keyword2.lower()
    
    def _calculate_ats_score_fuzzy(
        self,
        job_keywords: Set[str],
        resume_keywords: Set[str]
    ) -> tuple[int, Set[str]]:
        """
        Calculate ATS score with fuzzy matching: (matched_keywords / total_job_keywords) * 100
        Returns (score, matched_keywords_set)
        """
        if not job_keywords:
            return 75, set()  # Base score when no job description
        
        matched = set()
        for job_kw in job_keywords:
            # Check exact match first
            if job_kw in resume_keywords:
                matched.add(job_kw)
            else:
                # Check fuzzy match
                for resume_kw in resume_keywords:
                    if self._fuzzy_match(job_kw, resume_kw):
                        matched.add(job_kw)
                        break
        
        if not job_keywords:
            return 0, matched
        
        score = (len(matched) / len(job_keywords)) * 100
        return int(max(0, min(100, score))), matched
    
    def _find_missing_keywords_fuzzy(
        self,
        job_keywords: Set[str],
        resume_keywords: Set[str]
    ) -> List[str]:
        """Find missing keywords using fuzzy matching to avoid false positives."""
        missing = []
        for job_kw in job_keywords:
            # Check exact match
            if job_kw in resume_keywords:
                continue
            
            # Check fuzzy match
            found = False
            for resume_kw in resume_keywords:
                if self._fuzzy_match(job_kw, resume_kw):
                    found = True
                    break
            
            if not found:
                missing.append(job_kw)
        
        return missing
    
    def _calculate_readability_score(self, text: str) -> int:
        """Calculate readability score using NLTK/textstat Flesch-Kincaid."""
        try:
            import textstat
            flesch_score = textstat.flesch_reading_ease(text)
            # Normalize to 0-100 scale
            if flesch_score >= 60:
                return min(100, int(60 + (flesch_score - 60) * 2))
            elif flesch_score >= 40:
                return int(40 + (flesch_score - 40))
            else:
                return max(0, int(flesch_score * 0.5))
        except ImportError:
            # Fallback: simple heuristic
            sentences = re.split(r'[.!?]+', text)
            if not sentences:
                return 50
            
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 15 <= avg_sentence_length <= 20:
                return 85
            elif 10 <= avg_sentence_length <= 25:
                return 75
            elif 5 <= avg_sentence_length <= 30:
                return 65
            else:
                return 50
    
    def _calculate_quantifiable_score(
        self,
        resume_text: str,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate quantifiable achievements score as PERCENTAGE of bullets with numbers/metrics.
        Formula: (bullets_with_numbers / total_bullets) * 100
        """
        # Find all bullets
        bullets = re.findall(r'[•\-\*]\s*(.+)', resume_text)
        
        # Also check structured data
        if resume_data:
            for exp in resume_data.get('experiences', []):
                if exp.get('description'):
                    exp_bullets = re.findall(r'[•\-\*]\s*(.+)', exp['description'])
                    bullets.extend(exp_bullets)
            for project in resume_data.get('projects', []):
                if project.get('description'):
                    proj_bullets = re.findall(r'[•\-\*]\s*(.+)', project['description'])
                    bullets.extend(proj_bullets)
        
        if not bullets:
            return 30  # Low score if no bullets
        
        # Count bullets with numbers/metrics
        bullets_with_numbers = sum(
            1 for bullet in bullets
            if re.search(r'\b\d+[%$KMB]?\b', bullet)
        )
        
        # Return percentage
        score = int((bullets_with_numbers / len(bullets)) * 100)
        return max(0, min(100, score))
    
    def _calculate_bullet_strength(
        self,
        resume_text: str,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate bullet point strength as PERCENTAGE of bullets starting with action verbs.
        Formula: (bullets_with_action_verbs / total_bullets) * 100
        """
        bullets = re.findall(r'[•\-\*]\s*(.+)', resume_text)
        
        # Also check structured data
        if resume_data:
            for exp in resume_data.get('experiences', []):
                if exp.get('description'):
                    exp_bullets = re.findall(r'[•\-\*]\s*(.+)', exp['description'])
                    bullets.extend(exp_bullets)
            for project in resume_data.get('projects', []):
                if project.get('description'):
                    proj_bullets = re.findall(r'[•\-\*]\s*(.+)', project['description'])
                    bullets.extend(proj_bullets)
        
        if not bullets:
            return 40  # Low score if no bullets
        
        # Count action verbs
        action_verbs = {
            'developed', 'implemented', 'created', 'managed', 'led', 'achieved',
            'increased', 'improved', 'designed', 'built', 'optimized', 'reduced',
            'delivered', 'executed', 'launched', 'established', 'generated',
            'designed', 'architected', 'scaled', 'automated', 'streamlined'
        }
        
        bullets_with_verbs = sum(
            1 for bullet in bullets
            if any(verb in bullet.lower().split()[0:3] for verb in action_verbs)
        )
        
        # Return percentage
        score = int((bullets_with_verbs / len(bullets)) * 100)
        return max(0, min(100, score))
    
    def _calculate_formatting_score(
        self,
        resume_text: str,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Calculate formatting score based on structure and organization."""
        score = 50  # Base score
        
        # Check for sections
        sections = ['experience', 'education', 'skills', 'summary', 'projects', 'certifications']
        found_sections = sum(1 for section in sections if section.lower() in resume_text.lower())
        score += found_sections * 8  # +8 per section, max 48
        
        # Check for proper structure
        if resume_data:
            if resume_data.get('experiences'):
                score += 10
            if resume_data.get('skills'):
                score += 10
            if resume_data.get('educations'):
                score += 10
        
        return min(100, score)
    
    def _generate_suggestions(
        self,
        resume_text: str,
        resume_data: Optional[Dict[str, Any]],
        missing_keywords: List[str],
        ats_score: int,
        quantifiable_score: int,
        bullet_strength: int
    ) -> List[Dict[str, str]]:
        """Generate intelligent, specific suggestions."""
        suggestions = []
        
        # Keyword suggestions with placement ideas
        if missing_keywords:
            top_missing = missing_keywords[:5]
            placement = "Add to Skills section"
            if resume_data and resume_data.get('experiences'):
                placement = "Add to relevant Experience descriptions or Skills section"
            
            suggestions.append({
                'type': 'keyword',
                'text': f"Add keywords: {', '.join(top_missing)}. {placement}.",
                'priority': 'high'
            })
        
        # Quantifiable achievements
        if quantifiable_score < 60:
            suggestions.append({
                'type': 'achievement',
                'text': 'Add quantifiable metrics to bullet points (e.g., "Increased revenue by 25%", "Managed team of 10")',
                'priority': 'high'
            })
        
        # Bullet strength
        if bullet_strength < 70:
            suggestions.append({
                'type': 'formatting',
                'text': 'Start bullet points with strong action verbs (Developed, Implemented, Led, Achieved)',
                'priority': 'medium'
            })
        
        # Section gaps
        if resume_data:
            if not resume_data.get('projects') and 'project' in resume_text.lower():
                suggestions.append({
                    'type': 'content',
                    'text': 'Consider adding a Projects section to showcase technical work',
                    'priority': 'medium'
                })
            
            if not resume_data.get('certifications') and missing_keywords:
                cert_keywords = {'aws', 'azure', 'gcp', 'certified', 'certification'}
                if any(kw in ' '.join(missing_keywords).lower() for kw in cert_keywords):
                    suggestions.append({
                        'type': 'content',
                        'text': 'Consider adding relevant certifications (e.g., AWS, Azure) if applicable',
                        'priority': 'low'
                    })
        
        # ATS score suggestions
        if ats_score < 60:
            suggestions.append({
                'type': 'general',
                'text': 'Low ATS compatibility. Review job description keywords and ensure they appear naturally in your resume',
                'priority': 'high'
            })
        
        # Ensure we have at least 3 suggestions
        if len(suggestions) < 3:
            suggestions.append({
                'type': 'formatting',
                'text': 'Ensure consistent formatting and clear section headers',
                'priority': 'low'
            })
        
        return suggestions[:5]  # Limit to top 5
    
    def _extract_text_from_data(self, resume_data: Dict[str, Any]) -> str:
        """Extract plain text from structured resume data - ALL fields."""
        text_parts = []
        
        # Personal info
        if resume_data.get('full_name'):
            text_parts.append(resume_data['full_name'])
        if resume_data.get('title'):
            text_parts.append(resume_data['title'])
        if resume_data.get('summary'):
            text_parts.append(resume_data['summary'])
        if resume_data.get('optimized_summary'):  # CRITICAL - was missing
            text_parts.append(resume_data['optimized_summary'])
        
        # Experiences
        for exp in resume_data.get('experiences', []):
            if exp.get('position'):
                text_parts.append(exp['position'])
            if exp.get('company'):
                text_parts.append(exp['company'])
            if exp.get('description'):
                text_parts.append(exp['description'])
        
        # Projects
        for project in resume_data.get('projects', []):
            if project.get('title'):
                text_parts.append(project['title'])
            if project.get('description'):
                text_parts.append(project['description'])
            if project.get('technologies'):
                text_parts.append(project['technologies'])
        
        # Educations
        for edu in resume_data.get('educations', []):
            if edu.get('degree'):
                text_parts.append(edu['degree'])
            if edu.get('institution'):
                text_parts.append(edu['institution'])
        
        # Skills
        for skill in resume_data.get('skills', []):
            if skill.get('name'):
                text_parts.append(skill['name'])
        
        # Certifications (CRITICAL - was missing)
        for cert in resume_data.get('certifications', []):
            if cert.get('name'):
                text_parts.append(cert['name'])
        
        return ' '.join(text_parts)
