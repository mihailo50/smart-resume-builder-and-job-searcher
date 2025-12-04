from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator


class JobPosting(models.Model):
    """Job posting model"""
    JOB_TYPE_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]

    REMOTE_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    remote_type = models.CharField(max_length=20, choices=REMOTE_TYPE_CHOICES, default='onsite')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full-time')
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    application_url = models.URLField(blank=True)
    company_url = models.URLField(blank=True)
    posted_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Vector search fields
    embedding = models.JSONField(null=True, blank=True)  # Store vector embedding for similarity search
    pinecone_id = models.CharField(max_length=200, blank=True)  # Pinecone vector ID
    
    # Metadata
    source = models.CharField(max_length=200, blank=True)  # Where the job was scraped from
    external_id = models.CharField(max_length=200, blank=True)  # External system ID
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-posted_date', '-created_at']
        indexes = [
            models.Index(fields=['is_active', '-posted_date']),
            models.Index(fields=['company']),
            models.Index(fields=['job_type']),
        ]


class Application(models.Model):
    """Job application model"""
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('viewed', 'Viewed'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer Received'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey('resumes.Resume', on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    cover_letter = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    applied_date = models.DateTimeField(null=True, blank=True)
    match_score = models.FloatField(null=True, blank=True)  # AI-generated match score
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.job_posting.title}"

    class Meta:
        ordering = ['-applied_date', '-created_at']
        unique_together = ['user', 'job_posting']


class SavedJob(models.Model):
    """Saved jobs for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='saved_by')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} saved {self.job_posting.title}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'job_posting']


class JobSearch(models.Model):
    """Saved job searches with criteria"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_searches')
    name = models.CharField(max_length=200)
    query = models.CharField(max_length=500, blank=True)  # Search query keywords
    location = models.CharField(max_length=200, blank=True)
    job_type = models.CharField(max_length=20, choices=JobPosting.JOB_TYPE_CHOICES, blank=True)
    remote_type = models.CharField(max_length=20, choices=JobPosting.REMOTE_TYPE_CHOICES, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notify_new_jobs = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_searched_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    class Meta:
        ordering = ['-updated_at']
