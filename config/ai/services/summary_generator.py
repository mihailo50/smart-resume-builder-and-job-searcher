"""
Summary Generator Service.

Generates professional resume summaries using OpenAI.
"""
from typing import Dict, Any, Optional
from config.ai.utils import get_openai_client, extract_text_from_resume_data


class SummaryGeneratorService:
    """Service for generating professional resume summaries."""
    
    def __init__(self):
        self.client = None
        self.max_length = 500  # Maximum characters for summary
    
    def enhance(
        self,
        summary_text: str,
        resume_data: Optional[Dict[str, Any]] = None,
        tone: str = 'professional'
    ) -> str:
        """
        Enhance an existing summary using AI.
        
        Args:
            summary_text: The existing summary text to enhance
            resume_data: Optional dictionary containing resume data for context
            tone: Tone of the summary ('professional', 'confident', 'friendly', 'enthusiastic')
            
        Returns:
            str: Enhanced professional summary
        """
        if not summary_text or not summary_text.strip():
            # If no summary provided, generate from scratch
            if resume_data:
                return self.generate(resume_data, existing_summary=None, tone=tone)
            else:
                return "Experienced professional seeking new opportunities."
        
        try:
            self.client = get_openai_client()
        except ValueError:
            # Fallback if OpenAI is not configured
            return summary_text  # Return original if can't enhance
        
        # Build context from resume data if available
        context_parts = []
        if resume_data:
            name = resume_data.get('full_name')
            experiences = resume_data.get('experiences', [])
            educations = resume_data.get('educations', [])
            skills = resume_data.get('skills', [])
            
            if name:
                context_parts.append(f"Name: {name}")
            if experiences:
                latest_exp = experiences[0] if isinstance(experiences, list) else None
                if latest_exp:
                    position = latest_exp.get('position', '')
                    company = latest_exp.get('company', '')
                    if position or company:
                        context_parts.append(f"Current/Recent Position: {position} at {company}")
            if educations:
                latest_edu = educations[0] if isinstance(educations, list) else None
                if latest_edu:
                    degree = latest_edu.get('degree', '')
                    institution = latest_edu.get('institution', '')
                    if degree or institution:
                        context_parts.append(f"Education: {degree} from {institution}")
            if skills:
                skill_names = [skill.get('name', '') for skill in skills[:10]]
                context_parts.append(f"Key Skills: {', '.join(skill_names)}")
        
        context = "\n".join(context_parts) if context_parts else "No additional context available."
        
        # Create enhancement prompt
        tone_descriptions = {
            'professional': 'professional and formal',
            'confident': 'confident and assertive',
            'friendly': 'friendly and approachable',
            'enthusiastic': 'enthusiastic and energetic'
        }
        tone_desc = tone_descriptions.get(tone, 'professional')
        
        prompt = f"""Improve and enhance the following professional resume summary. Make it more impactful, concise, and compelling while keeping all key information.

Use a {tone_desc} tone. The enhanced summary should:
- Be more concise and impactful (maximum {self.max_length} characters)
- Use stronger action verbs
- Highlight achievements and value proposition more effectively
- Maintain all key information from the original
- Be professional and ATS-friendly

{f'Additional Context:\n{context}\n' if context_parts else ''}

Original Summary:
{summary_text}

Generate only the enhanced summary text, no additional formatting or explanations."""
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume writer specializing in creating impactful, ATS-friendly professional summaries. Enhance summaries to be more compelling while preserving all key information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=250,  # Allow more tokens for enhancement
                temperature=0.7,
            )
            
            enhanced_summary = response.choices[0].message.content.strip()
            
            # Trim to max length if needed
            if len(enhanced_summary) > self.max_length:
                enhanced_summary = enhanced_summary[:self.max_length].rsplit(' ', 1)[0] + '...'
            
            return enhanced_summary
        
        except Exception as e:
            # On error, return original summary
            print(f"Error enhancing summary: {e}")
            return summary_text

    def generate(
        self,
        resume_data: Dict[str, Any],
        existing_summary: Optional[str] = None,
        tone: str = 'professional'
    ) -> str:
        """
        Generate a professional summary from resume data.
        
        Args:
            resume_data: Dictionary containing resume data
            existing_summary: Optional existing summary to improve/regenerate
            tone: Tone of the summary ('professional', 'confident', 'friendly', 'enthusiastic')
            
        Returns:
            str: Generated professional summary
        """
        try:
            self.client = get_openai_client()
        except ValueError:
            # Fallback to basic summary if OpenAI is not configured
            return self._generate_basic_summary(resume_data)
        
        # Extract key information from resume
        name = resume_data.get('full_name', 'Candidate')
        experiences = resume_data.get('experiences', [])
        educations = resume_data.get('educations', [])
        skills = resume_data.get('skills', [])
        
        # Build context for AI
        context = self._build_context(name, experiences, educations, skills, existing_summary)
        
        # Create prompt
        prompt = self._create_prompt(context, tone)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume writer. Generate concise, impactful professional summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,  # Limit tokens for concise summary
                temperature=0.7,
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Trim to max length if needed
            if len(summary) > self.max_length:
                summary = summary[:self.max_length].rsplit(' ', 1)[0] + '...'
            
            return summary
        
        except Exception as e:
            # Fallback to basic summary on error
            print(f"Error generating AI summary: {e}")
            return self._generate_basic_summary(resume_data)
    
    def _build_context(
        self,
        name: str,
        experiences: list,
        educations: list,
        skills: list,
        existing_summary: Optional[str] = None
    ) -> str:
        """Build context string from resume data."""
        context_parts = []
        
        # Add name
        if name:
            context_parts.append(f"Name: {name}")
        
        # Add most recent experience
        if experiences:
            latest_exp = experiences[0] if isinstance(experiences, list) else None
            if latest_exp:
                position = latest_exp.get('position', '')
                company = latest_exp.get('company', '')
                if position or company:
                    context_parts.append(f"Current/Recent Position: {position} at {company}")
                if latest_exp.get('description'):
                    context_parts.append(f"Key Responsibilities: {latest_exp['description'][:200]}")
        
        # Add education
        if educations:
            latest_edu = educations[0] if isinstance(educations, list) else None
            if latest_edu:
                degree = latest_edu.get('degree', '')
                institution = latest_edu.get('institution', '')
                if degree or institution:
                    context_parts.append(f"Education: {degree} from {institution}")
        
        # Add top skills
        if skills:
            skill_names = [skill.get('name', '') for skill in skills[:10]]
            context_parts.append(f"Key Skills: {', '.join(skill_names)}")
        
        # Add existing summary if provided
        if existing_summary:
            context_parts.append(f"Existing Summary: {existing_summary}")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, context: str, tone: str) -> str:
        """Create prompt for OpenAI."""
        tone_descriptions = {
            'professional': 'professional and formal',
            'confident': 'confident and assertive',
            'friendly': 'friendly and approachable',
            'enthusiastic': 'enthusiastic and energetic'
        }
        
        tone_desc = tone_descriptions.get(tone, 'professional')
        
        prompt = f"""Generate a professional resume summary (maximum {self.max_length} characters) based on the following information.

Use a {tone_desc} tone. The summary should:
- Highlight key achievements and experiences
- Emphasize relevant skills and expertise
- Be concise and impactful
- Start with years of experience or key qualification if available
- Focus on value proposition

Resume Information:
{context}

Generate only the summary text, no additional formatting or explanations."""
        
        return prompt
    
    def _generate_basic_summary(self, resume_data: Dict[str, Any]) -> str:
        """
        Generate a basic summary without AI (fallback).
        
        Args:
            resume_data: Dictionary containing resume data
            
        Returns:
            str: Basic summary
        """
        summary_parts = []
        
        # Extract key info
        experiences = resume_data.get('experiences', [])
        educations = resume_data.get('educations', [])
        skills = resume_data.get('skills', [])
        
        # Start with experience
        if experiences:
            latest_exp = experiences[0] if isinstance(experiences, list) else None
            if latest_exp:
                position = latest_exp.get('position', '')
                company = latest_exp.get('company', '')
                if position:
                    summary_parts.append(f"Experienced {position.lower()}")
                    if company:
                        summary_parts.append(f"with a background at {company}")
        
        # Add skills
        if skills:
            skill_names = [skill.get('name', '') for skill in skills[:5]]
            if skill_names:
                summary_parts.append(f"proficient in {', '.join(skill_names)}")
        
        # Add education
        if educations and not summary_parts:
            latest_edu = educations[0] if isinstance(educations, list) else None
            if latest_edu:
                degree = latest_edu.get('degree', '')
                if degree:
                    summary_parts.append(f"{degree} graduate")
        
        # Combine into summary
        summary = ". ".join(summary_parts)
        
        if summary:
            summary += "."
        else:
            summary = "Experienced professional seeking new opportunities."
        
        # Trim to max length
        if len(summary) > self.max_length:
            summary = summary[:self.max_length].rsplit(' ', 1)[0] + '...'
        
        return summary



