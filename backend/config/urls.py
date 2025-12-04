"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# API Router
router = DefaultRouter()

# Import viewsets
from api.views.auth import AuthViewSet
from api.views.resumes import ResumeViewSet
from api.views.experiences import ExperienceViewSet
from api.views.projects import ProjectViewSet
from api.views.educations import EducationViewSet
from api.views.certifications import CertificationViewSet
from api.views.skills import SkillViewSet
from api.views.languages import LanguageViewSet
from api.views.interests import InterestViewSet
from api.views.ai import AIViewSet
from api.views.files import FileViewSet
from api.views.templates import TemplateViewSet
from api.views.jobs import JobViewSet
from api.views.dashboard import DashboardViewSet
from api.views.drafts import ResumeDraftViewSet

# Register API viewsets
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'resumes', ResumeViewSet, basename='resume')
router.register(r'resume-drafts', ResumeDraftViewSet, basename='resume-draft')
router.register(r'ai', AIViewSet, basename='ai')
router.register(r'files', FileViewSet, basename='files')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Nested routes for experiences, educations, and skills
# These will be handled via nested URL patterns below

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 Routes
    path('api/v1/', include(router.urls)),
    
    # Nested routes for experiences, educations, and skills
    path('api/v1/resumes/<uuid:resume_id>/experiences/', 
         ExperienceViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-experiences-list'),
    path('api/v1/resumes/<uuid:resume_id>/experiences/reorder/', 
         ExperienceViewSet.as_view({'patch': 'reorder'}),
         name='resume-experiences-reorder'),
    path('api/v1/resumes/<uuid:resume_id>/experiences/<uuid:pk>/', 
         ExperienceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-experiences-detail'),
    
    path('api/v1/resumes/<uuid:resume_id>/projects/', 
         ProjectViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-projects-list'),
    path('api/v1/resumes/<uuid:resume_id>/projects/reorder/', 
         ProjectViewSet.as_view({'patch': 'reorder'}),
         name='resume-projects-reorder'),
    path('api/v1/resumes/<uuid:resume_id>/projects/<uuid:pk>/', 
         ProjectViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-projects-detail'),
    
    path('api/v1/resumes/<uuid:resume_id>/educations/', 
         EducationViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-educations-list'),
    path('api/v1/resumes/<uuid:resume_id>/educations/reorder/', 
         EducationViewSet.as_view({'patch': 'reorder'}),
         name='resume-educations-reorder'),
    path('api/v1/resumes/<uuid:resume_id>/educations/<uuid:pk>/', 
         EducationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-educations-detail'),
    
    path('api/v1/resumes/<uuid:resume_id>/certifications/', 
         CertificationViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-certifications-list'),
    path('api/v1/resumes/<uuid:resume_id>/certifications/reorder/', 
         CertificationViewSet.as_view({'patch': 'reorder'}),
         name='resume-certifications-reorder'),
    path('api/v1/resumes/<uuid:resume_id>/certifications/<uuid:pk>/', 
         CertificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-certifications-detail'),
    
    path('api/v1/resumes/<uuid:resume_id>/skills/', 
         SkillViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-skills-list'),
    path('api/v1/resumes/<uuid:resume_id>/skills/<uuid:pk>/', 
         SkillViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-skills-detail'),
    
    path('api/v1/resumes/<uuid:resume_id>/languages/', 
         LanguageViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-languages-list'),
    path('api/v1/resumes/<uuid:resume_id>/languages/reorder/', 
         LanguageViewSet.as_view({'patch': 'reorder'}),
         name='resume-languages-reorder'),
    path('api/v1/resumes/<uuid:resume_id>/languages/<uuid:pk>/', 
         LanguageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-languages-detail'),
    
    path('api/v1/resumes/<uuid:resume_id>/interests/', 
         InterestViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='resume-interests-list'),
    path('api/v1/resumes/<uuid:resume_id>/interests/reorder/', 
         InterestViewSet.as_view({'patch': 'reorder'}),
         name='resume-interests-reorder'),
    path('api/v1/resumes/<uuid:resume_id>/interests/<uuid:pk>/', 
         InterestViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='resume-interests-detail'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
