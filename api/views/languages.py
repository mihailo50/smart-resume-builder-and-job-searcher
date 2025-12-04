"""
Language views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, LanguageService
from api.serializers.resume import LanguageSerializer, ReorderSerializer
from api.auth.utils import get_supabase_user_id


class LanguageViewSet(viewsets.ViewSet):
    """
    ViewSet for language CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_languages',
        responses={200: LanguageSerializer(many=True)},
        tags=['Languages']
    )
    def list(self, request, **kwargs):
        """
        List languages for a resume.
        
        GET /api/v1/resumes/{resume_id}/languages/
        """
        resume_id = self.get_resume_id()
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify resume ownership
        resume_service = ResumeService()
        resume = resume_service.get_by_id(resume_id)
        
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
        
        service = LanguageService()
        languages = service.get_by_resume_id(resume_id)
        
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_language',
        request=LanguageSerializer,
        responses={201: LanguageSerializer},
        tags=['Languages']
    )
    def create(self, request, **kwargs):
        """
        Create a new language entry.
        
        POST /api/v1/resumes/{resume_id}/languages/
        """
        resume_id = self.get_resume_id()
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify resume ownership
        resume_service = ResumeService()
        resume = resume_service.get_by_id(resume_id)
        
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
        
        serializer = LanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add resume_id to data
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        service = LanguageService()
        language = service.create(data)
        
        response_serializer = LanguageSerializer(language)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='get_language',
        responses={200: LanguageSerializer},
        tags=['Languages']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a specific language.
        
        GET /api/v1/resumes/{resume_id}/languages/{id}/
        """
        resume_id = self.get_resume_id()
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify resume ownership
        resume_service = ResumeService()
        resume = resume_service.get_by_id(resume_id)
        
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
        
        service = LanguageService()
        language = service.get_by_id(pk)
        
        if not language:
            return Response(
                {'error': 'Language not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        lang_resume_id = str(language.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if lang_resume_id != url_resume_id:
            return Response(
                {'error': 'Language not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LanguageSerializer(language)
        return Response(serializer.data)
    
    def _update(self, request, pk=None, partial=False, **kwargs):
        """Internal update method."""
        resume_id = self.get_resume_id()
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify resume ownership
        resume_service = ResumeService()
        resume = resume_service.get_by_id(resume_id)
        
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
        
        service = LanguageService()
        language = service.get_by_id(pk)
        
        if not language:
            return Response(
                {'error': 'Language not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        lang_resume_id = str(language.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if lang_resume_id != url_resume_id:
            return Response(
                {'error': 'Language not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LanguageSerializer(language, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_language = service.update(pk, serializer.validated_data)
        response_serializer = LanguageSerializer(updated_language)
        return Response(response_serializer.data)
    
    @extend_schema(
        operation_id='update_language',
        request=LanguageSerializer,
        responses={200: LanguageSerializer},
        tags=['Languages']
    )
    def update(self, request, pk=None, **kwargs):
        """
        Update a language entry.
        
        PUT /api/v1/resumes/{resume_id}/languages/{id}/
        """
        return self._update(request, pk, partial=False, **kwargs)
    
    @extend_schema(
        operation_id='partial_update_language',
        request=LanguageSerializer,
        responses={200: LanguageSerializer},
        tags=['Languages']
    )
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update a language entry.
        
        PATCH /api/v1/resumes/{resume_id}/languages/{id}/
        """
        return self._update(request, pk, partial=True, **kwargs)
    
    @extend_schema(
        operation_id='delete_language',
        responses={204: None},
        tags=['Languages']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete a language entry.
        
        DELETE /api/v1/resumes/{resume_id}/languages/{id}/
        """
        resume_id = self.get_resume_id()
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify resume ownership
        resume_service = ResumeService()
        resume = resume_service.get_by_id(resume_id)
        
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
        
        service = LanguageService()
        language = service.get_by_id(pk)
        
        if not language:
            return Response(
                {'error': 'Language not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        lang_resume_id = str(language.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if lang_resume_id != url_resume_id:
            return Response(
                {'error': 'Language not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='reorder_languages',
        request=ReorderSerializer,
        responses={200: {'message': 'Languages reordered successfully'}},
        tags=['Languages']
    )
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, **kwargs):
        """
        Reorder languages.
        
        PATCH /api/v1/resumes/{resume_id}/languages/reorder/
        """
        resume_id = self.get_resume_id()
        
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify resume ownership
        resume_service = ResumeService()
        resume = resume_service.get_by_id(resume_id)
        
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
        
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_ids = serializer.validated_data.get('item_ids', [])
        
        service = LanguageService()
        for index, lang_id in enumerate(item_ids):
            service.update(lang_id, {'order': index})
        
        return Response({'message': 'Languages reordered successfully'}, status=status.HTTP_200_OK)











