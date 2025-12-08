"""
Project views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, ProjectService
from api.serializers.resume import ProjectSerializer, ReorderSerializer
from api.auth.utils import get_supabase_user_id


class ProjectViewSet(viewsets.ViewSet):
    """
    ViewSet for project CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_projects',
        responses={200: ProjectSerializer(many=True)},
        tags=['Projects']
    )
    def list(self, request, **kwargs):
        """
        List projects for a resume.
        
        GET /api/v1/resumes/{resume_id}/projects/
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
        
        service = ProjectService()
        projects = service.get_by_resume_id(resume_id)
        
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_project',
        request=ProjectSerializer,
        responses={201: ProjectSerializer},
        tags=['Projects']
    )
    def create(self, request, **kwargs):
        """
        Create a new project entry.
        
        POST /api/v1/resumes/{resume_id}/projects/
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
        
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add resume_id to data
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        service = ProjectService()
        project = service.create(data)
        
        response_serializer = ProjectSerializer(project)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='get_project',
        responses={200: ProjectSerializer},
        tags=['Projects']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a specific project.
        
        GET /api/v1/resumes/{resume_id}/projects/{id}/
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
        
        service = ProjectService()
        project = service.get_by_id(pk)
        
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        project_resume_id = str(project.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if project_resume_id != url_resume_id:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProjectSerializer(project)
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
        
        service = ProjectService()
        project = service.get_by_id(pk)
        
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        project_resume_id = str(project.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if project_resume_id != url_resume_id:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProjectSerializer(project, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_project = service.update(pk, serializer.validated_data)
        response_serializer = ProjectSerializer(updated_project)
        return Response(response_serializer.data)
    
    @extend_schema(
        operation_id='update_project',
        request=ProjectSerializer,
        responses={200: ProjectSerializer},
        tags=['Projects']
    )
    def update(self, request, pk=None, **kwargs):
        """
        Update a project entry.
        
        PUT /api/v1/resumes/{resume_id}/projects/{id}/
        """
        return self._update(request, pk, partial=False, **kwargs)
    
    @extend_schema(
        operation_id='partial_update_project',
        request=ProjectSerializer,
        responses={200: ProjectSerializer},
        tags=['Projects']
    )
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update a project entry.
        
        PATCH /api/v1/resumes/{resume_id}/projects/{id}/
        """
        return self._update(request, pk, partial=True, **kwargs)
    
    @extend_schema(
        operation_id='delete_project',
        responses={204: None},
        tags=['Projects']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete a project entry.
        
        DELETE /api/v1/resumes/{resume_id}/projects/{id}/
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
        
        service = ProjectService()
        project = service.get_by_id(pk)
        
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        project_resume_id = str(project.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if project_resume_id != url_resume_id:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='reorder_projects',
        request=ReorderSerializer,
        responses={200: {'message': 'Projects reordered successfully'}},
        tags=['Projects']
    )
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, **kwargs):
        """
        Reorder projects.
        
        PATCH /api/v1/resumes/{resume_id}/projects/reorder/
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
        
        service = ProjectService()
        for index, project_id in enumerate(item_ids):
            service.update(project_id, {'order': index})
        
        return Response({'message': 'Projects reordered successfully'}, status=status.HTTP_200_OK)












