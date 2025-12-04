"""
Certification views for CRUD operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from config.services.resume_service import ResumeService, CertificationService
from api.serializers.resume import CertificationSerializer, ReorderSerializer
from api.auth.utils import get_supabase_user_id


class CertificationViewSet(viewsets.ViewSet):
    """
    ViewSet for certification CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_resume_id(self):
        """Get resume_id from URL kwargs."""
        return self.kwargs.get('resume_id')
    
    @extend_schema(
        operation_id='list_certifications',
        responses={200: CertificationSerializer(many=True)},
        tags=['Certifications']
    )
    def list(self, request, **kwargs):
        """
        List certifications for a resume.
        
        GET /api/v1/resumes/{resume_id}/certifications/
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
        
        service = CertificationService()
        certifications = service.get_by_resume_id(resume_id)
        
        serializer = CertificationSerializer(certifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='create_certification',
        request=CertificationSerializer,
        responses={201: CertificationSerializer},
        tags=['Certifications']
    )
    def create(self, request, **kwargs):
        """
        Create a new certification entry.
        
        POST /api/v1/resumes/{resume_id}/certifications/
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
        
        serializer = CertificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add resume_id to data
        data = serializer.validated_data.copy()
        data['resume_id'] = resume_id
        
        service = CertificationService()
        certification = service.create(data)
        
        response_serializer = CertificationSerializer(certification)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='get_certification',
        responses={200: CertificationSerializer},
        tags=['Certifications']
    )
    def retrieve(self, request, pk=None, **kwargs):
        """
        Get a specific certification.
        
        GET /api/v1/resumes/{resume_id}/certifications/{id}/
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
        
        service = CertificationService()
        certification = service.get_by_id(pk)
        
        if not certification:
            return Response(
                {'error': 'Certification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cert_resume_id = str(certification.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if cert_resume_id != url_resume_id:
            return Response(
                {'error': 'Certification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CertificationSerializer(certification)
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
        
        service = CertificationService()
        certification = service.get_by_id(pk)
        
        if not certification:
            return Response(
                {'error': 'Certification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cert_resume_id = str(certification.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if cert_resume_id != url_resume_id:
            return Response(
                {'error': 'Certification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CertificationSerializer(certification, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_certification = service.update(pk, serializer.validated_data)
        response_serializer = CertificationSerializer(updated_certification)
        return Response(response_serializer.data)
    
    @extend_schema(
        operation_id='update_certification',
        request=CertificationSerializer,
        responses={200: CertificationSerializer},
        tags=['Certifications']
    )
    def update(self, request, pk=None, **kwargs):
        """
        Update a certification entry.
        
        PUT /api/v1/resumes/{resume_id}/certifications/{id}/
        """
        return self._update(request, pk, partial=False, **kwargs)
    
    @extend_schema(
        operation_id='partial_update_certification',
        request=CertificationSerializer,
        responses={200: CertificationSerializer},
        tags=['Certifications']
    )
    def partial_update(self, request, pk=None, **kwargs):
        """
        Partially update a certification entry.
        
        PATCH /api/v1/resumes/{resume_id}/certifications/{id}/
        """
        return self._update(request, pk, partial=True, **kwargs)
    
    @extend_schema(
        operation_id='delete_certification',
        responses={204: None},
        tags=['Certifications']
    )
    def destroy(self, request, pk=None, **kwargs):
        """
        Delete a certification entry.
        
        DELETE /api/v1/resumes/{resume_id}/certifications/{id}/
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
        
        service = CertificationService()
        certification = service.get_by_id(pk)
        
        if not certification:
            return Response(
                {'error': 'Certification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cert_resume_id = str(certification.get('resume_id', ''))
        url_resume_id = str(resume_id)
        
        if cert_resume_id != url_resume_id:
            return Response(
                {'error': 'Certification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        operation_id='reorder_certifications',
        request=ReorderSerializer,
        responses={200: {'message': 'Certifications reordered successfully'}},
        tags=['Certifications']
    )
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, **kwargs):
        """
        Reorder certifications.
        
        PATCH /api/v1/resumes/{resume_id}/certifications/reorder/
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
        
        service = CertificationService()
        for index, cert_id in enumerate(item_ids):
            service.update(cert_id, {'order': index})
        
        return Response({'message': 'Certifications reordered successfully'}, status=status.HTTP_200_OK)











