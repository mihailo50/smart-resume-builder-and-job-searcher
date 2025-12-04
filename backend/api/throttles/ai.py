"""
Server-side throttles for guest AI usage.
"""
from __future__ import annotations

from django.core.cache import cache
from django.utils.crypto import salted_hmac
from typing import Optional
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
from api.auth.utils import get_supabase_user_id


class GuestAIRateLimiter:
    """
    Rate limiter for unauthenticated users hitting AI endpoints.
    Uses IP + User-Agent (+ guest_id cookie when available) to fingerprint guests.
    """

    WINDOW = 24 * 60 * 60  # 24 hours

    LIMITS = {
        'parse_resume_file': 2,
        'analyze_resume': 5,  # 5 per day for guests
        'apply_suggestions': 5,  # 5 per day for guests
        'enhance_summary': 1,  # Limited to 1 call per 24h for guests
    }

    def __init__(self, request):
        self.request = request
        self.user_id = get_supabase_user_id(request)
        self._fingerprint: Optional[str] = None

    def is_authenticated(self) -> bool:
        return bool(self.user_id)

    def _build_fingerprint(self) -> str:
        """
        Create a stable fingerprint for unauthenticated users.
        Prefers guest_id cookie if available, otherwise uses IP + User-Agent.
        """
        if self._fingerprint:
            return self._fingerprint

        if self.is_authenticated():
            self._fingerprint = str(self.user_id)
            return self._fingerprint

        guest_id = (
            self.request.COOKIES.get('guest_id')
            or self.request.query_params.get('guest_id')
            or (hasattr(self.request, 'data') and self.request.data.get('guest_id'))
        )

        if guest_id:
            raw = f"guest:{guest_id}"
        else:
            ip = (
                self.request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or self.request.META.get('REMOTE_ADDR', 'unknown')
            )
            user_agent = self.request.META.get('HTTP_USER_AGENT', 'unknown')
            raw = f"{ip}:{user_agent}"

        self._fingerprint = salted_hmac('guest_ai_fingerprint', raw).hexdigest()
        return self._fingerprint

    def _cache_key(self, feature: str) -> str:
        fingerprint = self._build_fingerprint()
        return f"guest_ai:{feature}:{fingerprint}"

    def allow(self, feature: str) -> bool:
        """
        Returns True if request should proceed, False if throttled.
        """
        if self.is_authenticated():
            return True

        limit = self.LIMITS.get(feature)
        if limit is None:
            return True

        cache_key = self._cache_key(feature)
        count = cache.get(cache_key)

        if count is None:
            cache.set(cache_key, 1, timeout=self.WINDOW)
            return True

        if count >= limit:
            return False

        try:
            cache.incr(cache_key)
        except ValueError:
            # Key expired between get and incr, reset count
            cache.set(cache_key, 1, timeout=self.WINDOW)
        return True


class GuestThrottle(BaseThrottle):
    """
    DRF throttle class for limiting guest users to 1 call per 24 hours for enhance-summary.
    Uses IP + User-Agent (or guest_id cookie if exists) to identify guests.
    Authenticated users are unlimited.
    """
    
    WINDOW = 24 * 60 * 60  # 24 hours
    LIMIT = 1  # 1 call per 24 hours for enhance-summary
    
    def get_ident(self, request):
        """
        Identify the user making the request.
        Returns user_id if authenticated, otherwise a fingerprint based on IP + User-Agent or guest_id.
        """
        user_id = get_supabase_user_id(request)
        if user_id:
            return f"user:{user_id}"
        
        # Try to get guest_id from cookie or query params
        guest_id = (
            request.COOKIES.get('guest_id')
            or request.query_params.get('guest_id')
            or (hasattr(request, 'data') and request.data.get('guest_id'))
        )
        
        if guest_id:
            raw = f"guest:{guest_id}"
        else:
            # Fallback to IP + User-Agent
            ip = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', 'unknown')
            )
            user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
            raw = f"{ip}:{user_agent}"
        
        # Create a stable hash for the fingerprint
        return salted_hmac('guest_ai_fingerprint', raw).hexdigest()
    
    def get_cache_key(self, request, view):
        """
        Generate a cache key for this request.
        """
        ident = self.get_ident(request)
        # Only throttle guests, not authenticated users
        if ident.startswith('user:'):
            return None  # No throttling for authenticated users
        return f"guest_enhance_summary:{ident}"
    
    def allow_request(self, request, view):
        """
        Check if the request should be throttled.
        Returns True if request should proceed, raises Throttled if throttled.
        """
        cache_key = self.get_cache_key(request, view)
        
        # No throttling for authenticated users
        if cache_key is None:
            return True
        
        # Check current count
        count = cache.get(cache_key)
        
        if count is None:
            # First request - set initial count
            cache.set(cache_key, 1, timeout=self.WINDOW)
            return True
        
        # Check if limit exceeded
        if count >= self.LIMIT:
            raise Throttled(
                detail="Guests limited to one AI summary enhancement. Sign up for unlimited.",
                wait=self.WINDOW
            )
        
        # Increment count
        try:
            cache.incr(cache_key)
        except ValueError:
            # Key expired between get and incr, reset count
            cache.set(cache_key, 1, timeout=self.WINDOW)
        
        return True
    
    def wait(self):
        """
        Return the number of seconds to wait before retrying.
        For 24-hour window, return remaining time.
        """
        # This is called when throttled, but we don't have access to the request here
        # Return a reasonable wait time (24 hours in seconds)
        return self.WINDOW




