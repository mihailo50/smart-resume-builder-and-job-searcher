"""
Serializers for resume and related data.
"""
from rest_framework import serializers
from typing import Optional, List, Dict, Any


# Base serializers for resume sections
class ExperienceSerializer(serializers.Serializer):
    """Serializer for experience entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    position = serializers.CharField(max_length=200, required=True)
    company = serializers.CharField(max_length=200, required=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_current = serializers.BooleanField(default=False)
    description = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)


class EducationSerializer(serializers.Serializer):
    """Serializer for education entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    degree = serializers.CharField(max_length=200, required=True)
    field_of_study = serializers.CharField(max_length=200, required=False, allow_blank=True)
    institution = serializers.CharField(max_length=200, required=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_current = serializers.BooleanField(default=False)
    description = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)


class ProjectSerializer(serializers.Serializer):
    """Serializer for project entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=200, required=True)  # Matches DB column
    name = serializers.CharField(source='title', read_only=True)  # Frontend alias
    technologies = serializers.CharField(max_length=500, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure 'name' is present for frontend compatibility, mapping from 'title'
        if 'title' in ret and 'name' not in ret:
            ret['name'] = ret['title']
        return ret

    def to_internal_value(self, data):
        # Map 'name' from frontend to 'title' for backend if 'title' is not provided
        if 'name' in data and 'title' not in data:
            data['title'] = data.pop('name')
        return super().to_internal_value(data)


class CertificationSerializer(serializers.Serializer):
    """Serializer for certification entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200, required=True)  # Matches DB column
    title = serializers.CharField(source='name', read_only=True)  # Frontend alias
    issuer = serializers.CharField(max_length=200, required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    expiration_date = serializers.DateField(source='expiry_date', required=False, allow_null=True)  # Frontend alias
    credential_id = serializers.CharField(max_length=200, required=False, allow_blank=True)
    credential_url = serializers.URLField(required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure 'title' is present for frontend compatibility, mapping from 'name'
        if 'name' in ret and 'title' not in ret:
            ret['title'] = ret['name']
        # Map expiry_date to expiration_date for frontend
        if 'expiry_date' in ret and 'expiration_date' not in ret:
            ret['expiration_date'] = ret.get('expiry_date')
        return ret

    def to_internal_value(self, data):
        # Map 'title' from frontend to 'name' for backend if 'name' is not provided
        if 'title' in data and 'name' not in data:
            data = data.copy()  # Don't modify the original
            data['name'] = data.pop('title')
        # Map 'expiration_date' from frontend to 'expiry_date' for backend
        if 'expiration_date' in data and 'expiry_date' not in data:
            data = data.copy() if not isinstance(data, dict) else data
            data['expiry_date'] = data.pop('expiration_date')
        return super().to_internal_value(data)


class SkillSerializer(serializers.Serializer):
    """Serializer for skill entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200, required=True)
    level = serializers.CharField(max_length=50, required=False, allow_blank=True)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)


class LanguageSerializer(serializers.Serializer):
    """Serializer for language entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100, required=True)
    proficiency = serializers.CharField(max_length=50, required=False, allow_blank=True)
    level = serializers.CharField(source='proficiency', read_only=True)  # Alias for frontend
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure 'level' is present if 'proficiency' exists
        if 'proficiency' in ret and 'level' not in ret:
            ret['level'] = ret['proficiency']
        return ret


class InterestSerializer(serializers.Serializer):
    """Serializer for interest entries."""
    id = serializers.UUIDField(read_only=True)
    resume_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200, required=True)
    order = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)


# Resume serializers
class ResumeSerializer(serializers.Serializer):
    """Base serializer for resume data."""
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    optimized_summary = serializers.CharField(required=False, allow_blank=True)
    professional_tagline = serializers.CharField(required=False, allow_blank=True)
    last_template = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_font = serializers.CharField(max_length=50, required=False, allow_blank=True)
    status = serializers.CharField(max_length=50, default='draft')
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ResumeCreateSerializer(serializers.Serializer):
    """Serializer for creating a new resume."""
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    professional_tagline = serializers.CharField(required=False, allow_blank=True)
    last_template = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_font = serializers.CharField(max_length=50, required=False, allow_blank=True)


class ResumeListSerializer(serializers.Serializer):
    """Serializer for listing resumes (minimal data)."""
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    professional_tagline = serializers.CharField(source='summary', read_only=True)
    status = serializers.CharField(read_only=True)
    last_template = serializers.CharField(read_only=True)
    last_font = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ResumeDetailSerializer(serializers.Serializer):
    """Serializer for detailed resume view."""
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    professional_tagline = serializers.CharField(read_only=True, required=False, allow_null=True)
    summary = serializers.CharField(read_only=True)
    optimized_summary = serializers.CharField(read_only=True)
    last_template = serializers.CharField(read_only=True)
    last_font = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    # Contact info
    full_name = serializers.CharField(read_only=True, required=False)
    email = serializers.EmailField(read_only=True, required=False)
    phone = serializers.CharField(read_only=True, required=False)
    location = serializers.CharField(read_only=True, required=False)
    date_of_birth = serializers.DateField(read_only=True, required=False, allow_null=True)
    linkedin_url = serializers.URLField(read_only=True, required=False)
    github_url = serializers.URLField(read_only=True, required=False)
    portfolio_url = serializers.URLField(read_only=True, required=False)
    avatar_url = serializers.URLField(read_only=True, required=False, allow_null=True)
    # Sections
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    interests = InterestSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class PersonalInfoSerializer(serializers.Serializer):
    """Serializer for personal information."""
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    github_url = serializers.URLField(required=False, allow_blank=True)
    portfolio_url = serializers.URLField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)


class ProfessionalTaglineSerializer(serializers.Serializer):
    """Serializer for professional tagline."""
    professional_tagline = serializers.CharField(required=True)


class OptimizedSummarySerializer(serializers.Serializer):
    """Serializer for optimized summary."""
    optimized_summary = serializers.CharField(required=True)


class ReorderSerializer(serializers.Serializer):
    """Serializer for reordering items."""
    items = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )


class ResumeMetadataSerializer(serializers.Serializer):
    """Serializer for resume metadata."""
    last_template = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_font = serializers.CharField(max_length=50, required=False, allow_blank=True)
    status = serializers.CharField(max_length=50, required=False)
