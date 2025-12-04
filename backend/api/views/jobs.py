"""
Job search and matching API views.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema
from config.services.job_search_service import AdzunaJobSearchService
from config.services.location_service import LocationService
from config.ai.services.job_matcher import JobMatcherService
from config.services.resume_service import ResumeService
from api.auth.utils import get_supabase_user_id
from api.serializers.jobs import (
    JobSearchRequestSerializer,
    JobSearchResponseSerializer,
    JobMatchAllRequestSerializer,
    JobMatchAllResponseSerializer,
    MatchResultSerializer,
)

logger = logging.getLogger(__name__)


class JobViewSet(viewsets.ViewSet):
    """
    API endpoints for job search and matching.
    """
    permission_classes = [IsAuthenticated]  # Job matching requires auth
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_search_service = AdzunaJobSearchService()
        self.location_service = LocationService()
        self.job_matcher = JobMatcherService()
        self.resume_service = ResumeService()
    
    @extend_schema(
        operation_id='search_jobs',
        request=JobSearchRequestSerializer,
        responses={200: JobSearchResponseSerializer},
        tags=['Jobs']
    )
    @action(detail=False, methods=['post'], url_path='search', permission_classes=[AllowAny])
    def search(self, request):
        """
        Search for jobs using external API (Adzuna).
        
        POST /api/v1/jobs/search/
        
        Body:
        {
            "query": "software engineer",
            "location": "New York, NY",
            "country": "US",
            "job_type": "full-time",
            "remote": false,
            "max_results": 20,
            "page": 1
        }
        
        Returns:
        {
            "success": true,
            "results": [...],
            "count": 20,
            "total_results": 100,
            "page": 1,
            "total_pages": 5,
            "source": "adzuna"
        }
        """
        serializer = JobSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data.get('query', '')
        location = serializer.validated_data.get('location')
        country = serializer.validated_data.get('country', 'US')
        job_type = serializer.validated_data.get('job_type')
        remote = serializer.validated_data.get('remote', False)
        max_results = serializer.validated_data.get('max_results', 20)
        page = serializer.validated_data.get('page', 1)
        
        try:
            search_results = self.job_search_service.search_jobs(
                query=query,
                location=location,
                country=country,
                job_type=job_type,
                remote=remote,
                max_results=max_results,
                page=page
            )
            
            response_serializer = JobSearchResponseSerializer(search_results)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error searching jobs")
            return Response(
                {'error': f'Failed to search jobs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='match_all_resumes',
        request=JobMatchAllRequestSerializer,
        responses={200: JobMatchAllResponseSerializer},
        tags=['Jobs']
    )
    @action(detail=False, methods=['post'], url_path='match-all')
    def match_all(self, request):
        """
        Match all user's resumes against a job description.
        
        POST /api/v1/jobs/match-all/
        
        Body:
        {
            "job_description": "We are looking for a software engineer...",
            "location": "New York, NY" (optional)
        }
        
        Returns:
        {
            "results": [
                {
                    "resume_id": "uuid",
                    "resume_name": "Software Engineer Resume",
                    "match_score": 85,
                    "missing_keywords": ["AWS", "Docker"],
                    "matched_keywords": ["Python", "React"],
                    "suggestions": [...],
                    "category_matches": {...}
                },
                ...
            ],
            "count": 3
        }
        """
        serializer = JobMatchAllRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Format validation errors to be more user-friendly
            errors = {}
            for field, messages in serializer.errors.items():
                if field == 'job_description':
                    # Provide helpful message for job_description errors
                    if isinstance(messages, list):
                        # Join multiple error messages
                        errors[field] = ' '.join(messages)
                    else:
                        errors[field] = str(messages)
                else:
                    errors[field] = messages if isinstance(messages, str) else messages[0] if messages else 'Invalid value'
            
            return Response(
                {
                    'error': 'Validation failed',
                    'errors': errors,
                    'message': 'Please check your input and try again. The job description should be at least 30 characters long.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = get_supabase_user_id(request)
        if not user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        job_description = serializer.validated_data.get('job_description', '')
        if not job_description or not job_description.strip():
            return Response(
                {
                    'error': 'Job description is required',
                    'message': 'Please provide the job posting text. It should be at least 30 characters long and include details about the role, requirements, and responsibilities.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all user's resumes
        try:
            resumes = self.resume_service.get_user_resumes(user_id)
            
            if not resumes:
                return Response(
                    {
                        'results': [],
                        'count': 0,
                        'message': 'No resumes found. Create a resume first.'
                    },
                    status=status.HTTP_200_OK
                )
            
            # Match each resume against job description
            match_results = []
            
            for resume in resumes:
                resume_id = resume.get('id')
                resume_title = resume.get('title', 'Untitled Resume')
                
                # Get full resume data
                resume_data = self.resume_service.get_resume_with_details(resume_id)
                
                # Match resume with job description
                match_result = self.job_matcher.match(
                    resume_data=resume_data or {},
                    job_description=job_description
                )
                
                # Add resume metadata to match result
                match_result['resume_id'] = str(resume_id)
                match_result['resume_name'] = resume_title
                
                match_results.append(match_result)
            
            # Sort by match score (highest first)
            match_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            
            response_data = {
                'results': match_results,
                'count': len(match_results),
                'job_description': job_description[:200] + '...' if len(job_description) > 200 else job_description
            }
            
            response_serializer = JobMatchAllResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error matching resumes")
            return Response(
                {'error': f'Failed to match resumes: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='detect_location',
        responses={200: {'type': 'object'}},
        tags=['Jobs']
    )
    @action(detail=False, methods=['get'], url_path='detect-location', permission_classes=[AllowAny])
    def detect_location(self, request):
        """
        Detect user location from IP address.
        
        GET /api/v1/jobs/detect-location/
        
        Query params:
        - ip: Optional IP address (if not provided, uses request IP)
        - latitude: Optional latitude (for reverse geocoding)
        - longitude: Optional longitude (for reverse geocoding)
        
        Returns:
        {
            "success": true,
            "city": "New York",
            "country": "United States",
            "country_code": "US",
            "region": "New York",
            "location_string": "New York, NY, US",
            "source": "ipapi.co"
        }
        """
        # Check if coordinates provided (browser geolocation)
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        
        if latitude and longitude:
            try:
                lat = float(latitude)
                lon = float(longitude)
                
                # Reverse geocode coordinates
                location = self.location_service.reverse_geocode(lat, lon)
                
                if location.get('success'):
                    location['location_string'] = self.location_service.normalize_location_string(location)
                    return Response(location, status=status.HTTP_200_OK)
            
            except (ValueError, TypeError):
                pass
        
        # Get IP address
        ip_address = request.query_params.get('ip')
        if not ip_address:
            ip_address = self.location_service.get_client_ip(request)
        
        # Get location from IP
        location = self.location_service.get_location_from_ip(ip_address)
        
        if location.get('success'):
            location['location_string'] = self.location_service.normalize_location_string(location)
        
        return Response(location, status=status.HTTP_200_OK)

