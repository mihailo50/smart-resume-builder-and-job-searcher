"""
Serializers for resume draft endpoints.
"""
from rest_framework import serializers
from typing import Dict, Any


class ResumeDraftSerializer(serializers.Serializer):
    """Serializer for resume draft operations."""
    guest_id = serializers.UUIDField(read_only=True)
    data = serializers.JSONField(required=False, allow_null=True)
    owner = serializers.UUIDField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)


class ResumeDraftCreateSerializer(serializers.Serializer):
    """Serializer for creating a new resume draft."""
    guest_id = serializers.UUIDField(required=False)  # Optional, will be generated if not provided
    data = serializers.JSONField(required=False, default=dict)


class ResumeDraftUpdateSerializer(serializers.Serializer):
    """Serializer for updating resume draft data (incremental save)."""
    data = serializers.JSONField(required=True)


class ResumeDraftConvertSerializer(serializers.Serializer):
    """Serializer for converting draft to real resume.
    
    On conversion, the draft's owner is set to the authenticated user,
    and all draft data is converted to real Resume/Experience/Education/Skill models.
    """
    resume_id = serializers.UUIDField(read_only=True)
    message = serializers.CharField(read_only=True)




