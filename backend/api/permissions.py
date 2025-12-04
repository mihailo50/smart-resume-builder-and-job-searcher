"""
Custom permissions for API endpoints.
"""
from rest_framework.permissions import BasePermission
from api.auth.utils import get_supabase_user_id


class IsAuthenticated(BasePermission):
    """Allow only authenticated users."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsResumeOwner(BasePermission):
    """Only allow owners to access their resumes."""
    
    def has_object_permission(self, request, view, obj):
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return False
        
        # Check if obj has user_id attribute
        if hasattr(obj, 'user_id'):
            return str(obj.user_id) == supabase_user_id
        
        # Check if obj is a dict (from Supabase response)
        if isinstance(obj, dict):
            return str(obj.get('user_id')) == supabase_user_id
        
        return False


class IsOwner(BasePermission):
    """Generic permission to check if user owns the resource."""
    
    def has_object_permission(self, request, view, obj):
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return False
        
        # Check various user_id field names
        user_id_fields = ['user_id', 'owner_id', 'created_by']
        
        for field in user_id_fields:
            if hasattr(obj, field):
                return str(getattr(obj, field)) == supabase_user_id
            
            if isinstance(obj, dict) and field in obj:
                return str(obj.get(field)) == supabase_user_id
        
        return False


class IsSubscriptionActive(BasePermission):
    """Check if user has active subscription for premium features."""
    
    def has_permission(self, request, view):
        # TODO: Implement subscription check
        # For now, allow all authenticated users
        # Later: Check subscription status from database
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)








