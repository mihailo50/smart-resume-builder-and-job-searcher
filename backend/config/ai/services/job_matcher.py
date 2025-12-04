"""
Basic Job Matcher Service (Keyword-based).

Matches resumes with job postings using keyword analysis.
"""
from typing import Dict, List, Optional, Any
from config.ai.utils import extract_text_from_resume_data, extract_keywords_from_text
from collections import Counter


class JobMatcherService:
    """Service for matching resumes with job postings (keyword-based)."""
    
    def __init__(self):
        pass
    
    def match(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        resume_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match a resume with a job description.
        
        Args:
            resume_data: Dictionary containing resume data
            job_description: Job description text
            resume_text: Optional raw resume text (if provided, will be used instead)
            
        Returns:
            Dict: Match results with score and analysis
        """
        # Extract text from resume data if not provided
        if not resume_text:
            resume_text = extract_text_from_resume_data(resume_data)
        
        resume_text_lower = resume_text.lower()
        job_text_lower = job_description.lower()
        
        # Extract keywords from both
        resume_keywords = extract_keywords_from_text(resume_text_lower)
        job_keywords = extract_keywords_from_text(job_text_lower)
        
        # Calculate match score
        match_score = self._calculate_match_score(resume_keywords, job_keywords)
        
        # Find missing keywords
        missing_keywords = self._find_missing_keywords(resume_keywords, job_keywords)
        
        # Find matched keywords
        matched_keywords = self._find_matched_keywords(resume_keywords, job_keywords)
        
        # Calculate category matches
        category_matches = self._calculate_category_matches(
            resume_text_lower, job_text_lower
        )
        
        return {
            'match_score': min(int(match_score * 100), 100),  # 0-100
            'missing_keywords': missing_keywords[:15],  # Top 15 missing
            'matched_keywords': matched_keywords[:15],  # Top 15 matched
            'category_matches': category_matches,
            'resume_keyword_count': len(resume_keywords),
            'job_keyword_count': len(job_keywords),
            'keyword_overlap': len(matched_keywords),
            'recommendations': self._generate_recommendations(
                match_score, missing_keywords, category_matches
            )
        }
    
    def _calculate_match_score(
        self,
        resume_keywords: List[str],
        job_keywords: List[str]
    ) -> float:
        """Calculate match score between resume and job keywords."""
        if not job_keywords:
            return 0.0
        
        # Count keyword frequencies
        resume_counter = Counter(resume_keywords)
        job_counter = Counter(job_keywords)
        
        # Calculate overlap
        matched_count = 0
        total_job_weight = 0
        
        for keyword, job_freq in job_counter.items():
            total_job_weight += job_freq
            if keyword in resume_counter:
                matched_count += min(resume_counter[keyword], job_freq)
        
        # Calculate score as percentage of job keywords matched
        if total_job_weight > 0:
            score = matched_count / total_job_weight
        else:
            score = 0.0
        
        # Normalize based on unique keyword match
        unique_matches = len(set(resume_keywords) & set(job_keywords))
        unique_job_keywords = len(set(job_keywords))
        
        if unique_job_keywords > 0:
            unique_score = unique_matches / unique_job_keywords
            # Combine weighted and unique match scores
            score = (score * 0.6) + (unique_score * 0.4)
        
        return min(score, 1.0)
    
    def _find_missing_keywords(
        self,
        resume_keywords: List[str],
        job_keywords: List[str]
    ) -> List[str]:
        """Find keywords in job description that are missing from resume."""
        resume_keyword_set = set(resume_keywords)
        job_keyword_set = set(job_keywords)
        
        missing = job_keyword_set - resume_keyword_set
        
        # Prioritize by frequency in job description
        job_counter = Counter(job_keywords)
        missing_with_freq = [(kw, job_counter[kw]) for kw in missing]
        missing_with_freq.sort(key=lambda x: x[1], reverse=True)
        
        return [kw.title() for kw, _ in missing_with_freq]  # Capitalize for display
    
    def _find_matched_keywords(
        self,
        resume_keywords: List[str],
        job_keywords: List[str]
    ) -> List[str]:
        """Find keywords that are present in both resume and job description."""
        resume_keyword_set = set(resume_keywords)
        job_keyword_set = set(job_keywords)
        
        matched = resume_keyword_set & job_keyword_set
        
        # Prioritize by combined frequency
        resume_counter = Counter(resume_keywords)
        job_counter = Counter(job_keywords)
        
        matched_with_freq = [
            (kw, resume_counter[kw] + job_counter[kw])
            for kw in matched
        ]
        matched_with_freq.sort(key=lambda x: x[1], reverse=True)
        
        return [kw.title() for kw, _ in matched_with_freq]  # Capitalize for display
    
    def _calculate_category_matches(
        self,
        resume_text: str,
        job_text: str
    ) -> Dict[str, float]:
        """Calculate match scores by category."""
        categories = {
            'technical_skills': [
                'javascript', 'python', 'java', 'react', 'node', 'typescript',
                'aws', 'docker', 'kubernetes', 'sql', 'mongodb', 'postgresql',
                'git', 'api', 'microservices', 'cloud', 'devops'
            ],
            'tools': [
                'git', 'jenkins', 'jira', 'confluence', 'slack', 'docker',
                'kubernetes', 'terraform', 'ansible', 'aws', 'azure', 'gcp'
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd',
                'bdd', 'microservices', 'api', 'rest'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem-solving',
                'collaboration', 'analytical', 'detail-oriented', 'self-motivated'
            ]
        }
        
        category_matches = {}
        
        for category, keywords in categories.items():
            category_keywords_in_job = sum(1 for kw in keywords if kw in job_text)
            
            if category_keywords_in_job == 0:
                category_matches[category] = 0.0
                continue
            
            category_keywords_matched = sum(
                1 for kw in keywords if kw in job_text and kw in resume_text
            )
            
            match_ratio = category_keywords_matched / category_keywords_in_job
            category_matches[category] = min(match_ratio * 100, 100)
        
        return category_matches
    
    def _generate_recommendations(
        self,
        match_score: float,
        missing_keywords: List[str],
        category_matches: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations for improving resume match."""
        recommendations = []
        
        # Overall match score recommendation
        if match_score < 0.5:
            recommendations.append(
                "Low match score. Consider adding more relevant keywords from the job description."
            )
        elif match_score < 0.7:
            recommendations.append(
                "Moderate match score. Add a few more key skills to improve your match."
            )
        
        # Missing keywords recommendation
        if missing_keywords:
            top_missing = missing_keywords[:5]
            recommendations.append(
                f"Consider adding these keywords: {', '.join(top_missing)}"
            )
        
        # Category-specific recommendations
        for category, score in category_matches.items():
            if score < 50:
                category_name = category.replace('_', ' ').title()
                recommendations.append(
                    f"Low {category_name} match. Consider adding relevant {category_name} keywords."
                )
        
        return recommendations

