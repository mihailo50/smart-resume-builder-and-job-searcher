"""
Service for job-related Supabase operations.
"""
from typing import Dict, List, Optional, Any
from config.services.base import BaseSupabaseService


class JobPostingService(BaseSupabaseService):
    """Service for managing job postings in Supabase."""
    
    def __init__(self):
        super().__init__('job_postings')
    
    def get_active_jobs(
        self,
        job_type: Optional[str] = None,
        remote_type: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get active job postings with optional filters.
        
        Args:
            job_type: Filter by job type
            remote_type: Filter by remote type
            location: Filter by location
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List: List of job postings
        """
        filters = {'is_active': True}
        
        if job_type:
            filters['job_type'] = job_type
        if remote_type:
            filters['remote_type'] = remote_type
        if location:
            filters['location'] = location
        
        return self.get_all(
            filters=filters,
            order_by='posted_date.desc',
            limit=limit,
            offset=offset
        )
    
    def search_jobs(
        self,
        query: str,
        job_type: Optional[str] = None,
        remote_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search jobs by title, company, or description.
        
        Args:
            query: Search query string
            job_type: Optional job type filter
            remote_type: Optional remote type filter
            location: Optional location filter
            
        Returns:
            List: List of matching job postings
        """
        filters = {'is_active': True}
        if job_type:
            filters['job_type'] = job_type
        if remote_type:
            filters['remote_type'] = remote_type
        if location:
            filters['location'] = location
        
        return self.search(
            search_term=query,
            search_columns=['title', 'company', 'description'],
            filters=filters
        )
    
    def get_jobs_by_company(self, company: str) -> List[Dict[str, Any]]:
        """Get all active jobs from a specific company."""
        return self.get_all(
            filters={'company': company, 'is_active': True},
            order_by='posted_date.desc'
        )


class ApplicationService(BaseSupabaseService):
    """Service for managing job applications."""
    
    def __init__(self):
        super().__init__('applications')
    
    def get_user_applications(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all applications for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            List: List of user applications
        """
        filters = {'user_id': user_id}
        if status:
            filters['status'] = status
        
        return self.get_all(filters=filters, order_by='applied_date.desc')
    
    def get_job_applications(self, job_posting_id: str) -> List[Dict[str, Any]]:
        """Get all applications for a job posting."""
        return self.get_all(
            filters={'job_posting_id': job_posting_id},
            order_by='applied_date.desc'
        )
    
    def create_application(
        self,
        user_id: str,
        job_posting_id: str,
        resume_id: Optional[str] = None,
        cover_letter: Optional[str] = None,
        match_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a new job application.
        
        Args:
            user_id: User ID
            job_posting_id: Job posting ID
            resume_id: Optional resume ID
            cover_letter: Optional cover letter
            match_score: Optional AI match score
            
        Returns:
            Dict: Created application
        """
        data = {
            'user_id': user_id,
            'job_posting_id': job_posting_id,
            'status': 'applied',
        }
        
        if resume_id:
            data['resume_id'] = resume_id
        if cover_letter:
            data['cover_letter'] = cover_letter
        if match_score:
            data['match_score'] = match_score
        
        return self.create(data)


class SavedJobService(BaseSupabaseService):
    """Service for managing saved jobs."""
    
    def __init__(self):
        super().__init__('saved_jobs')
    
    def get_user_saved_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all saved jobs for a user."""
        return self.get_all(
            filters={'user_id': user_id},
            order_by='created_at.desc'
        )
    
    def save_job(self, user_id: str, job_posting_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a job for a user.
        
        Args:
            user_id: User ID
            job_posting_id: Job posting ID
            notes: Optional notes
            
        Returns:
            Dict: Created saved job record
        """
        data = {
            'user_id': user_id,
            'job_posting_id': job_posting_id,
        }
        
        if notes:
            data['notes'] = notes
        
        return self.create(data)


class JobSearchService(BaseSupabaseService):
    """Service for managing saved job searches."""
    
    def __init__(self):
        super().__init__('job_searches')
    
    def get_user_searches(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all job searches for a user.
        
        Args:
            user_id: User ID
            active_only: Only return active searches
            
        Returns:
            List: List of job searches
        """
        filters = {'user_id': user_id}
        if active_only:
            filters['is_active'] = True
        
        return self.get_all(filters=filters, order_by='updated_at.desc')









