"""
Serializers for user-related endpoints.
"""
from rest_framework import serializers


class UserProfileSerializer(serializers.Serializer):
    """Serializer for user profile."""
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    avatar = serializers.URLField(read_only=True, allow_null=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    github_url = serializers.URLField(required=False, allow_blank=True)
    portfolio_url = serializers.URLField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserSerializer(serializers.Serializer):
    """Serializer for current user."""
    id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_authenticated = serializers.BooleanField(read_only=True)
    profile = UserProfileSerializer(read_only=True, allow_null=True)








