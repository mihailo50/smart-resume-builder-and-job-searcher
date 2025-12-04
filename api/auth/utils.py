"""
Authentication utility functions.
"""
from typing import Optional
from rest_framework.request import Request
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_from_request(request: Request) -> Optional[User]:
    """
    Extract user from authenticated request.
    
    Args:
        request: DRF request object
        
    Returns:
        User instance or None
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


def get_supabase_user_id(request: Request) -> Optional[str]:
    """
    Get Supabase user ID from request.
    
    Args:
        request: DRF request object
        
    Returns:
        Supabase user ID (UUID string) or None
    """
    user = get_user_from_request(request)
    if user:
        # Supabase user_id is stored as username
        return user.username
    return None








