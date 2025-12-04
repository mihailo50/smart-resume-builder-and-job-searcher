"""
Dashboard views for statistics and analytics.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from api.auth.utils import get_supabase_user_id
from config.services.resume_service import ResumeService
from config.services.job_service import SavedJobService
from config.services.base import BaseSupabaseService
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ResumeAnalysesService(BaseSupabaseService):
    """Service for managing resume analyses."""
    
    def __init__(self):
        super().__init__('resume_analyses')
    
    def get_user_analyses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all resume analyses for a user's resumes.
        
        Args:
            user_id: User ID
            
        Returns:
            List: List of resume analyses
        """
        # First get user's resumes
        resume_service = ResumeService()
        resumes = resume_service.get_user_resumes(user_id)
        resume_ids = [str(r['id']) for r in resumes]
        
        if not resume_ids:
            return []
        
        # Get analyses for each resume (Supabase doesn't easily support IN queries)
        # We'll query each resume_id separately and combine results
        all_analyses = []
        for resume_id in resume_ids:
            analyses = self.get_all(
                filters={'resume_id': resume_id},
                order_by='created_at.desc'
            )
            all_analyses.extend(analyses)
        
        # Sort by created_at descending
        all_analyses.sort(
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        return all_analyses
    
    def get_latest_analysis_for_resume(self, resume_id: str) -> Dict[str, Any]:
        """Get the latest analysis for a resume."""
        analyses = self.get_all(
            filters={'resume_id': resume_id},
            order_by='created_at.desc',
            limit=1
        )
        return analyses[0] if analyses else None


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard statistics and analytics.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id='get_dashboard_stats',
        responses={200: {
            'total_resumes': 'int',
            'average_ats_score': 'float',
            'total_views': 'int',
            'saved_jobs': 'int'
        }},
        tags=['Dashboard']
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get dashboard statistics for the current user.
        
        GET /api/v1/dashboard/stats/
        
        Returns:
        {
            "total_resumes": 5,
            "average_ats_score": 87.5,
            "total_views": 234,
            "saved_jobs": 8
        }
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Get total resumes
            resume_service = ResumeService()
            resumes = resume_service.get_user_resumes(supabase_user_id)
            total_resumes = len(resumes)
            
            # Get average ATS score from latest analyses
            analyses_service = ResumeAnalysesService()
            user_analyses = analyses_service.get_user_analyses(supabase_user_id)
            
            # Get latest analysis for each resume
            resume_ids = [str(r['id']) for r in resumes]
            latest_scores = []
            for resume_id in resume_ids:
                latest = analyses_service.get_latest_analysis_for_resume(resume_id)
                if latest and latest.get('ats_score') is not None:
                    latest_scores.append(latest['ats_score'])
            
            average_ats_score = sum(latest_scores) / len(latest_scores) if latest_scores else 0
            
            # Get saved jobs count
            saved_job_service = SavedJobService()
            saved_jobs = saved_job_service.get_user_saved_jobs(supabase_user_id)
            saved_jobs_count = len(saved_jobs)
            
            # Total views - for now, we'll use a placeholder
            # TODO: Implement actual view tracking
            # For now, we can use the number of times resumes were exported/accessed
            # or implement a views table
            total_views = 0  # Placeholder until views tracking is implemented
            
            return Response({
                'total_resumes': total_resumes,
                'average_ats_score': round(average_ats_score, 1),
                'total_views': total_views,
                'saved_jobs': saved_jobs_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error fetching dashboard stats")
            return Response(
                {'error': f'Failed to fetch dashboard stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='get_dashboard_analytics',
        responses={200: {
            'data': [{
                'month': 'str',
                'score': 'float'
            }]
        }},
        tags=['Dashboard']
    )
    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """
        Get dashboard analytics (ATS score over time).
        
        GET /api/v1/dashboard/analytics/
        
        Query params:
        - months: Number of months to retrieve (default: 6)
        
        Returns:
        {
            "data": [
                {"month": "Jan", "score": 75},
                {"month": "Feb", "score": 78},
                ...
            ]
        }
        """
        supabase_user_id = get_supabase_user_id(request)
        if not supabase_user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            months = int(request.query_params.get('months', 6))
            
            # Get all analyses for user's resumes
            analyses_service = ResumeAnalysesService()
            user_analyses = analyses_service.get_user_analyses(supabase_user_id)
            
            if not user_analyses:
                # Return empty data structure with last N months
                now = datetime.now()
                data = []
                for i in range(months - 1, -1, -1):
                    date = now - timedelta(days=30 * i)
                    data.append({
                        'month': date.strftime('%b'),
                        'score': 0
                    })
                return Response({'data': data}, status=status.HTTP_200_OK)
            
            # Group analyses by month
            monthly_scores: Dict[str, List[int]] = {}
            
            for analysis in user_analyses:
                created_at = analysis.get('created_at')
                if not created_at:
                    continue
                
                # Parse datetime string if needed
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        continue
                
                month_key = created_at.strftime('%b')  # e.g., "Jan", "Feb"
                
                if month_key not in monthly_scores:
                    monthly_scores[month_key] = []
                
                score = analysis.get('ats_score')
                if score is not None:
                    monthly_scores[month_key].append(score)
            
            # Calculate average score per month
            monthly_averages = {}
            for month, scores in monthly_scores.items():
                if scores:
                    monthly_averages[month] = sum(scores) / len(scores)
            
            # Generate data for last N months, filling missing months with 0 or previous score
            now = datetime.now()
            data = []
            previous_score = 0
            
            for i in range(months - 1, -1, -1):
                date = now - timedelta(days=30 * i)
                month_key = date.strftime('%b')
                
                score = monthly_averages.get(month_key, previous_score if previous_score > 0 else 0)
                previous_score = score
                
                data.append({
                    'month': month_key,
                    'score': round(score, 1)
                })
            
            return Response({'data': data}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error fetching dashboard analytics")
            return Response(
                {'error': f'Failed to fetch dashboard analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

