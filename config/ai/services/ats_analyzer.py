"""
ATS Analyzer Service.

Analyzes resumes for ATS (Applicant Tracking System) compatibility.
"""
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ATSAnalyzerService:
    """Service for analyzing resumes for ATS compatibility."""
    
    def __init__(self):
        self.logger = logger
    
    def analyze(
        self,
        resume_data: Optional[Dict[str, Any]] = None,
        resume_text: Optional[str] = None,
        job_desc: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a resume for ATS compatibility.
        
        Args:
            resume_data: Dictionary containing structured resume data
            resume_text: Plain text version of the resume
            job_desc: Optional job description for targeted analysis
            
        Returns:
            Dict containing analysis results with keys:
            - ats_score: Integer 0-100
            - missing_keywords: List of missing keywords
            - suggestions: List of suggestion dicts with 'type', 'text', 'priority'
            - readability_score: Integer 0-100
            - bullet_strength: Integer 0-100
            - quantifiable_achievements: Integer 0-100
            - keyword_score: Integer 0-100 (optional)
            - formatting_score: Integer 0-100 (optional)
            - detailed_analysis: Dict with additional details (optional)
        """
        # Basic analysis implementation
        # In production, this would use AI/ML models for more sophisticated analysis
        
        # Extract text if resume_data is provided
        if resume_data and not resume_text:
            resume_text = self._extract_text_from_data(resume_data)
        
        # Basic scoring (placeholder - should be enhanced with actual analysis)
        ats_score = 75  # Default score
        readability_score = 80
        bullet_strength = 70
        quantifiable_achievements = 65
        keyword_score = 70
        formatting_score = 75
        
        missing_keywords: List[str] = []
        suggestions: List[Dict[str, str]] = []
        
        # Basic keyword analysis if job description provided
        if job_desc and resume_text:
            missing_keywords = self._find_missing_keywords(resume_text, job_desc)
            if missing_keywords:
                ats_score = max(50, ats_score - len(missing_keywords) * 5)
                suggestions.append({
                    'type': 'keyword',
                    'text': f"Add {len(missing_keywords)} missing keywords from job description",
                    'priority': 'high'
                })
        
        # Basic suggestions based on resume content
        if resume_text:
            if len(resume_text) < 500:
                suggestions.append({
                    'type': 'content',
                    'text': 'Resume seems too short. Consider adding more detail.',
                    'priority': 'medium'
                })
            
            if not any(char.isdigit() for char in resume_text):
                suggestions.append({
                    'type': 'achievement',
                    'text': 'Add quantifiable achievements (numbers, percentages, metrics)',
                    'priority': 'high'
                })
                quantifiable_achievements = 40
        
        # Generate suggestions if score is low
        if ats_score < 60:
            suggestions.append({
                'type': 'general',
                'text': 'Resume needs improvement for ATS compatibility',
                'priority': 'high'
            })
        
        return {
            'ats_score': max(0, min(100, ats_score)),
            'missing_keywords': missing_keywords[:10],  # Limit to top 10
            'suggestions': suggestions,
            'readability_score': readability_score,
            'bullet_strength': bullet_strength,
            'quantifiable_achievements': quantifiable_achievements,
            'keyword_score': keyword_score,
            'formatting_score': formatting_score,
            'detailed_analysis': {
                'total_words': len(resume_text.split()) if resume_text else 0,
                'has_contact_info': bool(resume_data and resume_data.get('email')),
                'has_experience': bool(resume_data and resume_data.get('experiences')),
            }
        }
    
    def _extract_text_from_data(self, resume_data: Dict[str, Any]) -> str:
        """Extract plain text from structured resume data."""
        text_parts = []
        
        # Add personal info
        if resume_data.get('full_name'):
            text_parts.append(resume_data['full_name'])
        if resume_data.get('title'):
            text_parts.append(resume_data['title'])
        if resume_data.get('summary'):
            text_parts.append(resume_data['summary'])
        if resume_data.get('optimized_summary'):
            text_parts.append(resume_data['optimized_summary'])
        
        # Add experiences
        for exp in resume_data.get('experiences', []):
            if exp.get('position'):
                text_parts.append(exp['position'])
            if exp.get('company'):
                text_parts.append(exp['company'])
            if exp.get('description'):
                text_parts.append(exp['description'])
        
        # Add educations
        for edu in resume_data.get('educations', []):
            if edu.get('degree'):
                text_parts.append(edu['degree'])
            if edu.get('institution'):
                text_parts.append(edu['institution'])
        
        # Add skills
        for skill in resume_data.get('skills', []):
            if skill.get('name'):
                text_parts.append(skill['name'])
        
        return ' '.join(text_parts)
    
    def _find_missing_keywords(self, resume_text: str, job_desc: str) -> List[str]:
        """Find important keywords from job description missing in resume."""
        import re
        
        # Extract keywords from job description (simple approach)
        # In production, use NLP to extract important terms
        job_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', job_desc.lower()))
        resume_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', resume_text.lower()))
        
        # Common stop words to ignore
        stop_words = {
            'with', 'from', 'this', 'that', 'have', 'will', 'would',
            'should', 'could', 'been', 'being', 'them', 'their', 'there',
            'these', 'those', 'which', 'where', 'when', 'what', 'work',
            'years', 'year', 'experience', 'skills', 'ability', 'abilities'
        }
        
        # Find missing important keywords
        missing = job_words - resume_words - stop_words
        
        # Return top missing keywords (prioritize longer words)
        return sorted(missing, key=len, reverse=True)[:10]
