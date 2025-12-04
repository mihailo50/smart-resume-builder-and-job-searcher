"""
Template views for serving template previews and metadata.
"""
import os
import logging
from pathlib import Path
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.conf import settings
from django.http import FileResponse, Http404

logger = logging.getLogger(__name__)


class TemplateViewSet(viewsets.ViewSet):
    """
    ViewSet for serving template previews and metadata.
    """
    permission_classes = [AllowAny]  # Templates are public
    
    # Available templates (should match frontend/lib/templates.ts)
    TEMPLATE_IDS = [
        'modern-indigo',
        'minimalist-black',
        'creative-violet',
        'executive-gold',
        'tech-cyan',
        'sidebar-teal',
        'ats-classic',
        'elegant-emerald',
    ]
    
    @extend_schema(
        operation_id='list_templates',
        responses={200: {'type': 'array', 'items': {'type': 'object'}}},
        tags=['Templates']
    )
    def list(self, request):
        """
        List all available templates with metadata.
        
        GET /api/v1/templates/
        """
        templates = []
        for template_id in self.TEMPLATE_IDS:
            template = {
                'id': template_id,
                'preview_url': f'/api/v1/templates/{template_id}/preview/',
                'thumbnail_url': f'/api/v1/templates/{template_id}/thumbnail/',
            }
            templates.append(template)
        
        return Response(templates, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='get_template_preview',
        responses={200: {'content': {'application/pdf': {}}}},
        tags=['Templates']
    )
    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        """
        Get PDF preview of a template.
        
        GET /api/v1/templates/{template_id}/preview/
        
        Returns the PDF preview file for the template.
        """
        template_id = pk
        
        if template_id not in self.TEMPLATE_IDS:
            return Response(
                {'error': f'Template not found: {template_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Look for PDF preview in media/templates/previews/
        # File naming: resume_{template_id}.pdf
        media_root = Path(settings.MEDIA_ROOT)
        preview_path = media_root / 'templates' / 'previews' / f'resume_{template_id}.pdf'
        
        # Fallback to test_exports_pdf if file doesn't exist in new location
        if not preview_path.exists():
            fallback_path = media_root / 'test_exports_pdf' / f'resume_{template_id}.pdf'
            if fallback_path.exists():
                preview_path = fallback_path
            else:
                return Response(
                    {'error': f'Preview not found for template: {template_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try:
            return FileResponse(
                open(preview_path, 'rb'),
                content_type='application/pdf',
                filename=f'{template_id}_preview.pdf'
            )
        except Exception as e:
            logger.error(f"Error serving template preview: {e}")
            return Response(
                {'error': 'Failed to serve preview'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='get_template_thumbnail',
        responses={200: {'content': {'image/png': {}}}},
        tags=['Templates']
    )
    @action(detail=True, methods=['get'], url_path='thumbnail')
    def thumbnail(self, request, pk=None):
        """
        Get thumbnail image of a template.
        
        GET /api/v1/templates/{template_id}/thumbnail/
        
        Returns a thumbnail image for the template.
        """
        template_id = pk
        
        if template_id not in self.TEMPLATE_IDS:
            return Response(
                {'error': f'Template not found: {template_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Look for PNG thumbnail in multiple possible locations
        media_root = Path(settings.MEDIA_ROOT)
        
        # List of possible thumbnail paths (in order of preference)
        possible_paths = [
            # Primary location: thumbnails directory with standard naming
            media_root / 'templates' / 'thumbnails' / f'{template_id}-thumb.png',
            # Alternative: previews directory with standard naming
            media_root / 'templates' / 'previews' / f'{template_id}-thumb.png',
            # Alternative: previews directory with underscore naming
            media_root / 'templates' / 'previews' / f'{template_id}_thumb.png',
            # Alternative: thumbnails directory with underscore naming
            media_root / 'templates' / 'thumbnails' / f'{template_id}_thumb.png',
        ]
        
        thumbnail_path = None
        for path in possible_paths:
            if path.exists():
                thumbnail_path = path
                logger.debug(f"Found thumbnail at: {thumbnail_path}")
                break
        
        if not thumbnail_path:
            # Log all checked paths for debugging
            logger.warning(
                f"Thumbnail not found for template '{template_id}'. "
                f"Checked paths: {[str(p) for p in possible_paths]}"
            )
            return Response(
                {'error': f'Thumbnail not found for template: {template_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Verify file exists and is readable
            if not thumbnail_path.is_file():
                logger.error(f"Thumbnail path is not a file: {thumbnail_path}")
                return Response(
                    {'error': 'Thumbnail file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Use FileResponse with as_attachment=False to serve inline
            response = FileResponse(
                open(thumbnail_path, 'rb'),
                content_type='image/png',
                filename=f'{template_id}_thumbnail.png',
                as_attachment=False
            )
            # Add cache headers for better performance
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            response['Content-Disposition'] = f'inline; filename="{template_id}_thumbnail.png"'
            # Add CORS headers to allow cross-origin requests
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type'
            logger.info(f"Serving thumbnail: {thumbnail_path} (size: {thumbnail_path.stat().st_size} bytes)")
            return response
        except FileNotFoundError:
            logger.error(f"Thumbnail file not found: {thumbnail_path}")
            return Response(
                {'error': 'Thumbnail file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError:
            logger.error(f"Permission denied accessing thumbnail: {thumbnail_path}")
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Error serving template thumbnail: {e}", exc_info=True)
            return Response(
                {'error': f'Failed to serve thumbnail: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





