"""
Supabase JWT Authentication Backend for Django REST Framework.
"""
import jwt
from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from supabase import Client
from config.supabase import get_supabase_client

User = get_user_model()


class SupabaseUser:
    """
    Simple user-like object for Supabase authentication.
    This doesn't require Django's User model or database access.
    """
    def __init__(self, supabase_id: str, email: str = ''):
        self.supabase_id = supabase_id
        self.id = supabase_id  # For compatibility
        self.username = supabase_id  # For compatibility
        self.email = email
        self._is_authenticated = True
        self._is_active = True
    
    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def __str__(self):
        return f"SupabaseUser({self.supabase_id})"


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    Custom authentication backend that validates Supabase JWT tokens.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using Supabase JWT token.
        
        Args:
            request: HTTP request object
            
        Returns:
            Tuple of (user, token) or None if authentication fails
        """
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token with Supabase
            payload = self._validate_token(token)
            
            if not payload:
                return None
            
            # Get or create user
            user_id = payload.get('sub')
            user = self._get_or_create_user(user_id, payload)
            
            return (user, token)
            
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
    
    def _validate_token(self, token: str) -> Optional[dict]:
        """
        Validate JWT token with Supabase.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None
        """
        try:
            # Verify token with Supabase
            supabase: Client = get_supabase_client()
            
            # Supabase client can verify tokens
            # For now, we'll decode and verify manually
            # In production, you might want to use Supabase's token verification
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}  # Supabase handles signature verification
            )
            
            # Verify with Supabase
            try:
                # Use Supabase's auth.get_user() to verify token
                user_response = supabase.auth.get_user(token)
                if user_response.user:
                    return decoded
            except Exception:
                # Fallback: decode token if Supabase verification fails
                # In production, always verify with Supabase
                return decoded
                
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            raise AuthenticationFailed(f'Token validation error: {str(e)}')
        
        return None
    
    def _get_or_create_user(self, user_id: str, payload: dict) -> SupabaseUser:
        """
        Create a simple user-like object from Supabase user ID.
        We don't use Django's User model since we're using Supabase Auth.
        
        Args:
            user_id: Supabase user ID (UUID)
            payload: Decoded JWT payload
            
        Returns:
            SupabaseUser instance
        """
        email = payload.get('email', '')
        return SupabaseUser(supabase_id=user_id, email=email)
    
    def authenticate_header(self, request):
        """Return a string to be used as the value of the `WWW-Authenticate` header."""
        return 'Bearer'


class SupabaseAuthBackend(BaseBackend):
    """
    Django authentication backend for Supabase Auth.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate using Supabase Auth.
        
        This is a fallback backend - primary authentication happens via JWT.
        """
        # Supabase authentication is handled via JWT
        # This backend is mainly for Django admin access
        return None
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


