"""
Interest views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, InterestService
from api.serializers.resume import InterestSerializer, ReorderSerializer
from api.auth.utils import get_supabase_user_id


class InterestViewSet(viewsets.ViewSet):
    """
    ViewSet for interest CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_interests',
        responses={200: InterestSerializer(many=True)},
        tags=['Interests']
    )
    def list(self, request, **kwargs):
        """
        List interests for a resume.
        
        GET /api/v1/resumes/{resume_id}/interests/
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
        
        service = InterestService()
        interests = service.get_by_resume_id(resume_id)
        
        serializer = InterestSerializer(interests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_interest',
        request=InterestSerializer,
        responses={201: InterestSerializer},
        tags=['Interests']
    )
    def create(self, request, **kwargs):
        """
        Create a new interest entry.
        
        POST /api/v1/resumes/{resume_id}/interests/
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
        
        serializer = InterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add resume_id to data
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        service = InterestService()
        interest = service.create(data)
        
        response_serializer = InterestSerializer(interest)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='get_interest',
        responses={200: InterestSerializer},
        tags=['Interests']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a specific interest.
        
        GET /api/v1/resumes/{resume_id}/interests/{id}/
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
        
        service = InterestService()
        interest = service.get_by_id(pk)
        
        if not interest:
            return Response(
                {'error': 'Interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        int_resume_id = str(interest.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if int_resume_id != url_resume_id:
            return Response(
                {'error': 'Interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InterestSerializer(interest)
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
        
        service = InterestService()
        interest = service.get_by_id(pk)
        
        if not interest:
            return Response(
                {'error': 'Interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        int_resume_id = str(interest.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if int_resume_id != url_resume_id:
            return Response(
                {'error': 'Interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InterestSerializer(interest, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_interest = service.update(pk, serializer.validated_data)
        response_serializer = InterestSerializer(updated_interest)
        return Response(response_serializer.data)
    
    @extend_schema(
        operation_id='update_interest',
        request=InterestSerializer,
        responses={200: InterestSerializer},
        tags=['Interests']
    )
    def update(self, request, pk=None, **kwargs):
        """
        Update an interest entry.
        
        PUT /api/v1/resumes/{resume_id}/interests/{id}/
        """
        return self._update(request, pk, partial=False, **kwargs)
    
    @extend_schema(
        operation_id='partial_update_interest',
        request=InterestSerializer,
        responses={200: InterestSerializer},
        tags=['Interests']
    )
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update an interest entry.
        
        PATCH /api/v1/resumes/{resume_id}/interests/{id}/
        """
        return self._update(request, pk, partial=True, **kwargs)
    
    @extend_schema(
        operation_id='delete_interest',
        responses={204: None},
        tags=['Interests']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete an interest entry.
        
        DELETE /api/v1/resumes/{resume_id}/interests/{id}/
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
        
        service = InterestService()
        interest = service.get_by_id(pk)
        
        if not interest:
            return Response(
                {'error': 'Interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        int_resume_id = str(interest.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if int_resume_id != url_resume_id:
            return Response(
                {'error': 'Interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='reorder_interests',
        request=ReorderSerializer,
        responses={200: {'message': 'Interests reordered successfully'}},
        tags=['Interests']
    )
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, **kwargs):
        """
        Reorder interests.
        
        PATCH /api/v1/resumes/{resume_id}/interests/reorder/
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
        
        service = InterestService()
        for index, int_id in enumerate(item_ids):
            service.update(int_id, {'order': index})
        
        return Response({'message': 'Interests reordered successfully'}, status=status.HTTP_200_OK)












