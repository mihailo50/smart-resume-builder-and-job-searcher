"""
Resume views for CRUD operations and premium PDF export.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService

logger = logging.getLogger(__name__)
from api.serializers.resume import (
    ResumeSerializer,
    ResumeCreateSerializer,
    ResumeListSerializer,
    ResumeDetailSerializer,
    PersonalInfoSerializer,
    OptimizedSummarySerializer,
    ProfessionalTaglineSerializer,
    ReorderSerializer,
    ResumeMetadataSerializer,
)
from api.serializers.files import (
    ResumeExportRequestSerializer,
    ResumeExportResponseSerializer
)
from api.auth.utils import get_supabase_user_id
from api.permissions import IsResumeOwner
from config.files.exporter import ResumeExporter
from config.files.storage import FileStorageService
from config.services.resume_pdf_generator import PremiumResumePDFGenerator
from django.template.loader import render_to_string


class ResumeViewSet(viewsets.ViewSet):
    """
    ViewSet for resume CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get resumes for current user."""
        supabase_user_id = get_supabase_user_id(self.request)
        if not supabase_user_id:
            return []
        
        service = ResumeService()
        return service.get_user_resumes(supabase_user_id)
    
    @extend_schema(
        operation_id='list_resumes',
        responses={200: ResumeListSerializer(many=True)},
        tags=['Resumes']
    )
    def list(self, request):
        """
        List user's resumes.
        
        GET /api/v1/resumes/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resumes = service.get_user_resumes(supabase_user_id)
        
        serializer = ResumeListSerializer(resumes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_resume',
        request=ResumeCreateSerializer,
        responses={201: ResumeSerializer},
        tags=['Resumes']
    )
    def create(self, request):
        """
        Create a new resume.
        
        POST /api/v1/resumes/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = ResumeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = ResumeService()
        data = serializer.validated_data.copy()
        data['user_id'] = supabase_user_id
        data['status'] = 'draft'
        
        resume = service.create(data)
        
        response_serializer = ResumeSerializer(resume)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='retrieve_resume',
        responses={200: ResumeDetailSerializer},
        tags=['Resumes']
    )
    def retrieve(self, request, pk=None):
        """
        Get resume details.
        
        GET /api/v1/resumes/{id}/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resume = service.get_resume_with_details(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != supabase_user_id:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ResumeDetailSerializer(resume)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='update_resume',
        request=ResumeSerializer,
        responses={200: ResumeSerializer},
        tags=['Resumes']
    )
    def update(self, request, pk=None):
        """
        Update resume.
        
        PUT /api/v1/resumes/{id}/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resume = service.get_by_id(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != supabase_user_id:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ResumeSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_resume = service.update(pk, serializer.validated_data)
        
        response_serializer = ResumeSerializer(updated_resume)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='delete_resume',
        responses={204: None},
        tags=['Resumes']
    )
    def destroy(self, request, pk=None):
        """
        Delete resume.
        
        DELETE /api/v1/resumes/{id}/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resume = service.get_by_id(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != supabase_user_id:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='update_personal_info',
        request=PersonalInfoSerializer,
        responses={200: PersonalInfoSerializer},
        tags=['Resumes']
    )
    @action(detail=True, methods=['put'], url_path='personal')
    def update_personal_info(self, request, pk=None):
        """
        Update personal information for a resume.
        
        PUT /api/v1/resumes/{id}/personal/
        
        Personal info is stored in two places:
        - full_name -> resumes.title
        - email, phone, location, linkedin_url, github_url, portfolio_url -> user_profiles
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[PERSONAL INFO] Request received - pk: {pk}, data: {request.data}")
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resume = service.get_by_id(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != supabase_user_id:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PersonalInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update resume with full_name -> title
        update_data = {}
        if serializer.validated_data.get('full_name'):
            update_data['title'] = serializer.validated_data['full_name']
        
        # Update user profile with personal info (phone, location, linkedin, github, portfolio)
        # Note: email is in auth.users, not user_profiles - we store it anyway for reference
        from config.services.user_service import UserProfileService
        profile_service = UserProfileService()
        
        # Collect all profile data (including empty strings to allow clearing values)
        profile_update_kwargs = {
            'user_id': supabase_user_id,
        }
        
        # Only include fields that were actually provided in the request
        if 'email' in serializer.validated_data:
            profile_update_kwargs['email'] = serializer.validated_data['email'] or None
        if 'phone' in serializer.validated_data:
            profile_update_kwargs['phone_number'] = serializer.validated_data['phone'] or None
        if 'location' in serializer.validated_data:
            profile_update_kwargs['location'] = serializer.validated_data['location'] or None
        if 'linkedin_url' in serializer.validated_data:
            profile_update_kwargs['linkedin_url'] = serializer.validated_data['linkedin_url'] or None
        if 'github_url' in serializer.validated_data:
            profile_update_kwargs['github_url'] = serializer.validated_data['github_url'] or None
        if 'portfolio_url' in serializer.validated_data:
            profile_update_kwargs['portfolio_url'] = serializer.validated_data['portfolio_url'] or None
        if 'date_of_birth' in serializer.validated_data:
            dob = serializer.validated_data['date_of_birth']
            profile_update_kwargs['date_of_birth'] = str(dob) if dob else None
        if 'avatar_url' in serializer.validated_data:
            profile_update_kwargs['avatar_url'] = serializer.validated_data['avatar_url'] or None
        
        # Update or create user profile
        logger.info(f"[PERSONAL INFO] Updating user profile with: {profile_update_kwargs}")
        try:
            updated_profile = profile_service.create_or_update_profile(**profile_update_kwargs)
            logger.info(f"[PERSONAL INFO] User profile updated: {updated_profile}")
        except Exception as e:
            logger.error(f"[PERSONAL INFO] Error updating user profile: {e}")
            return Response(
                {'error': f'Failed to update profile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update resume if needed
        if update_data:
            updated_resume = service.update(pk, update_data)
            logger.info(f"[PERSONAL INFO] Resume updated with: {update_data}")
        else:
            updated_resume = resume
        
        # Return complete personal info response (from saved profile data)
        response_data = {
            'full_name': updated_resume.get('title', ''),
            'email': updated_profile.get('email', '') or '',  # Now saved in user_profiles
            'phone': updated_profile.get('phone_number', '') or '',
            'location': updated_profile.get('location', '') or '',
            'linkedin_url': updated_profile.get('linkedin_url', '') or '',
            'github_url': updated_profile.get('github_url', '') or '',
            'portfolio_url': updated_profile.get('portfolio_url', '') or '',
            'date_of_birth': updated_profile.get('date_of_birth', '') or '',
            'avatar_url': updated_profile.get('avatar', '') or '',
            'message': 'Personal info saved successfully',
        }
        
        logger.info(f"[PERSONAL INFO] Returning response: {response_data}")
        return Response(response_data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='update_professional_tagline',
        request=ProfessionalTaglineSerializer,
        responses={200: ResumeSerializer},
        tags=['Resumes']
    )
    @action(detail=True, methods=['put'], url_path='summary')
    def update_summary(self, request, pk=None):
        """
        Update resume summary (DEPRECATED - now saves to optimized_summary).
        This endpoint is kept for backwards compatibility but now saves to optimized_summary.
        
        PUT /api/v1/resumes/{id}/summary/
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SUMMARY UPDATE] Request received - pk: {pk}, data: {request.data}")
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            logger.warning(f"[SUMMARY UPDATE] User not authenticated - pk: {pk}")
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resume = service.get_by_id(pk)
        
        if not resume:
            logger.warning(f"[SUMMARY UPDATE] Resume not found - pk: {pk}")
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != supabase_user_id:
            logger.warning(f"[SUMMARY UPDATE] Permission denied - pk: {pk}, user_id: {supabase_user_id}")
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Accept both old format (professional_tagline/summary) and new format (optimized_summary/summary)
        serializer = OptimizedSummarySerializer(data=request.data)
        if not serializer.is_valid():
            # Fallback to old serializer for backwards compatibility
            serializer = ProfessionalTaglineSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        
        # Build update data based on what was provided
        update_data = {}
        
        # Handle professional_tagline - save to both professional_tagline and summary fields
        professional_tagline = serializer.validated_data.get('professional_tagline')
        if professional_tagline is not None:
            update_data['professional_tagline'] = professional_tagline
            update_data['summary'] = professional_tagline  # Keep in sync for backwards compat
        
        # Handle optimized_summary - only update if explicitly provided
        optimized_summary = serializer.validated_data.get('optimized_summary')
        if optimized_summary is not None:
            update_data['optimized_summary'] = optimized_summary
        
        # If neither was provided but 'summary' was (legacy), use it for professional_tagline
        if not update_data and serializer.validated_data.get('summary'):
            legacy_summary = serializer.validated_data.get('summary')
            update_data['professional_tagline'] = legacy_summary
            update_data['summary'] = legacy_summary
        
        if not update_data:
            return Response({'error': 'No data provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[SUMMARY UPDATE] Updating resume - pk: {pk}, fields: {list(update_data.keys())}")
        updated_resume = service.update(pk, update_data)
        response_serializer = ResumeSerializer(updated_resume)
        logger.info(f"[SUMMARY UPDATE] Successfully updated - pk: {pk}")
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='update_optimized_summary',
        request=OptimizedSummarySerializer,
        responses={200: ResumeSerializer},
        tags=['Resumes']
    )
    @action(detail=True, methods=['put'], url_path='optimized-summary')
    def update_optimized_summary(self, request, pk=None):
        """
        Update full-length optimized resume summary.
        
        PUT /api/v1/resumes/{id}/optimized-summary/
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[OPTIMIZED SUMMARY UPDATE] Request received - pk: {pk}, data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}")
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service = ResumeService()
        resume = service.get_by_id(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if str(resume.get('user_id')) != supabase_user_id:
            logger.warning(f"[OPTIMIZED SUMMARY UPDATE] Permission denied - pk: {pk}, user_id: {supabase_user_id}")
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OptimizedSummarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        optimized_summary = serializer.validated_data.get('optimized_summary', '')
        logger.info(f"[OPTIMIZED SUMMARY UPDATE] Updating resume - pk: {pk}, summary length: {len(optimized_summary) if optimized_summary else 0}")
        
        updated_resume = service.update(pk, {'optimized_summary': optimized_summary})
        response_serializer = ResumeSerializer(updated_resume)
        logger.info(f"[OPTIMIZED SUMMARY UPDATE] Successfully updated - pk: {pk}")
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id='update_resume_metadata',
        request=ResumeMetadataSerializer,
        responses={200: ResumeSerializer},
        tags=['Resumes']
    )
    @action(detail=True, methods=['patch'], url_path='metadata')
    def update_metadata(self, request, pk=None):
        """
        Update resume metadata such as last selected template/font.
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        service = ResumeService()
        resume = service.get_by_id(pk)

        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if str(resume.get('user_id')) != supabase_user_id:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ResumeMetadataSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        update_data = {}
        if 'last_template' in serializer.validated_data:
            update_data['last_template'] = serializer.validated_data['last_template']
        if 'last_font' in serializer.validated_data:
            update_data['last_font'] = serializer.validated_data['last_font']

        if not update_data:
            return Response(ResumeSerializer(resume).data, status=status.HTTP_200_OK)

        updated_resume = service.update(pk, update_data)
        response_serializer = ResumeSerializer(updated_resume)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='export_resume',
        request=ResumeExportRequestSerializer,
        responses={200: ResumeExportResponseSerializer},
        tags=['Resumes'],
        parameters=[
            dict(name='format', in_='query', description='pdf or docx', required=False, type=str),
            dict(name='template', in_='query', description='Template ID', required=False, type=str),
            dict(name='font', in_='query', description='Font combination', required=False, type=str),
            dict(name='ats_mode', in_='query', description='ATS mode (true/false)', required=False, type=bool),
        ]
    )
    @action(detail=True, methods=['post', 'get'], url_path='export')
    def export(self, request, pk=None):
        """
        Export a resume to PDF or DOCX format with premium templates.
        
        Supports both POST (JSON body) and GET (query params) for easy download links.
        
        GET /api/v1/resumes/{id}/export/?format=pdf&template=modern&font=inter&token={jwt}
        POST /api/v1/resumes/{id}/export/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get resume with ALL related data
        service = ResumeService()
        resume = service.get_resume_with_details(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != str(supabase_user_id):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle parameters based on request method
        params = {}
        if request.method == 'POST':
            # Validate request body
            serializer = ResumeExportRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            params = serializer.validated_data
        else:
            # GET request - use query params
            params = {
                'format': request.query_params.get('format', 'pdf'),
                'template': request.query_params.get('template'),
                'font': request.query_params.get('font'),
                'ats_mode': request.query_params.get('ats_mode', 'false').lower() == 'true',
                'photo_url': request.query_params.get('photo_url')
            }
        
        export_format = params.get('format', 'pdf')
        template_name = params.get('template') or resume.get('last_template') or 'modern-indigo'
        font_combination = params.get('font') or resume.get('last_font') or 'modern'
        ats_mode = params.get('ats_mode', False)
        # Use photo_url from params, or fallback to avatar from user profile
        photo_url = params.get('photo_url') or resume.get('avatar_url') or resume.get('user_profile', {}).get('avatar')
        
        # Debug logging for photo URL
        logger.info(f"[PHOTO DEBUG] params.photo_url: {params.get('photo_url')}")
        logger.info(f"[PHOTO DEBUG] resume.avatar_url: {resume.get('avatar_url')}")
        logger.info(f"[PHOTO DEBUG] user_profile.avatar: {resume.get('user_profile', {}).get('avatar')}")
        logger.info(f"[PHOTO DEBUG] Final photo_url: {photo_url}")
        
        # Log what we're getting from database
        logger.info(
            f"Exporting resume {pk} - "
            f"experiences: {len(resume.get('experiences', []))}, "
            f"projects: {len(resume.get('projects', []))}, "
            f"skills: {len(resume.get('skills', []))}, "
            f"educations: {len(resume.get('educations', []))}, "
            f"certifications: {len(resume.get('certifications', []))}, "
            f"languages: {len(resume.get('languages', []))}, "
            f"title: '{resume.get('title', '')}', "
            f"summary_length: {len(resume.get('summary', ''))}"
        )
        
        # Extract personal_info if it's stored as a JSON field
        personal_info = {}
        if isinstance(resume.get('personal_info'), dict):
            personal_info = resume.get('personal_info', {})
        else:
            # If personal_info is stored as separate fields, construct it
            personal_info = {
                'full_name': resume.get('full_name', ''),
                'email': resume.get('email', ''),
                'phone': resume.get('phone', ''),
                'location': resume.get('location', ''),
                'linkedin_url': resume.get('linkedin_url', ''),
                'github_url': resume.get('github_url', ''),
                'portfolio_url': resume.get('portfolio_url', ''),
            }
        
        # Log experiences before passing to PDF generator
        experiences_for_pdf = resume.get('experiences') or []
        if experiences_for_pdf:
            logger.info(f"First experience dates: start_date={experiences_for_pdf[0].get('start_date')}, end_date={experiences_for_pdf[0].get('end_date')}")
        
        # Get user_profile from resume data
        user_profile = resume.get('user_profile', {})
        
        # Prepare COMPLETE resume data for PDF generation - NO DATA STRIPPING
        resume_data = {
            'id': str(resume.get('id', '')),
            'full_name': personal_info.get('full_name') or resume.get('title', '') or resume.get('full_name', 'Your Name'),
            'title': resume.get('title', ''),  # This is the name field in DB
            'professional_tagline': resume.get('professional_tagline', ''),
            'summary': resume.get('summary', ''),
            'optimized_summary': resume.get('optimized_summary', ''),
            'email': personal_info.get('email') or resume.get('email', '') or user_profile.get('email', ''),
            'phone': personal_info.get('phone') or resume.get('phone', '') or user_profile.get('phone_number', ''),
            'location': personal_info.get('location') or resume.get('location', '') or user_profile.get('location', ''),
            'linkedin_url': personal_info.get('linkedin_url') or resume.get('linkedin_url', '') or user_profile.get('linkedin_url', ''),
            'github_url': personal_info.get('github_url') or resume.get('github_url', '') or user_profile.get('github_url', ''),
            'portfolio_url': personal_info.get('portfolio_url') or resume.get('portfolio_url', '') or user_profile.get('portfolio_url', ''),
            'date_of_birth': resume.get('date_of_birth', '') or user_profile.get('date_of_birth', ''),
            'personal_info': personal_info,
            'user_profile': user_profile,  # Pass user_profile for PDF generator
            # Pass ALL data - ensure lists are never None
            'experiences': resume.get('experiences') or [],
            'educations': resume.get('educations') or [],
            'skills': resume.get('skills') or [],
            'projects': resume.get('projects') or [],
            'certifications': resume.get('certifications') or [],
            'languages': resume.get('languages') or [],
            'interests': resume.get('interests') or [],
        }
        
        # Log final data being sent to generator
        logger.info(
            f"Resume data prepared for PDF - "
            f"full_name: '{resume_data['full_name']}', "
            f"title: '{resume_data['title']}', "
            f"professional_tagline: '{resume_data['professional_tagline']}', "
            f"email: '{resume_data['email']}', "
            f"phone: '{resume_data['phone']}', "
            f"location: '{resume_data['location']}', "
            f"photo_url: '{photo_url}', "
            f"experiences: {len(resume_data['experiences'])}, "
            f"projects: {len(resume_data['projects'])}, "
            f"skills: {len(resume_data['skills'])}, "
            f"educations: {len(resume_data['educations'])}, "
            f"certifications: {len(resume_data['certifications'])}"
        )
        
        try:
            # Export resume
            exporter = ResumeExporter()
            
            if export_format == 'pdf':
                file_content = exporter.export_to_pdf(
                    resume_data,
                    template_name=template_name,
                    font_combination=font_combination,
                    ats_mode=ats_mode,
                    photo_url=photo_url
                )
                content_type = 'application/pdf'
                filename = f"resume_{pk}.pdf"
            elif export_format == 'docx':
                file_content = exporter.export_to_docx(resume, template_name)
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                filename = f"resume_{pk}.docx"
            else:
                return Response(
                    {'error': f'Unsupported format: {export_format}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Return file directly for download
            from django.http import HttpResponse
            
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(file_content)
            
            return response
        
        except ImportError as e:
            logger.error(f"Missing dependency for export: {e}")
            return Response(
                {'error': f'Export functionality not available: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except Exception as e:
            logger.exception("Error exporting resume")
            return Response(
                {'error': f'Failed to export resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='debug_pdf_html',
        tags=['Debug'],
        description='Debug endpoint to get raw HTML being sent to WeasyPrint'
    )
    @action(detail=True, methods=['post'], url_path='debug/pdf-html')
    def debug_pdf_html(self, request, pk=None):
        """
        Debug endpoint: Returns the raw HTML string being sent to WeasyPrint.
        POST /api/v1/resumes/{id}/debug/pdf-html/
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get resume with ALL related data
        service = ResumeService()
        resume = service.get_resume_with_details(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != str(supabase_user_id):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get template from request or use default
        template_name = request.data.get('template', resume.get('last_template', 'sidebar-teal'))
        font_combination = request.data.get('font', resume.get('last_font', 'modern'))
        ats_mode = request.data.get('ats_mode', False)
        photo_url = request.data.get('photo_url')
        
        # Prepare resume data (same as export endpoint)
        personal_info = {}
        if isinstance(resume.get('personal_info'), dict):
            personal_info = resume.get('personal_info', {})
        else:
            personal_info = {
                'full_name': resume.get('full_name', ''),
                'email': resume.get('email', ''),
                'phone': resume.get('phone', ''),
                'location': resume.get('location', ''),
                'linkedin_url': resume.get('linkedin_url', ''),
                'github_url': resume.get('github_url', ''),
                'portfolio_url': resume.get('portfolio_url', ''),
            }
        
        resume_data = {
            'id': str(resume.get('id', '')),
            'full_name': personal_info.get('full_name') or resume.get('title', '') or resume.get('full_name', 'Your Name'),
            'title': resume.get('title', ''),
            'professional_tagline': resume.get('professional_tagline', ''),
            'summary': resume.get('summary', ''),
            'optimized_summary': resume.get('optimized_summary', ''),
            'email': personal_info.get('email') or resume.get('email', ''),
            'phone': personal_info.get('phone') or resume.get('phone', ''),
            'location': personal_info.get('location') or resume.get('location', ''),
            'linkedin_url': personal_info.get('linkedin_url') or resume.get('linkedin_url', ''),
            'github_url': personal_info.get('github_url') or resume.get('github_url', ''),
            'portfolio_url': personal_info.get('portfolio_url') or resume.get('portfolio_url', ''),
            'personal_info': personal_info,
            'experiences': resume.get('experiences') or [],
            'educations': resume.get('educations') or [],
            'skills': resume.get('skills') or [],
            'projects': resume.get('projects') or [],
            'certifications': resume.get('certifications') or [],
            'languages': resume.get('languages') or [],
            'interests': resume.get('interests') or [],
        }
        
        try:
            # Generate HTML using the same method as PDF generation
            generator = PremiumResumePDFGenerator()
            fonts = generator.FONT_COMBINATIONS.get(font_combination, generator.FONT_COMBINATIONS['modern'])
            context = generator._prepare_context(resume_data, template_name, fonts, ats_mode, None, photo_url)
            
            # Generate QR codes
            linkedin_url = resume_data.get('linkedin_url') or resume_data.get('user_profile', {}).get('linkedin_url', '')
            portfolio_url = resume_data.get('portfolio_url') or resume_data.get('user_profile', {}).get('portfolio_url', '')
            if linkedin_url or portfolio_url:
                qr_code_data = generator._generate_qr_code(linkedin_url or portfolio_url)
                if qr_code_data:
                    context['qr_code'] = qr_code_data
            
            resume_id = str(resume_data.get('id', ''))
            portfolio_view_url = f"https://resumeai.pro/view/{resume_id}" if resume_id else (portfolio_url or linkedin_url)
            if portfolio_view_url:
                qr_code_footer_data = generator._generate_qr_code(portfolio_view_url)
                if qr_code_footer_data:
                    context['qr_code_footer'] = qr_code_footer_data
                    context['portfolio_view_url'] = portfolio_view_url
            
            # Render HTML
            template_path = f'resumes/{template_name}.html'
            html_content = render_to_string(template_path, context)
            
            return Response({
                'html': html_content,
                'html_length': len(html_content),
                'template': template_name,
                'data_summary': {
                    'full_name': resume_data['full_name'],
                    'title': resume_data['title'],
                    'professional_tagline': resume_data['professional_tagline'],
                    'experiences_count': len(resume_data['experiences']),
                    'projects_count': len(resume_data['projects']),
                    'skills_count': len(resume_data['skills']),
                    'educations_count': len(resume_data['educations']),
                    'certifications_count': len(resume_data['certifications']),
                    'languages_count': len(resume_data['languages']),
                    'summary_length': len(resume_data.get('summary', '')),
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error generating debug HTML")
            return Response(
                {'error': f'Failed to generate HTML: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
