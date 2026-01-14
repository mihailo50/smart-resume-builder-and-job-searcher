"""
Service for resume-related Supabase operations.
"""
import logging
from typing import Dict, List, Optional, Any
from config.services.base import BaseSupabaseService

logger = logging.getLogger(__name__)


class ResumeService(BaseSupabaseService):
    """Service for managing resumes in Supabase."""
    
    def __init__(self):
        super().__init__('resumes')
    
    def get_user_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all resumes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List: List of resumes
        """
        return self.get_all(
            filters={'user_id': user_id},
            order_by='updated_at.desc'
        )
    
    def get_resume_with_details(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resume with all related data (experiences, educations, skills, etc.)
        AND user profile data (contact info).
        
        Args:
            resume_id: Resume ID
            
        Returns:
            Dict: Resume with all related data or None if not found
        """
        resume = self.get_by_id(resume_id)
        if not resume:
            return None
        
        # Fetch related data
        education_service = EducationService()
        experience_service = ExperienceService()
        skill_service = SkillService()
        project_service = ProjectService()
        certification_service = CertificationService()
        language_service = LanguageService()
        interest_service = InterestService()
        
        resume['educations'] = education_service.get_by_resume_id(resume_id)
        resume['experiences'] = experience_service.get_by_resume_id(resume_id)
        resume['skills'] = skill_service.get_by_resume_id(resume_id)
        resume['projects'] = project_service.get_by_resume_id(resume_id)
        resume['certifications'] = certification_service.get_by_resume_id(resume_id)
        
        # Handle languages (may not exist in all databases)
        try:
            resume['languages'] = language_service.get_by_resume_id(resume_id)
            logger.debug(f"Fetched {len(resume.get('languages', []))} languages for resume {resume_id}")
        except Exception as e:
            if 'PGRST205' in str(e) or 'Could not find the table' in str(e):
                logger.warning(f"Languages table not found, returning empty list. Run migration for languages table.")
            else:
                logger.error(f"Error fetching languages: {e}")
            resume['languages'] = []
        
        # Handle interests (may not exist in all databases)
        try:
            resume['interests'] = interest_service.get_by_resume_id(resume_id)
            logger.debug(f"Fetched {len(resume.get('interests', []))} interests for resume {resume_id}")
        except Exception as e:
            if 'PGRST205' in str(e) or 'Could not find the table' in str(e):
                logger.warning(f"Interests table not found, returning empty list. Run migration 012_create_interests_table.sql")
            else:
                logger.error(f"Error fetching interests: {e}")
            resume['interests'] = []
        
        # Fetch user profile data (contact info: email, phone, location, linkedin, github, portfolio)
        user_id = resume.get('user_id')
        if user_id:
            try:
                from config.services.user_service import UserProfileService
                profile_service = UserProfileService()
                user_profile = profile_service.get_user_profile(user_id)
                
                if user_profile:
                    # Map user_profile fields to resume fields for contact info
                    # Email is now stored in user_profiles (preferred contact email)
                    resume['email'] = user_profile.get('email', '')
                    resume['phone'] = user_profile.get('phone_number', '')
                    resume['location'] = user_profile.get('location', '')
                    resume['linkedin_url'] = user_profile.get('linkedin_url', '')
                    resume['github_url'] = user_profile.get('github_url', '')
                    resume['portfolio_url'] = user_profile.get('portfolio_url', '')
                    resume['user_profile'] = user_profile
                    logger.debug(f"Fetched user profile for resume {resume_id}: email={bool(resume.get('email'))}, phone={bool(resume.get('phone'))}, location={bool(resume.get('location'))}")
                
                # Fallback: if no email in profile, try to get from Supabase auth
                if not resume.get('email'):
                    try:
                        from config.supabase import get_supabase_client
                        supabase = get_supabase_client()
                        user_response = supabase.auth.admin.get_user_by_id(user_id)
                        if user_response and user_response.user:
                            resume['email'] = user_response.user.email or ''
                            logger.debug(f"Fetched auth email as fallback for resume {resume_id}: {bool(resume.get('email'))}")
                    except Exception as e:
                        logger.warning(f"Could not fetch user email from auth: {e}")
            except Exception as e:
                logger.warning(f"Error fetching user profile for resume {resume_id}: {e}")
        
        logger.info(
            f"Resume {resume_id} data summary: "
            f"experiences={len(resume.get('experiences', []))}, "
            f"projects={len(resume.get('projects', []))}, "
            f"educations={len(resume.get('educations', []))}, "
            f"certifications={len(resume.get('certifications', []))}, "
            f"skills={len(resume.get('skills', []))}, "
            f"languages={len(resume.get('languages', []))}, "
            f"interests={len(resume.get('interests', []))}, "
            f"has_contact_info={bool(resume.get('email') or resume.get('phone') or resume.get('location'))}"
        )
        return resume


# Related service classes for resume sections
class EducationService(BaseSupabaseService):
    """Service for managing educations."""
    
    def __init__(self):
        super().__init__('educations')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all educations for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc,start_date.desc'
        )


class ExperienceService(BaseSupabaseService):
    """Service for managing experiences."""
    
    def __init__(self):
        super().__init__('experiences')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all experiences for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc,start_date.desc'
        )


class SkillService(BaseSupabaseService):
    """Service for managing skills."""
    
    def __init__(self):
        super().__init__('skills')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all skills for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc'
        )


class ProjectService(BaseSupabaseService):
    """Service for managing projects."""
    
    def __init__(self):
        super().__init__('projects')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc,start_date.desc'
        )


class CertificationService(BaseSupabaseService):
    """Service for managing certifications."""
    
    def __init__(self):
        super().__init__('certifications')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all certifications for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc,issue_date.desc'
        )


class LanguageService(BaseSupabaseService):
    """Service for managing languages."""
    
    def __init__(self):
        super().__init__('languages')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all languages for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc'
        )


class InterestService(BaseSupabaseService):
    """Service for managing interests."""
    
    def __init__(self):
        super().__init__('interests')
    
    def get_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all interests for a resume."""
        return self.get_all(
            filters={'resume_id': resume_id},
            order_by='order.asc'
        )
