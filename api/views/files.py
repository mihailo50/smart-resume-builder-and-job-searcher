"""
File processing views for resume upload, parsing, and export.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from api.serializers.files import (
    ResumeUploadSerializer,
    ResumeUploadResponseSerializer,
    ResumeExportRequestSerializer,
    ResumeExportResponseSerializer,
    FileParseResponseSerializer
)
from config.files.parser import ResumeParser
from config.files.exporter import ResumeExporter
from config.files.storage import FileStorageService
from config.services.resume_service import ResumeService
from api.auth.utils import get_supabase_user_id

logger = logging.getLogger(__name__)


class FileViewSet(viewsets.ViewSet):
    """
    API endpoints for file processing (upload, parse, export).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @extend_schema(
        operation_id='upload_resume',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Resume file (PDF or DOCX)'
                    },
                    'resume_id': {
                        'type': 'string',
                        'format': 'uuid',
                        'description': 'Optional resume ID to update existing resume'
                    }
                },
                'required': ['file']
            }
        },
        responses={200: ResumeUploadResponseSerializer},
        tags=['Files']
    )
    @action(detail=False, methods=['post'], url_path='upload-resume')
    def upload_resume(self, request):
        """
        Upload and parse a resume file (PDF or DOCX).
        
        POST /api/v1/files/upload-resume/
        
        - Parses the uploaded file to extract text
        - Optionally creates or updates a resume with extracted data
        - Stores the file in Supabase Storage
        """
        user_id = get_supabase_user_id(request)
        if not user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get uploaded file
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        resume_id = request.data.get('resume_id')
        
        try:
            # Read file content
            file_content = uploaded_file.read()
            filename = uploaded_file.name
            content_type = uploaded_file.content_type
            
            # Parse file
            parser = ResumeParser()
            parse_result = parser.parse_file(file_content, filename, content_type)
            
            if not parse_result.get('success', False):
                return Response(
                    {
                        'error': f"Failed to parse file: {parse_result.get('error', 'Unknown error')}",
                        'details': parse_result
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload file to storage (local or Supabase)
            storage_service = FileStorageService()
            
            # Create or get resume ID
            resume_service = ResumeService()
            if resume_id:
                # Update existing resume
                resume = resume_service.get_by_id(resume_id)
                if not resume or str(resume.get('user_id')) != str(user_id):
                    return Response(
                        {'error': 'Resume not found or permission denied'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Create new resume
                resume_data = {
                    'user_id': user_id,
                    'title': filename,
                    'summary': parse_result.get('text', '')[:500],  # Use first 500 chars as summary
                    'raw_text': parse_result.get('text', ''),
                    'status': 'draft'
                }
                resume = resume_service.create(resume_data)
                resume_id = resume['id']
            
            # Upload file to storage
            try:
                upload_result = storage_service.upload_resume(
                    user_id=str(user_id),
                    resume_id=str(resume_id),
                    file_content=file_content,
                    filename=filename,
                    content_type=content_type
                )
                file_url = upload_result.get('url', '')
            except Exception as e:
                logger.error(f"Error uploading file to storage: {e}")
                file_url = ''  # Continue without file URL
            
            # Extract structured data (optional)
            structured_data = {}
            try:
                structured_data = parser.extract_structured_data(parse_result.get('text', ''))
            except Exception as e:
                logger.warning(f"Error extracting structured data: {e}")
            
            # Update resume with file URL if available
            if file_url:
                try:
                    resume_service.update(resume_id, {'file_url': file_url})
                except Exception as e:
                    logger.warning(f"Error updating resume with file URL: {e}")
            
            # Return response
            response_serializer = ResumeUploadResponseSerializer({
                'resume_id': resume_id,
                'text_extracted': parse_result.get('text', ''),
                'structured_data': structured_data,
                'file_url': file_url,
                'metadata': parse_result.get('metadata', {})
            })
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error processing resume upload")
            return Response(
                {'error': f'Failed to process file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Note: Resume export is added as an action to ResumeViewSet instead of a separate ViewSet
        """
        Export a resume to PDF or DOCX format.
        
        POST /api/v1/resumes/{id}/export/
        
        - Generates PDF or DOCX file from resume data
        - Uploads to Supabase Storage
        - Returns download URL
        """
        user_id = get_supabase_user_id(request)
        if not user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get resume
        resume_service = ResumeService()
        resume = resume_service.get_resume_with_details(pk)
        
        if not resume:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if str(resume.get('user_id')) != str(user_id):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request
        serializer = ResumeExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        export_format = serializer.validated_data.get('format', 'pdf')
        template_id = serializer.validated_data.get('template_id')
        
        try:
            # Export resume
            exporter = ResumeExporter()
            
            if export_format == 'pdf':
                file_content = exporter.export_to_pdf(resume, template_id)
                content_type = 'application/pdf'
                filename = f"resume_{pk}.pdf"
            elif export_format == 'docx':
                file_content = exporter.export_to_docx(resume, template_id)
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                filename = f"resume_{pk}.docx"
            else:
                return Response(
                    {'error': f'Unsupported format: {export_format}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload to Supabase Storage
            storage_service = SupabaseStorageService()
            upload_result = storage_service.upload_export(
                user_id=str(user_id),
                resume_id=str(pk),
                file_content=file_content,
                format=export_format,
                template_id=str(template_id) if template_id else None
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

