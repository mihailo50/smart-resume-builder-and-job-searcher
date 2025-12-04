"""
Serializers for AI service endpoints.
"""
from rest_framework import serializers
from typing import Optional, List, Dict, Any


class ResumeAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for resume analysis request."""
    resume_id = serializers.UUIDField(required=False, allow_null=True)
    resume_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    job_desc = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Job description for targeted keyword analysis")
    
    def validate(self, attrs):
        """Validate that either resume_id or resume_text is provided."""
        resume_id = attrs.get('resume_id')
        resume_text = attrs.get('resume_text')
        
        if not resume_id and not resume_text:
            raise serializers.ValidationError(
                "Either 'resume_id' or 'resume_text' must be provided."
            )
        
        return attrs


class SuggestionSerializer(serializers.Serializer):
    """Serializer for AI suggestions."""
    type = serializers.CharField()
    text = serializers.CharField()
    priority = serializers.CharField()


class ResumeAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for resume analysis response."""
    ats_score = serializers.IntegerField(min_value=0, max_value=100)
    missing_keywords = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    suggestions = SuggestionSerializer(many=True)
    readability_score = serializers.IntegerField(min_value=0, max_value=100)
    bullet_strength = serializers.IntegerField(min_value=0, max_value=100)
    quantifiable_achievements = serializers.IntegerField(min_value=0, max_value=100)
    keyword_score = serializers.IntegerField(min_value=0, max_value=100, required=False)
    formatting_score = serializers.IntegerField(min_value=0, max_value=100, required=False)
    detailed_analysis = serializers.DictField(required=False)


class SummaryGenerationRequestSerializer(serializers.Serializer):
    """Serializer for summary generation request."""
    resume_id = serializers.UUIDField(required=False, allow_null=True)
    tone = serializers.ChoiceField(
        choices=['professional', 'confident', 'friendly', 'enthusiastic'],
        default='professional',
        required=False
    )
    existing_summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class SummaryGenerationResponseSerializer(serializers.Serializer):
    """Serializer for summary generation response."""
    summary = serializers.CharField(max_length=500)
    tone = serializers.CharField()


class JobMatchRequestSerializer(serializers.Serializer):
    """Serializer for job matching request."""
    resume_id = serializers.UUIDField(required=False, allow_null=True)
    job_description = serializers.CharField(required=True)
    resume_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate(self, attrs):
        """Validate that either resume_id or resume_text is provided."""
        resume_id = attrs.get('resume_id')
        resume_text = attrs.get('resume_text')
        
        if not resume_id and not resume_text:
            raise serializers.ValidationError(
                "Either 'resume_id' or 'resume_text' must be provided."
            )
        
        return attrs


class CategoryMatchSerializer(serializers.Serializer):
    """Serializer for category match scores."""
    technical_skills = serializers.FloatField(required=False, allow_null=True)
    tools = serializers.FloatField(required=False, allow_null=True)
    methodologies = serializers.FloatField(required=False, allow_null=True)
    soft_skills = serializers.FloatField(required=False, allow_null=True)


class JobMatchResponseSerializer(serializers.Serializer):
    """Serializer for job matching response."""
    match_score = serializers.IntegerField(min_value=0, max_value=100)
    missing_keywords = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    matched_keywords = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    category_matches = CategoryMatchSerializer(required=False)
    resume_keyword_count = serializers.IntegerField(required=False)
    job_keyword_count = serializers.IntegerField(required=False)
    keyword_overlap = serializers.IntegerField(required=False)
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )







