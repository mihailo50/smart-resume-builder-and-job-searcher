"""
Resume views for CRUD operations and premium PDF export.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService
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
        responses={200: ResumeSerializer},
        tags=['Resumes']
    )
    @action(detail=True, methods=['put'], url_path='personal')
    def update_personal_info(self, request, pk=None):
        """
        Update personal information for a resume.
        
        PUT /api/v1/resumes/{id}/personal/
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
        
        serializer = PersonalInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update resume with personal info
        update_data = {}
        if 'full_name' in serializer.validated_data:
            update_data['title'] = serializer.validated_data['full_name']
        
        # Update user profile with personal info (phone, location, linkedin, github, portfolio)
        # Note: email is in auth.users, not user_profiles
        from config.services.user_service import UserProfileService
        profile_service = UserProfileService()
        
        # Filter out empty strings and None values before updating profile
        profile_data = {}
        if serializer.validated_data.get('phone'):
            profile_data['phone_number'] = serializer.validated_data['phone']
        if serializer.validated_data.get('location'):
            profile_data['location'] = serializer.validated_data['location']
        if serializer.validated_data.get('linkedin_url'):
            profile_data['linkedin_url'] = serializer.validated_data['linkedin_url']
        if serializer.validated_data.get('github_url'):
            profile_data['github_url'] = serializer.validated_data['github_url']
        if serializer.validated_data.get('portfolio_url'):
            profile_data['portfolio_url'] = serializer.validated_data['portfolio_url']
        
        # Update or create user profile with available data (only non-empty values)
        if profile_data:
            profile_service.create_or_update_profile(
                user_id=supabase_user_id,
                phone_number=profile_data.get('phone_number'),
                location=profile_data.get('location'),
                linkedin_url=profile_data.get('linkedin_url'),
                github_url=profile_data.get('github_url'),
                portfolio_url=profile_data.get('portfolio_url'),
            )
        
        if update_data:
            updated_resume = service.update(pk, update_data)
            response_serializer = ResumeSerializer(updated_resume)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(ResumeSerializer(resume).data, status=status.HTTP_200_OK)
    
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
        
        # Extract summary text from various possible fields
        summary_text = (
            serializer.validated_data.get('optimized_summary') or
            serializer.validated_data.get('summary') or
            serializer.validated_data.get('professional_tagline') or
            ''
        )
        
        # Save to optimized_summary (primary field)
        # Also update summary for backwards compatibility
        update_data = {
            'optimized_summary': summary_text,
            'summary': summary_text[:300] if summary_text else '',  # Keep first 300 chars in summary for backwards compat
        }
        
        logger.info(f"[SUMMARY UPDATE] Updating resume - pk: {pk}, summary length: {len(summary_text)}")
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
        tags=['Resumes']
    )
    @action(detail=True, methods=['post'], url_path='export')
    def export(self, request, pk=None):
        """
        Export a resume to PDF or DOCX format with premium templates.
        
        POST /api/v1/resumes/{id}/export/
        
        - Supports 8+ professional templates
        - Beautiful typography and styling
        - ATS-friendly mode available
        
        Request body:
        {
            "format": "pdf|docx",
            "template": "modern-indigo|minimalist-black|creative-violet|executive-gold|tech-cyan|sidebar-teal|ats-classic|elegant-emerald",
            "font": "modern|classic|creative",
            "ats_mode": false
        }
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get resume
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
        
        # Validate request
        serializer = ResumeExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        export_format = serializer.validated_data.get('format', 'pdf')
        template_name = serializer.validated_data.get('template') or resume.get('last_template') or 'modern-indigo'
        font_combination = serializer.validated_data.get('font') or resume.get('last_font') or 'modern'
        ats_mode = serializer.validated_data.get('ats_mode', False)
        
        try:
            # Export resume
            exporter = ResumeExporter()
            
            if export_format == 'pdf':
                file_content = exporter.export_to_pdf(
                    resume,
                    template_name=template_name,
                    font_combination=font_combination,
                    ats_mode=ats_mode
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
            
            # Upload to storage (local or Supabase)
            storage_service = FileStorageService()
            upload_result = storage_service.upload_export(
                user_id=str(supabase_user_id),
                resume_id=str(pk),
                file_content=file_content,
                format=export_format,
                template_id=template_name if template_name else None
            )
            
            file_url = upload_result.get('url', '')
            
            # Get signed URL for download (valid for 1 hour)
            try:
                signed_url = storage_service.get_signed_url(
                    bucket=storage_service.BUCKET_EXPORTS,
                    file_path=upload_result.get('path', ''),
                    expires_in=3600  # 1 hour
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error creating signed URL: {e}")
                signed_url = file_url
            
            # Calculate expiration time (1 hour from now)
            from datetime import datetime, timedelta, timezone
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            
            response_serializer = ResumeExportResponseSerializer({
                'file_url': file_url,
                'download_url': signed_url,
                'expires_at': expires_at
            })
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Missing dependency for export: {e}")
            return Response(
                {'error': f'Export functionality not available: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error exporting resume")
            return Response(
                {'error': f'Failed to export resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
