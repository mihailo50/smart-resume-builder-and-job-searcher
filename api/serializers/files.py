"""
Serializers for file processing endpoints.
"""
from rest_framework import serializers
from typing import Optional


class ResumeUploadSerializer(serializers.Serializer):
    """Serializer for resume file upload."""
    file = serializers.FileField(required=True, help_text="Resume file (PDF or DOCX)")
    resume_id = serializers.UUIDField(required=False, allow_null=True, help_text="Optional resume ID to update existing resume")


class ResumeUploadResponseSerializer(serializers.Serializer):
    """Serializer for resume upload response."""
    resume_id = serializers.UUIDField(help_text="ID of the created or updated resume")
    text_extracted = serializers.CharField(help_text="Extracted text from the resume")
    structured_data = serializers.DictField(help_text="Extracted structured data (if available)")
    file_url = serializers.URLField(help_text="URL of the uploaded file")
    metadata = serializers.DictField(help_text="File metadata")


class ResumeExportRequestSerializer(serializers.Serializer):
    """Serializer for resume export request."""
    format = serializers.ChoiceField(
        choices=['pdf', 'docx'],
        default='pdf',
        help_text="Export format (pdf or docx)"
    )
    template = serializers.ChoiceField(
        choices=[
            'modern-indigo', 'minimalist-black', 'creative-violet', 'executive-gold',
            'tech-cyan', 'sidebar-teal', 'ats-classic', 'elegant-emerald'
        ],
        required=False,
        allow_null=True,
        help_text="Template name for styled export"
    )
    font = serializers.ChoiceField(
        choices=['modern', 'classic', 'creative'],
        required=False,
        allow_null=True,
        help_text="Font combination (modern, classic, creative)"
    )
    ats_mode = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Generate ATS-friendly version (no columns/graphics)"
    )
    photo_url = serializers.URLField(
        required=False,
        allow_null=True,
        help_text="URL to user's photo image (optional)"
    )
    template_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional template ID (deprecated, use 'template' instead)"
    )


class ResumeExportResponseSerializer(serializers.Serializer):
    """Serializer for resume export response."""
    file_url = serializers.URLField(help_text="URL of the exported file")
    download_url = serializers.URLField(help_text="Direct download URL (signed)")
    expires_at = serializers.DateTimeField(help_text="URL expiration time")


class FileParseResponseSerializer(serializers.Serializer):
    """Serializer for file parsing response."""
    text = serializers.CharField(help_text="Extracted text")
    metadata = serializers.DictField(help_text="File metadata")
    format = serializers.CharField(help_text="File format (pdf or docx)")
    success = serializers.BooleanField(help_text="Whether parsing was successful")
    error = serializers.CharField(required=False, allow_null=True, help_text="Error message if parsing failed")

