"""
Supabase client initialization and configuration.
"""
import os
from supabase import create_client, Client
from django.conf import settings


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    
    Returns:
        Client: Supabase client instance
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    
    if not url or not key:
        raise ValueError(
            "Supabase URL and key must be set in environment variables. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY"
        )
    
    return create_client(url, key)


def get_supabase_anon_client() -> Client:
    """
    Get Supabase client with anon key (for client-side operations).
    
    Returns:
        Client: Supabase client instance with anon key
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_ANON_KEY
    
    if not url or not key:
        raise ValueError(
            "Supabase URL and ANON_KEY must be set in environment variables."
        )
    
    return create_client(url, key)


# Global client instance (singleton pattern)
_supabase_client: Client = None


def supabase() -> Client:
    """
    Get global Supabase client instance (singleton).
    
    Returns:
        Client: Supabase client instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client









