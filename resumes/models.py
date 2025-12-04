from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid
import os


class UserProfile(models.Model):
    """Extended user profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        ordering = ['-created_at']


class Resume(models.Model):
    """Main resume model"""
    RESUME_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)  # Used as professional tagline (<=300 chars)
    optimized_summary = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=RESUME_STATUS_CHOICES, default='draft')
    raw_text = models.TextField(blank=True)  # Parsed text from uploaded file
    file = models.FileField(
        upload_to='resumes/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    last_template = models.CharField(max_length=50, default='modern-indigo')
    last_font = models.CharField(max_length=20, default='modern')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ['-updated_at']


class ResumeDraft(models.Model):
    """Temporary resume draft for guest users before signup.
    
    Stores all resume data in a JSONField for simplicity.
    On signup, the draft is converted to a real Resume with all related data.
    The owner field is set when the user signs up and converts the draft.
    """
    guest_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    data = models.JSONField(default=dict, blank=True)
    owner = models.UUIDField(null=True, blank=True, help_text="Supabase user_id - set when draft is converted")
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft {self.guest_id}"

    class Meta:
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['guest_id']),
            models.Index(fields=['owner']),
            models.Index(fields=['-last_updated']),
        ]


class Education(models.Model):
    """Education entry for resume"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.degree} at {self.institution}"

    class Meta:
        ordering = ['order', '-end_date']


class Experience(models.Model):
    """Work experience entry for resume"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.position} at {self.company}"

    class Meta:
        ordering = ['order', '-end_date']


class Skill(models.Model):
    """Skill entry for resume"""
    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)  # e.g., "Programming", "Soft Skills"
    level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']


class Project(models.Model):
    """Project entry for resume"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    technologies = models.CharField(max_length=500, blank=True)  # Comma-separated
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', '-end_date']


class Certification(models.Model):
    """Certification entry for resume"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=200, blank=True)
    credential_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} from {self.issuer}"

    class Meta:
        ordering = ['order', '-issue_date']


class Language(models.Model):
    """Language entry for resume"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=100)
    level = models.CharField(
        max_length=10,
        choices=[
            ('A1', 'A1 - Beginner'),
            ('A2', 'A2 - Elementary'),
            ('B1', 'B1 - Intermediate'),
            ('B2', 'B2 - Upper Intermediate'),
            ('C1', 'C1 - Advanced'),
            ('C2', 'C2 - Proficient'),
            ('Native', 'Native'),
        ],
        blank=True
    )
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.level})"

    class Meta:
        ordering = ['order', 'name']


class Interest(models.Model):
    """Interest entry for resume"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='interests')
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
