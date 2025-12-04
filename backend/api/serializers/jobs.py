"""
Serializers for job search and matching endpoints.
"""
from rest_framework import serializers
from typing import Optional, List, Dict, Any


class JobSearchRequestSerializer(serializers.Serializer):
    """Serializer for job search request."""
    query = serializers.CharField(required=True, max_length=500)
    location = serializers.CharField(required=False, allow_blank=True, max_length=200)
    country = serializers.CharField(required=False, default='US', max_length=2)
    job_type = serializers.ChoiceField(
        choices=['full-time', 'part-time', 'contract', 'internship', 'freelance'],
        required=False,
        allow_null=True
    )
    remote = serializers.BooleanField(required=False, default=False)
    max_results = serializers.IntegerField(required=False, default=20, min_value=1, max_value=50)
    page = serializers.IntegerField(required=False, default=1, min_value=1)


class JobSearchResultSerializer(serializers.Serializer):
    """Serializer for job search result."""
    external_id = serializers.CharField()
    title = serializers.CharField()
    company = serializers.CharField()
    location = serializers.CharField()
    remote_type = serializers.CharField()
    job_type = serializers.CharField()
    description = serializers.CharField()
    requirements = serializers.CharField(required=False, allow_blank=True)
    salary_min = serializers.FloatField(required=False, allow_null=True)
    salary_max = serializers.FloatField(required=False, allow_null=True)
    currency = serializers.CharField(default='USD')
    application_url = serializers.URLField(required=False, allow_blank=True)
    company_url = serializers.URLField(required=False, allow_blank=True)
    posted_date = serializers.DateField(required=False, allow_null=True)
    source = serializers.CharField()
    source_id = serializers.CharField()
    category = serializers.CharField(required=False, allow_blank=True)


class JobSearchResponseSerializer(serializers.Serializer):
    """Serializer for job search response."""
    success = serializers.BooleanField()
    results = JobSearchResultSerializer(many=True)
    count = serializers.IntegerField()
    total_results = serializers.IntegerField(required=False)
    page = serializers.IntegerField(required=False)
    total_pages = serializers.IntegerField(required=False)
    source = serializers.CharField(required=False)
    error = serializers.CharField(required=False, allow_blank=True)


class JobMatchAllRequestSerializer(serializers.Serializer):
    """Serializer for matching all resumes against job description."""
    job_description = serializers.CharField(
        required=True, 
        min_length=30,
        error_messages={
            'required': 'Job description is required. Please provide the job posting text.',
            'min_length': 'Job description must be at least 30 characters long. Please provide a more detailed job description for better matching results.'
        }
    )
    location = serializers.CharField(required=False, allow_blank=True, max_length=200)
    
    def validate_job_description(self, value):
        """Custom validation for job description."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                'Job description cannot be empty. Please paste the full job posting text.'
            )
        
        # Check if it's just whitespace
        if len(value.strip()) < 30:
            raise serializers.ValidationError(
                f'Job description is too short ({len(value.strip())} characters). Please provide at least 30 characters of the job posting for accurate matching. Include details like required skills, responsibilities, and qualifications.'
            )
        
        return value.strip()


class CategoryMatchSerializer(serializers.Serializer):
    """Serializer for category match scores."""
    technical_skills = serializers.FloatField(required=False, allow_null=True)
    tools = serializers.FloatField(required=False, allow_null=True)
    methodologies = serializers.FloatField(required=False, allow_null=True)
    soft_skills = serializers.FloatField(required=False, allow_null=True)


class MatchResultSerializer(serializers.Serializer):
    """Serializer for match result."""
    resume_id = serializers.UUIDField()
    resume_name = serializers.CharField()
    match_score = serializers.IntegerField(min_value=0, max_value=100)
    missing_keywords = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    matched_keywords = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    category_matches = CategoryMatchSerializer(required=False, allow_null=True)
    resume_keyword_count = serializers.IntegerField(required=False)
    job_keyword_count = serializers.IntegerField(required=False)
    keyword_overlap = serializers.IntegerField(required=False)
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )


class JobMatchAllResponseSerializer(serializers.Serializer):
    """Serializer for matching all resumes response."""
    results = MatchResultSerializer(many=True)
    count = serializers.IntegerField()
    job_description = serializers.CharField(required=False)
    message = serializers.CharField(required=False, allow_blank=True)

