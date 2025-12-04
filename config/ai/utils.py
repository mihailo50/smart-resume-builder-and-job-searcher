"""
Utilities for AI services.
"""
import os
import re
from typing import Optional, List
from collections import Counter
from openai import OpenAI
from django.conf import settings


def get_openai_client() -> OpenAI:
    """
    Get OpenAI client instance.
    
    Returns:
        OpenAI: Configured OpenAI client
        
    Raises:
        ValueError: If OpenAI API key is not configured
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError(
            "OpenAI API key not configured. "
            "Set OPENAI_API_KEY in your .env file."
        )
    
    return OpenAI(api_key=api_key)


def extract_text_from_resume_data(resume_data: dict) -> str:
    """
    Extract text content from resume data structure.
    
    Args:
        resume_data: Dictionary containing resume data
        
    Returns:
        str: Combined text content from resume
    """
    text_parts = []
    
    # Personal info
    if resume_data.get('summary'):
        text_parts.append(resume_data['summary'])
    
    # Experiences
    if resume_data.get('experiences'):
        for exp in resume_data['experiences']:
            text_parts.append(f"{exp.get('position', '')} at {exp.get('company', '')}")
            if exp.get('description'):
                text_parts.append(exp['description'])
    
    # Education
    if resume_data.get('educations'):
        for edu in resume_data['educations']:
            text_parts.append(f"{edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('institution', '')}")
            if edu.get('description'):
                text_parts.append(edu['description'])
    
    # Skills
    if resume_data.get('skills'):
        skill_names = [skill.get('name', '') for skill in resume_data['skills']]
        text_parts.append(', '.join(skill_names))
    
    return ' '.join(text_parts)


def extract_keywords_from_text(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text (simple implementation).
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        
    Returns:
        List[str]: List of potential keywords
    """
    # Simple keyword extraction - split by whitespace/punctuation
    # Remove punctuation and split
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Return unique keywords with frequency info (simplified)
    keyword_counts = Counter(keywords)
    
    # Return top keywords
    return [word for word, count in keyword_counts.most_common(50)]

