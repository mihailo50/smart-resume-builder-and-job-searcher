"""
Skills views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, SkillService
from api.serializers.resume import SkillSerializer
from api.auth.utils import get_supabase_user_id


class SkillViewSet(viewsets.ViewSet):
    """
    ViewSet for skills CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_skills',
        responses={200: SkillSerializer(many=True)},
        tags=['Skills']
    )
    def list(self, request, **kwargs):
        """
        List skills for a resume.
        
        GET /api/v1/resumes/{resume_id}/skills/
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
        
        service = SkillService()
        skills = service.get_by_resume_id(resume_id)
        
        serializer = SkillSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_skill',
        request=SkillSerializer,
        responses={201: SkillSerializer},
        tags=['Skills']
    )
    def create(self, request, **kwargs):
        """
        Create a new skill entry.
        
        POST /api/v1/resumes/{resume_id}/skills/
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
        
        serializer = SkillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = SkillService()
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        skill = service.create(data)
        
        response_serializer = SkillSerializer(skill)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='update_skill',
        request=SkillSerializer,
        responses={200: SkillSerializer},
        tags=['Skills']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a single skill entry.
        
        GET /api/v1/resumes/{resume_id}/skills/{id}/
        """
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Skill ID is required'},
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
        
        service = SkillService()
        skill = service.get_by_id(pk)
        
        if not skill:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        skill_resume_id = str(skill.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if skill_resume_id != url_resume_id:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SkillSerializer(skill)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, pk=None, **kwargs):
        """
        Update a skill entry.
        
        PUT /api/v1/resumes/{resume_id}/skills/{id}/
        """
        return self._update(request, pk, partial=False)
    
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update a skill entry.
        
        PATCH /api/v1/resumes/{resume_id}/skills/{id}/
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
                {'error': 'Skill ID is required'},
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
        
        service = SkillService()
        skill = service.get_by_id(pk)
        
        if not skill:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        skill_resume_id = str(skill.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if skill_resume_id != url_resume_id:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SkillSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_skill = service.update(pk, serializer.validated_data)
        
        response_serializer = SkillSerializer(updated_skill)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='delete_skill',
        responses={204: None},
        tags=['Skills']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete a skill entry.
        
        DELETE /api/v1/resumes/{resume_id}/skills/{id}/
        """
        # Get resume_id from URL kwargs
        resume_id = self.get_resume_id()
        
        # Get pk from kwargs if not provided as parameter
        if pk is None:
            pk = self.kwargs.get('pk') or kwargs.get('pk')
        
        if not pk:
            return Response(
                {'error': 'Skill ID is required'},
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
        
        service = SkillService()
        skill = service.get_by_id(pk)
        
        if not skill:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Compare resume_id as strings (both might be UUID objects or strings)
        skill_resume_id = str(skill.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if skill_resume_id != url_resume_id:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

