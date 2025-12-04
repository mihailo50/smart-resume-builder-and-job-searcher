"""
Experience views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, ExperienceService
from api.serializers.resume import ExperienceSerializer, ReorderSerializer
from api.auth.utils import get_supabase_user_id


class ExperienceViewSet(viewsets.ViewSet):
    """
    ViewSet for experience CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_experiences',
        responses={200: ExperienceSerializer(many=True)},
        tags=['Experiences']
    )
    def list(self, request, **kwargs):
        """
        List experiences for a resume.
        
        GET /api/v1/resumes/{resume_id}/experiences/
        """
        # Get resume_id from URL kwargs
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
        
        service = ExperienceService()
        experiences = service.get_by_resume_id(resume_id)
        
        serializer = ExperienceSerializer(experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_experience',
        request=ExperienceSerializer,
        responses={201: ExperienceSerializer},
        tags=['Experiences']
    )
    def create(self, request, **kwargs):
        """
        Create a new experience entry.
        
        POST /api/v1/resumes/{resume_id}/experiences/
        """
        # Get resume_id from URL kwargs
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
        
        serializer = ExperienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = ExperienceService()
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        experience = service.create(data)
        
        response_serializer = ExperienceSerializer(experience)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='update_experience',
        request=ExperienceSerializer,
        responses={200: ExperienceSerializer},
        tags=['Experiences']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a single experience entry.
        
        GET /api/v1/resumes/{resume_id}/experiences/{id}/
        """
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Experience ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        service = ExperienceService()
        experience = service.get_by_id(pk)
        
        if not experience:
            return Response(
                {'error': 'Experience not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        experience_resume_id = str(experience.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if experience_resume_id != url_resume_id:
            return Response(
                {'error': 'Experience not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ExperienceSerializer(experience)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, pk=None, **kwargs):
        """
        Update an experience entry.
        
        PUT /api/v1/resumes/{resume_id}/experiences/{id}/
        """
        return self._update(request, pk, partial=False)
    
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update an experience entry.
        
        PATCH /api/v1/resumes/{resume_id}/experiences/{id}/
        """
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk=None, partial=False):
        """Internal update method."""
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Experience ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        service = ExperienceService()
        experience = service.get_by_id(pk)
        
        if not experience:
            return Response(
                {'error': 'Experience not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        experience_resume_id = str(experience.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if experience_resume_id != url_resume_id:
            return Response(
                {'error': 'Experience not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ExperienceSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_experience = service.update(pk, serializer.validated_data)
        
        response_serializer = ExperienceSerializer(updated_experience)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='delete_experience',
        responses={204: None},
        tags=['Experiences']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete an experience entry.
        
        DELETE /api/v1/resumes/{resume_id}/experiences/{id}/
        """
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Experience ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        service = ExperienceService()
        experience = service.get_by_id(pk)
        
        if not experience:
            return Response(
                {'error': 'Experience not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        experience_resume_id = str(experience.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if experience_resume_id != url_resume_id:
            return Response(
                {'error': 'Experience not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='reorder_experiences',
        request=ReorderSerializer,
        responses={200: {'message': 'Experiences reordered'}},
        tags=['Experiences']
    )
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, **kwargs):
        """
        Reorder experiences.
        
        PATCH /api/v1/resumes/{resume_id}/experiences/reorder/
        """
        # Get resume_id from URL kwargs
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
        
        service = ExperienceService()
        item_ids = serializer.validated_data['item_ids']
        
        # Update order for each item
        for index, item_id in enumerate(item_ids):
            service.update(item_id, {'order': index})
        
        return Response(
            {'message': 'Experiences reordered'},
            status=status.HTTP_200_OK
        )

