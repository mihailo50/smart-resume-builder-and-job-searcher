"""
Views for resume draft operations (guest users).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from api.serializers.draft import (
    ResumeDraftSerializer,
    ResumeDraftCreateSerializer,
    ResumeDraftUpdateSerializer,
    ResumeDraftConvertSerializer
)
from resumes.models import ResumeDraft, Resume, Education, Experience, Skill
from api.auth.utils import get_supabase_user_id
from config.services.resume_service import (
    ResumeService,
    ExperienceService,
    ProjectService,
    EducationService,
    CertificationService,
    SkillService
)
import uuid
import json


class ResumeDraftViewSet(viewsets.ViewSet):
    """
    ViewSet for resume draft CRUD operations.
    Allows anonymous access for guest users.
    """
    permission_classes = [AllowAny]
    
    def _get_guest_id_from_request(self, request):
        """Extract guest_id from request (cookie or query param)."""
        # Try to get from query params first
        guest_id = request.query_params.get('guest_id')
        
        # If not in query, try to get from cookie
        if not guest_id:
            guest_id = request.COOKIES.get('guest_id')
        
        # If still not found, try from request data
        if not guest_id and hasattr(request, 'data') and 'guest_id' in request.data:
            guest_id = request.data.get('guest_id')
        
        return guest_id
    
    @extend_schema(
        operation_id='create_resume_draft',
        request=ResumeDraftCreateSerializer,
        responses={201: ResumeDraftSerializer},
        tags=['Resume Drafts']
    )
    def create(self, request):
        """
        Create a new resume draft for a guest user.
        
        POST /api/v1/resume-drafts/
        """
        serializer = ResumeDraftCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or generate guest_id
        guest_id = serializer.validated_data.get('guest_id')
        if not guest_id:
            # Try to get from cookie
            guest_id = request.COOKIES.get('guest_id')
            if not guest_id:
                # Generate new UUID
                guest_id = str(uuid.uuid4())
        
        # Convert to UUID if string
        if isinstance(guest_id, str):
            try:
                guest_id = uuid.UUID(guest_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid guest_id format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if draft already exists
        try:
            draft = ResumeDraft.objects.get(guest_id=guest_id)
            response_serializer = ResumeDraftSerializer({
                'guest_id': draft.guest_id,
                'data': draft.data,
                'created_at': draft.created_at,
                'last_updated': draft.last_updated,
            })
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ResumeDraft.DoesNotExist:
            pass
        
        # Create new draft
        draft_data = serializer.validated_data.get('data', {})
        draft = ResumeDraft.objects.create(
            guest_id=guest_id,
            data=draft_data
        )
        
        response_serializer = ResumeDraftSerializer({
            'guest_id': draft.guest_id,
            'data': draft.data,
            'created_at': draft.created_at,
            'last_updated': draft.last_updated,
        })
        
        response = Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        # Set guest_id cookie (secure, httpOnly, sameSite)
        response.set_cookie(
            'guest_id',
            str(guest_id),
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            samesite='Lax',
            secure=False  # Set to True in production with HTTPS
        )
        
        return response
    
    @extend_schema(
        operation_id='get_resume_draft',
        responses={200: ResumeDraftSerializer},
        tags=['Resume Drafts']
    )
    def retrieve(self, request, pk=None):
        """
        Get a resume draft by guest_id.
        
        GET /api/v1/resume-drafts/{guest_id}/
        """
        guest_id = pk or self._get_guest_id_from_request(request)
        
        if not guest_id:
            return Response(
                {'error': 'guest_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if isinstance(guest_id, str):
                guest_id = uuid.UUID(guest_id)
        except ValueError:
            return Response(
                {'error': 'Invalid guest_id format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            draft = ResumeDraft.objects.get(guest_id=guest_id)
            response_serializer = ResumeDraftSerializer({
                'guest_id': draft.guest_id,
                'data': draft.data,
                'owner': draft.owner,
                'created_at': draft.created_at,
                'last_updated': draft.last_updated,
            })
            return Response(response_serializer.data)
        except ResumeDraft.DoesNotExist:
            return Response(
                {'error': 'Draft not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        operation_id='update_resume_draft',
        request=ResumeDraftUpdateSerializer,
        responses={200: ResumeDraftSerializer},
        tags=['Resume Drafts']
    )
    def partial_update(self, request, pk=None):
        """
        Update resume draft data (incremental save).
        
        PATCH /api/v1/resume-drafts/{guest_id}/
        """
        guest_id = pk or self._get_guest_id_from_request(request)
        
        if not guest_id:
            return Response(
                {'error': 'guest_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if isinstance(guest_id, str):
                guest_id = uuid.UUID(guest_id)
        except ValueError:
            return Response(
                {'error': 'Invalid guest_id format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ResumeDraftUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            draft = ResumeDraft.objects.get(guest_id=guest_id)
            
            # Merge new data with existing data
            existing_data = draft.data or {}
            new_data = serializer.validated_data.get('data', {})
            
            # Deep merge: update nested objects
            merged_data = {**existing_data, **new_data}
            
            # Handle nested objects (personal, experiences, etc.)
            for key in ['personal', 'experiences', 'projects', 'educations', 'certifications', 'skills', 'metadata']:
                if key in new_data and isinstance(new_data[key], dict):
                    merged_data[key] = {**existing_data.get(key, {}), **new_data[key]}
                elif key in new_data and isinstance(new_data[key], list):
                    merged_data[key] = new_data[key]  # Replace arrays entirely
            
            draft.data = merged_data
            draft.save()
            
            response_serializer = ResumeDraftSerializer({
                'guest_id': draft.guest_id,
                'data': draft.data,
                'owner': draft.owner,
                'created_at': draft.created_at,
                'last_updated': draft.last_updated,
            })
            return Response(response_serializer.data)
        except ResumeDraft.DoesNotExist:
            return Response(
                {'error': 'Draft not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        operation_id='convert_resume_draft',
        request=None,
        responses={200: ResumeDraftConvertSerializer},
        tags=['Resume Drafts']
    )
    @action(detail=True, methods=['post'], url_path='convert')
    def convert(self, request, pk=None):
        """
        Convert a resume draft to a real Resume owned by the authenticated user.
        Assigns owner to the draft, converts all JSON data to real models, then deletes the draft.
        
        POST /api/v1/resume-drafts/{guest_id}/convert/
        """
        guest_id = pk or self._get_guest_id_from_request(request)
        
        if not guest_id:
            return Response(
                {'error': 'guest_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if isinstance(guest_id, str):
                guest_id = uuid.UUID(guest_id)
        except ValueError:
            return Response(
                {'error': 'Invalid guest_id format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get authenticated user
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User must be authenticated to convert draft'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            draft = ResumeDraft.objects.get(guest_id=guest_id)
        except ResumeDraft.DoesNotExist:
            return Response(
                {'error': 'Draft not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if draft already has an owner (already converted)
        if draft.owner:
            return Response(
                {'error': 'Draft has already been converted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assign owner to draft
        try:
            if isinstance(supabase_user_id, str):
                owner_uuid = uuid.UUID(supabase_user_id)
            else:
                owner_uuid = supabase_user_id
            draft.owner = owner_uuid
            draft.save()
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid user_id format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract data from draft
        draft_data = draft.data or {}
        personal = draft_data.get('personal', {})
        
        # Create real Resume
        service = ResumeService()
        resume_data = {
            'user_id': supabase_user_id,
            'title': personal.get('fullName') or 'My Resume',
            'optimized_summary': draft_data.get('optimizedSummary') or '',
        }
        
        # Filter out empty strings
        resume_data = {k: v for k, v in resume_data.items() if v}
        
        created_resume = service.create(resume_data)
        resume_id = created_resume.get('id')
        
        if not resume_id:
            # Rollback: remove owner assignment
            draft.owner = None
            draft.save()
            return Response(
                {'error': 'Failed to create resume'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Save personal info via update
            if personal:
                personal_payload = {
                    'full_name': personal.get('fullName'),
                    'email': personal.get('email'),
                    'phone': personal.get('phone'),
                    'location': personal.get('location'),
                    'linkedin_url': personal.get('linkedin'),
                    'github_url': personal.get('github'),
                    'portfolio_url': personal.get('portfolio'),
                }
                # Filter out null and empty strings
                personal_payload = {k: v for k, v in personal_payload.items() if v and v != ''}
                
                if personal_payload:
                    # Update resume title if full_name provided
                    if 'full_name' in personal_payload:
                        service.update(resume_id, {'title': personal_payload['full_name']})
                    
                    # Save to user profile
                    from config.services.user_service import UserProfileService
                    profile_service = UserProfileService()
                    profile_service.create_or_update_profile(
                        user_id=supabase_user_id,
                        phone_number=personal_payload.get('phone'),
                        linkedin_url=personal_payload.get('linkedin_url'),
                        github_url=personal_payload.get('github_url'),
                        portfolio_url=personal_payload.get('portfolio_url'),
                        location=personal_payload.get('location'),
                    )
            
            # Save experiences
            experience_service = ExperienceService()
            experiences = draft_data.get('experiences', [])
            for exp in experiences:
                if exp.get('company') and exp.get('position'):
                    exp_payload = {
                        'resume_id': resume_id,
                        'company': exp.get('company'),
                        'position': exp.get('position'),
                        'location': exp.get('location'),
                        'start_date': exp.get('startDate'),
                        'end_date': exp.get('endDate'),
                        'is_current': exp.get('isCurrent', False),
                        'description': exp.get('description'),
                        'order': exp.get('order', 0),
                    }
                    exp_payload = {k: v for k, v in exp_payload.items() if v != '' and v is not None}
                    if exp_payload:
                        experience_service.create(exp_payload)
            
            # Save educations
            education_service = EducationService()
            educations = draft_data.get('educations', [])
            for edu in educations:
                if edu.get('institution') and edu.get('degree'):
                    edu_payload = {
                        'resume_id': resume_id,
                        'institution': edu.get('institution'),
                        'degree': edu.get('degree'),
                        'field_of_study': edu.get('fieldOfStudy'),
                        'start_date': edu.get('startDate'),
                        'end_date': edu.get('endDate'),
                        'is_current': edu.get('isCurrent', False),
                        'description': edu.get('description'),
                        'order': edu.get('order', 0),
                    }
                    edu_payload = {k: v for k, v in edu_payload.items() if v != '' and v is not None}
                    if edu_payload:
                        education_service.create(edu_payload)
            
            # Save projects
            project_service = ProjectService()
            projects = draft_data.get('projects', [])
            for proj in projects:
                if not proj.get('title'):
                    continue
                project_data = {
                    'resume_id': resume_id,
                    'title': proj.get('title'),
                    'technologies': proj.get('technologies', ''),
                    'description': proj.get('description', ''),
                }
                if proj.get('startDate'):
                    project_data['start_date'] = proj.get('startDate')
                if proj.get('endDate'):
                    project_data['end_date'] = proj.get('endDate')
                if isinstance(proj.get('order'), int):
                    project_data['order'] = proj.get('order')
                # Filter out empty strings
                project_data = {k: v for k, v in project_data.items() if v != '' and v is not None}
                project_service.create(project_data)
            
            # Save certifications
            certification_service = CertificationService()
            certifications = draft_data.get('certifications', [])
            for cert in certifications:
                if not cert.get('title'):
                    continue
                cert_data = {
                    'resume_id': resume_id,
                    'name': cert.get('title'),  # Map title to name
                    'issuer': cert.get('issuer', ''),
                    'credential_id': cert.get('credentialId', ''),
                    'credential_url': cert.get('url', ''),
                }
                if cert.get('issueDate'):
                    cert_data['issue_date'] = cert.get('issueDate')
                if cert.get('doesNotExpire'):
                    cert_data['expiry_date'] = None
                elif cert.get('expirationDate'):
                    cert_data['expiry_date'] = cert.get('expirationDate')
                if isinstance(cert.get('order'), int):
                    cert_data['order'] = cert.get('order')
                # Filter out empty strings
                cert_data = {k: v for k, v in cert_data.items() if v != '' and v is not None}
                certification_service.create(cert_data)
            
            # Save skills
            skill_service = SkillService()
            skills = draft_data.get('skills', [])
            for skill in skills:
                if skill.get('name'):
                    skill_payload = {
                        'resume_id': resume_id,
                        'name': skill.get('name'),
                        'category': skill.get('category'),
                        'level': skill.get('level'),
                        'order': skill.get('order', 0),
                    }
                    skill_payload = {k: v for k, v in skill_payload.items() if v != '' and v is not None}
                    if skill_payload:
                        skill_service.create(skill_payload)
            
            # Save optimized summary if exists
            optimized_summary = draft_data.get('optimizedSummary') or ''
            if optimized_summary:
                service.update(resume_id, {'optimized_summary': optimized_summary})
            
            # Save professional tagline if exists
            professional_tagline = personal.get('professionalTagline') or personal.get('summary') or ''
            if professional_tagline:
                service.update(resume_id, {
                    'summary': professional_tagline[:300],  # First 300 chars for backwards compat
                    'optimized_summary': optimized_summary or professional_tagline,  # Use optimized_summary if available
                })
            
            # Delete the draft after successful conversion
            draft.delete()
            
            return Response({
                'resume_id': resume_id,
                'message': 'Draft converted to resume successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Rollback: remove owner assignment and delete created resume
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error converting draft {guest_id}: {str(e)}', exc_info=True)
            
            draft.owner = None
            draft.save()
            
            # Try to delete the created resume
            try:
                service.delete(resume_id)
            except Exception:
                pass
            
            return Response(
                {'error': f'Failed to convert draft: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

