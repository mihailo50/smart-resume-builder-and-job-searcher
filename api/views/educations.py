"""
Education views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, EducationService
from api.serializers.resume import EducationSerializer, ReorderSerializer
from api.auth.utils import get_supabase_user_id


class EducationViewSet(viewsets.ViewSet):
    """
    ViewSet for education CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_educations',
        responses={200: EducationSerializer(many=True)},
        tags=['Educations']
    )
    def list(self, request, **kwargs):
        """
        List educations for a resume.
        
        GET /api/v1/resumes/{resume_id}/educations/
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
        
        service = EducationService()
        educations = service.get_by_resume_id(resume_id)
        
        serializer = EducationSerializer(educations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_education',
        request=EducationSerializer,
        responses={201: EducationSerializer},
        tags=['Educations']
    )
    def create(self, request, **kwargs):
        """
        Create a new education entry.
        
        POST /api/v1/resumes/{resume_id}/educations/
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
        
        serializer = EducationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = EducationService()
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        education = service.create(data)
        
        response_serializer = EducationSerializer(education)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='update_education',
        request=EducationSerializer,
        responses={200: EducationSerializer},
        tags=['Educations']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a single education entry.
        
        GET /api/v1/resumes/{resume_id}/educations/{id}/
        """
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Education ID is required'},
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
        
        service = EducationService()
        education = service.get_by_id(pk)
        
        if not education:
            return Response(
                {'error': 'Education not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        education_resume_id = str(education.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if education_resume_id != url_resume_id:
            return Response(
                {'error': 'Education not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EducationSerializer(education)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, pk=None, **kwargs):
        """
        Update an education entry.
        
        PUT /api/v1/resumes/{resume_id}/educations/{id}/
        """
        return self._update(request, pk, partial=False)
    
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update an education entry.
        
        PATCH /api/v1/resumes/{resume_id}/educations/{id}/
        """
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk=None, partial=False):
        """Internal update method."""
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Education ID is required'},
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
        
        service = EducationService()
        education = service.get_by_id(pk)
        
        if not education:
            return Response(
                {'error': 'Education not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        education_resume_id = str(education.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if education_resume_id != url_resume_id:
            return Response(
                {'error': 'Education not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EducationSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_education = service.update(pk, serializer.validated_data)
        
        response_serializer = EducationSerializer(updated_education)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='delete_education',
        responses={204: None},
        tags=['Educations']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete an education entry.
        
        DELETE /api/v1/resumes/{resume_id}/educations/{id}/
        """
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Education ID is required'},
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
        
        service = EducationService()
        education = service.get_by_id(pk)
        
        if not education:
            return Response(
                {'error': 'Education not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        education_resume_id = str(education.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if education_resume_id != url_resume_id:
            return Response(
                {'error': 'Education not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='reorder_educations',
        request=ReorderSerializer,
        responses={200: {'message': 'Educations reordered'}},
        tags=['Educations']
    )
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, **kwargs):
        """
        Reorder educations.
        
        PATCH /api/v1/resumes/{resume_id}/educations/reorder/
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
        
        service = EducationService()
        item_ids = serializer.validated_data['item_ids']
        
        # Update order for each item
        for index, item_id in enumerate(item_ids):
            service.update(item_id, {'order': index})
        
        return Response(
            {'message': 'Educations reordered'},
            status=status.HTTP_200_OK
        )

