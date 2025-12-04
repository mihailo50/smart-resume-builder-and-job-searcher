"""
Suggestion Applier Service.

Applies AI suggestions to resume by updating Supabase directly,
avoiding hallucinations and maintaining data integrity.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from django.conf import settings
from config.services.resume_service import (
    ResumeService,
    ExperienceService,
    ProjectService,
    SkillService,
    CertificationService
)

logger = logging.getLogger(__name__)


class SuggestionApplierService:
    """Service for applying AI suggestions to resume data in Supabase."""
    
    def __init__(self):
        self.logger = logger
        self.resume_service = ResumeService()
        self.experience_service = ExperienceService()
        self.project_service = ProjectService()
        self.skill_service = SkillService()
        self.certification_service = CertificationService()
        self.openai_client = None
        
        try:
            if settings.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
    
    def apply_suggestions(
        self,
        resume_id: str,
        resume_data: Dict[str, Any],
        suggestions: List[Dict[str, Any]],
        missing_keywords: List[str],
        resume_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply suggestions to resume by updating Supabase directly.
        
        Args:
            resume_id: UUID of the resume
            resume_data: Current resume data structure
            suggestions: List of suggestion dicts
            missing_keywords: List of missing keywords to incorporate
            resume_text: Optional resume text for context
            
        Returns:
            Dict with updated resume_data and optimized_text
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        updated_data = resume_data.copy()
        changes_applied = []
        
        # Parse suggestions by type
        keyword_suggestions = [s for s in suggestions if s.get('type') == 'keyword']
        achievement_suggestions = [s for s in suggestions if s.get('type') == 'achievement']
        formatting_suggestions = [s for s in suggestions if s.get('type') == 'formatting']
        
        # Apply keyword suggestions
        if missing_keywords or keyword_suggestions:
            updated_data, keyword_changes = self._apply_keyword_suggestions(
                resume_id=resume_id,
                resume_data=updated_data,
                missing_keywords=missing_keywords
            )
            changes_applied.extend(keyword_changes)
        
        # Apply achievement suggestions (enhance bullets with metrics)
        if achievement_suggestions:
            updated_data, achievement_changes = self._apply_achievement_suggestions(
                resume_id=resume_id,
                resume_data=updated_data
            )
            changes_applied.extend(achievement_changes)
        
        # Apply formatting suggestions
        if formatting_suggestions:
            updated_data, formatting_changes = self._apply_formatting_suggestions(
                resume_id=resume_id,
                resume_data=updated_data
            )
            changes_applied.extend(formatting_changes)
        
        # Refresh data from Supabase to get latest
        refreshed_data = self.resume_service.get_resume_with_details(resume_id)
        
        # Generate optimized text from updated data
        optimized_text = self._generate_optimized_text(refreshed_data)
        
        return {
            'resume_data': refreshed_data,  # Full updated resume JSON
            'optimized_text': optimized_text,
            'changes_applied': changes_applied
        }
    
    def _apply_keyword_suggestions(
        self,
        resume_id: str,
        resume_data: Dict[str, Any],
        missing_keywords: List[str]
    ) -> tuple:
        """Apply keyword suggestions by adding to skills or relevant sections."""
        changes = []
        updated_data = resume_data.copy()
        
        if not missing_keywords:
            return updated_data, changes
        
        # Use AI to determine best placement for keywords
        try:
            prompt = f"""Given these missing keywords: {', '.join(missing_keywords[:10])}
            
And this resume structure:
- Skills: {[s.get('name', '') for s in resume_data.get('skills', [])]}
- Experience descriptions: {[exp.get('description', '')[:100] for exp in resume_data.get('experiences', [])[:2]]}
- Projects: {[p.get('title', '') for p in resume_data.get('projects', [])[:2]]}

Determine the best placement for each keyword:
1. If it's a technology/tool → add to Skills section
2. If it's relevant to a specific experience → suggest adding to that experience description
3. If it's relevant to a project → suggest adding to that project description

Return JSON:
{{
  "skills_to_add": ["keyword1", "keyword2"],
  "experience_updates": [
    {{"index": 0, "keywords": ["keyword"], "suggestion": "Add to description naturally"}},
  ],
  "project_updates": [
    {{"index": 0, "keywords": ["keyword"], "suggestion": "Add to description naturally"}}
  ]
}}

