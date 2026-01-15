"""
Service for user-related Supabase operations.
"""
from typing import Dict, List, Optional, Any
from config.services.base import BaseSupabaseService


class UserProfileService(BaseSupabaseService):
    """Service for managing user profiles in Supabase."""
    
    def __init__(self):
        super().__init__('user_profiles')
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: User profile or None if not found
        """
        profiles = self.get_all(filters={'user_id': user_id}, limit=1)
        return profiles[0] if profiles else None
    
    def create_or_update_profile(
        self,
        user_id: str,
        avatar_url: Optional[str] = None,
        phone_number: Optional[str] = None,
        location: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        github_url: Optional[str] = None,
        portfolio_url: Optional[str] = None,
        bio: Optional[str] = None,
        email: Optional[str] = None,
        date_of_birth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update user profile.
        
        Args:
            user_id: User ID
            avatar_url: Optional avatar URL
            phone_number: Optional phone number
            location: Optional location (city, state, country, etc.)
            linkedin_url: Optional LinkedIn URL
            github_url: Optional GitHub URL
            portfolio_url: Optional portfolio URL
            bio: Optional bio text
            email: Optional contact email (may differ from auth email)
            date_of_birth: Optional date of birth (YYYY-MM-DD format)
            
        Returns:
            Dict: Created or updated profile
        """
        existing = self.get_user_profile(user_id)
        
        data = {'user_id': user_id}
        
        if avatar_url is not None:
            data['avatar'] = avatar_url
        if phone_number is not None:
            data['phone_number'] = phone_number
        if location is not None:
            data['location'] = location
        if linkedin_url is not None:
            data['linkedin_url'] = linkedin_url
        if github_url is not None:
            data['github_url'] = github_url
        if portfolio_url is not None:
            data['portfolio_url'] = portfolio_url
        if bio is not None:
            data['bio'] = bio
        if email is not None:
            data['email'] = email
        if date_of_birth is not None:
            data['date_of_birth'] = date_of_birth
        
        if existing:
            return self.update(existing['id'], data)
        else:
            return self.create(data)