Only suggest updates that make sense. Don't add keywords that don't fit."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume optimizer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            
            # Add to skills
            if result.get('skills_to_add'):
                existing_skills = {s.get('name', '').lower() for s in resume_data.get('skills', [])}
                for keyword in result['skills_to_add']:
                    if keyword.lower() not in existing_skills:
                        # Add new skill
                        try:
                            self.skill_service.create({
                                'resume_id': resume_id,
                                'name': keyword.title(),
                                'category': 'Technical',
                                'order': len(resume_data.get('skills', []))
                            })
                            changes.append(f"Added '{keyword}' to Skills section")
                        except Exception as e:
                            logger.warning(f"Failed to add skill {keyword}: {e}")
            
            # Update experiences
            if result.get('experience_updates'):
                experiences = resume_data.get('experiences', [])
                for update in result['experience_updates']:
                    idx = update.get('index')
                    if 0 <= idx < len(experiences):
                        exp = experiences[idx]
                        keywords = update.get('keywords', [])
                        if keywords and exp.get('id'):
                            # Enhance description with keywords naturally
                            enhanced_desc = self._enhance_description_with_keywords(
                                exp.get('description', ''),
                                keywords
                            )
                            try:
                                self.experience_service.update(exp['id'], {
                                    'description': enhanced_desc
                                })
                                changes.append(f"Enhanced experience '{exp.get('position', '')}' with keywords: {', '.join(keywords)}")
                            except Exception as e:
                                logger.warning(f"Failed to update experience: {e}")
            
            # Update projects
            if result.get('project_updates'):
                projects = resume_data.get('projects', [])
                for update in result['project_updates']:
                    idx = update.get('index')
                    if 0 <= idx < len(projects):
                        project = projects[idx]
                        keywords = update.get('keywords', [])
                        if keywords and project.get('id'):
                            enhanced_desc = self._enhance_description_with_keywords(
                                project.get('description', ''),
                                keywords
                            )
                            try:
                                self.project_service.update(project['id'], {
                                    'description': enhanced_desc
                                })
                                changes.append(f"Enhanced project '{project.get('title', '')}' with keywords: {', '.join(keywords)}")
                            except Exception as e:
                                logger.warning(f"Failed to update project: {e}")
        
        except Exception as e:
            logger.error(f"Error applying keyword suggestions: {e}")
            # Fallback: just add to skills
            for keyword in missing_keywords[:5]:
                try:
                    self.skill_service.create({
                        'resume_id': resume_id,
                        'name': keyword.title(),
                        'category': 'Technical',
                        'order': len(resume_data.get('skills', []))
                    })
                    changes.append(f"Added '{keyword}' to Skills section")
                except Exception:
                    pass
        
        # Refresh data
        updated_data = self.resume_service.get_resume_with_details(resume_id)
        return updated_data, changes
    
    def _apply_achievement_suggestions(
        self,
        resume_id: str,
        resume_data: Dict[str, Any]
    ) -> tuple:
        """Enhance bullets with quantifiable metrics."""
        changes = []
        updated_data = resume_data.copy()
        
        # Enhance experience descriptions
        for exp in resume_data.get('experiences', []):
            if exp.get('description') and exp.get('id'):
                # Check if already has numbers
                if not any(char.isdigit() for char in exp['description']):
                    # Try to enhance with metrics
                    enhanced = self._enhance_with_metrics(exp['description'])
                    if enhanced != exp['description']:
                        try:
                            self.experience_service.update(exp['id'], {
                                'description': enhanced
                            })
                            changes.append(f"Added metrics to experience '{exp.get('position', '')}'")
                        except Exception as e:
                            logger.warning(f"Failed to enhance experience: {e}")
        
        # Refresh data
        updated_data = self.resume_service.get_resume_with_details(resume_id)
        return updated_data, changes
    
    def _apply_formatting_suggestions(
        self,
        resume_id: str,
        resume_data: Dict[str, Any]
    ) -> tuple:
        """Apply formatting improvements."""
        changes = []
        updated_data = resume_data.copy()
        
        # Convert descriptions to bullet format if needed
        for exp in resume_data.get('experiences', []):
            if exp.get('description') and exp.get('id'):
                # Check if already has bullets
                if '•' not in exp['description'] and '-' not in exp['description']:
                    formatted = self._format_as_bullets(exp['description'])
                    if formatted != exp['description']:
                        try:
                            self.experience_service.update(exp['id'], {
                                'description': formatted
                            })
                            changes.append(f"Formatted experience '{exp.get('position', '')}' as bullets")
                        except Exception as e:
                            logger.warning(f"Failed to format experience: {e}")
        
        updated_data = self.resume_service.get_resume_with_details(resume_id)
        return updated_data, changes
    
    def _enhance_description_with_keywords(
        self,
        description: str,
        keywords: List[str]
    ) -> str:
        """Naturally incorporate keywords into description."""
        if not description or not keywords:
            return description
        
        # Use AI to naturally incorporate keywords
        try:
            prompt = f"""Enhance this resume description by naturally incorporating these keywords: {', '.join(keywords)}

Original description:
{description}

Return the enhanced description with keywords naturally integrated. Don't add false information. Only use the keywords if they make sense in context."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Enhance descriptions naturally without adding false information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            enhanced = response.choices[0].message.content.strip()
            # Remove markdown if present
            if '```' in enhanced:
                enhanced = enhanced.split('```')[1].strip()
                if enhanced.startswith('text\n'):
                    enhanced = enhanced[5:].strip()
            
            return enhanced
        
        except Exception as e:
            logger.warning(f"Failed to enhance description with keywords: {e}")
            return description
    
    def _enhance_with_metrics(self, description: str) -> str:
        """Suggest adding metrics to description (conservative - only if makes sense)."""
        # Don't hallucinate metrics - just return original
        # In production, could use AI to suggest realistic metrics based on context
        return description
    
    def _format_as_bullets(self, text: str) -> str:
        """Convert text to bullet format."""
        lines = text.split('\n')
        bullets = []
        for line in lines:
            line = line.strip()
            if line:
                if not line.startswith(('•', '-', '*')):
                    bullets.append(f"• {line}")
                else:
                    bullets.append(line)
        return '\n'.join(bullets)
    
    def _generate_optimized_text(self, resume_data: Dict[str, Any]) -> str:
        """Generate optimized text from updated resume data."""
        from config.ai.utils import extract_text_from_resume_data
        return extract_text_from_resume_data(resume_data)

