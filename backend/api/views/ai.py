"""
AI service API views.
"""
import logging
from typing import List, Dict, Any, Optional
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from config.ai.services.ats_analyzer import ATSAnalyzerService
from config.ai.services.enhanced_ats_analyzer import EnhancedATSAnalyzerService
from config.ai.services.suggestion_applier import SuggestionApplierService
from config.ai.services.summary_generator import SummaryGeneratorService
from config.ai.services.job_matcher import JobMatcherService
from config.services.resume_service import ResumeService
from api.serializers.ai import (
    ResumeAnalysisRequestSerializer,
    ResumeAnalysisResponseSerializer,
    SummaryGenerationRequestSerializer,
    SummaryGenerationResponseSerializer,
    JobMatchRequestSerializer,
    JobMatchResponseSerializer
)
from api.auth.utils import get_supabase_user_id
from api.throttles.ai import GuestAIRateLimiter, GuestThrottle
from rest_framework.decorators import throttle_classes


class AIViewSet(viewsets.ViewSet):
    """
    API endpoints for AI services.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ats_analyzer = ATSAnalyzerService()  # Fallback
        self.enhanced_ats_analyzer = EnhancedATSAnalyzerService()
        self.suggestion_applier = SuggestionApplierService()
        self.summary_generator = SummaryGeneratorService()
        self.job_matcher = JobMatcherService()
        self.resume_service = ResumeService()
    
    def _guest_rate_limit(self, request, feature: str):
        limiter = GuestAIRateLimiter(request)
        if not limiter.allow(feature):
            return Response(
                {
                    'detail': "You've used your free AI optimization. Sign up for unlimited access!",
                    'upgrade': True,
                    'pro_tip': "Upgrade to Pro ($9/mo) for unlimited optimizations and job matching.",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return None
    
    def _is_pro_user(self, user_id: Optional[str]) -> bool:
        """Check if user has Pro subscription."""
        if not user_id:
            return False
        # TODO: Check Supabase subscription table
        # For now, return False (all users are free)
        return False
    
    def _add_upsell_message(self, response_data: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Add upsell message to response for non-Pro users."""
        if not self._is_pro_user(user_id):
            response_data['pro_tip'] = "Pro ($9/mo) unlocks tailored job matches with Pinecone."
        return response_data
    
    @extend_schema(
        operation_id='analyze_resume',
        request=ResumeAnalysisRequestSerializer,
        responses={200: ResumeAnalysisResponseSerializer},
        tags=['AI Services']
    )
    @extend_schema(
        operation_id='parse_resume_file',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Resume file (PDF or DOCX)'
                    }
                },
                'required': ['file']
            }
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'text': {'type': 'string'},
                'success': {'type': 'boolean'},
                'error': {'type': 'string'}
            }
        }},
        tags=['AI Services']
    )
    @action(detail=False, methods=['post'], url_path='parse-resume-file', permission_classes=[AllowAny], parser_classes=[MultiPartParser, FormParser])
    def parse_resume_file(self, request):
        """
        Parse a resume file (PDF or DOCX) to extract text.
        Works for both authenticated and guest users.
        
        POST /api/v1/ai/parse-resume-file/
        
        Form Data:
        {
            "file": <binary file>
        }
        
        Returns:
        {
            "text": "Extracted text from file",
            "success": true
        }
        """
        throttle_response = self._guest_rate_limit(request, 'parse_resume_file')
        if throttle_response:
            return throttle_response
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc']
        filename = uploaded_file.name.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return Response(
                {'error': 'Unsupported file type. Please upload a PDF or DOCX file.', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return Response(
                {'error': 'File too large. Maximum size is 10MB.', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read file content
            file_content = uploaded_file.read()
            content_type = uploaded_file.content_type or 'application/pdf'
            
            # Parse file
            from config.files.parser import ResumeParser
            parser = ResumeParser()
            parse_result = parser.parse_file(file_content, uploaded_file.name, content_type)
            
            if not parse_result.get('success', False):
                return Response(
                    {
                        'error': f"Failed to parse file: {parse_result.get('error', 'Unknown error')}",
                        'success': False
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            extracted_text = parse_result.get('text', '')
            
            return Response({
                'text': extracted_text,
                'success': True,
                'metadata': parse_result.get('metadata', {})
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error parsing resume file: {e}")
            return Response(
                {'error': f'Failed to parse file: {str(e)}', 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='analyze-resume', permission_classes=[AllowAny])
    def analyze_resume(self, request):
        """
        Analyze a resume for ATS optimization.
        
        POST /api/v1/ai/analyze-resume/
        
        Body:
        {
            "resume_id": "uuid" (optional),
            "resume_text": "text" (optional, required if resume_id not provided)
        }
        
        Returns:
        {
            "ats_score": 75,
            "missing_keywords": ["JavaScript", "React"],
            "suggestions": [...],
            "readability_score": 85,
            "bullet_strength": 78,
            "quantifiable_achievements": 65
        }
        """
        throttle_response = self._guest_rate_limit(request, 'analyze_resume')
        if throttle_response:
            return throttle_response
        
        serializer = ResumeAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user is authenticated (optional for guest mode)
        user_id = get_supabase_user_id(request)
        
        resume_id = serializer.validated_data.get('resume_id')
        resume_text = serializer.validated_data.get('resume_text')
        
        # Get resume data if resume_id is provided and user is authenticated
        resume_data = None
        if resume_id:
            if not user_id:
                return Response(
                    {'error': 'Authentication required to use resume_id'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            resume = self.resume_service.get_by_id(resume_id)
            
            if not resume:
                return Response(
                    {'error': 'Resume not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify ownership
            if str(resume.get('user_id')) != user_id:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get resume with all details
            resume_data = self.resume_service.get_resume_with_details(resume_id)
        
        # Require either resume_id or resume_text
        if not resume_id and not resume_text:
            return Response(
                {'error': 'Either resume_id or resume_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get job description if provided
        job_desc = serializer.validated_data.get('job_desc')
        
        # Analyze resume using enhanced analyzer
        try:
            analysis = self.enhanced_ats_analyzer.analyze(
                resume_data=resume_data or {},
                resume_text=resume_text,
                job_desc=job_desc
            )
            
            # Add upsell message
            analysis = self._add_upsell_message(analysis, user_id)
            
            response_serializer = ResumeAnalysisResponseSerializer(analysis)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception(f"Analysis failed: {e}")
            # Fallback to basic analyzer
            try:
                analysis = self.ats_analyzer.analyze(
                    resume_data=resume_data or {},
                    resume_text=resume_text,
                    job_desc=job_desc
                )
                analysis = self._add_upsell_message(analysis, user_id)
                response_serializer = ResumeAnalysisResponseSerializer(analysis)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            except Exception as fallback_error:
                return Response(
                    {'error': f'Analysis failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    @extend_schema(
        operation_id='generate_summary',
        request=SummaryGenerationRequestSerializer,
        responses={200: SummaryGenerationResponseSerializer},
        tags=['AI Services']
    )
    @action(detail=False, methods=['post'], url_path='generate-summary')
    def generate_summary(self, request):
        """
        Generate a professional resume summary using AI.
        
        POST /api/v1/ai/generate-summary/
        
        Body:
        {
            "resume_id": "uuid" (required),
            "tone": "professional" (optional),
            "existing_summary": "text" (optional)
        }
        
        Returns:
        {
            "summary": "Generated summary text",
            "tone": "professional"
        }
        """
        serializer = SummaryGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_supabase_user_id(request)
        if not user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        resume_id = serializer.validated_data.get('resume_id')
        if not resume_id:
            return Response(
                {'error': 'resume_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get resume data
        resume_data = self.resume_service.get_resume_with_details(resume_id)
        
        if not resume_data:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify ownership
        if str(resume_data.get('user_id')) != user_id:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate summary
        tone = serializer.validated_data.get('tone', 'professional')
        existing_summary = serializer.validated_data.get('existing_summary')
        
        try:
            summary = self.summary_generator.generate(
                resume_data=resume_data,
                existing_summary=existing_summary,
                tone=tone
            )
            
            response_serializer = SummaryGenerationResponseSerializer({
                'summary': summary,
                'tone': tone
            })
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Summary generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='match_job',
        request=JobMatchRequestSerializer,
        responses={200: JobMatchResponseSerializer},
        tags=['AI Services']
    )
    @action(detail=False, methods=['post'], url_path='match-job')
    def match_job(self, request):
        """
        Match a resume with a job description (keyword-based).
        
        POST /api/v1/ai/match-job/
        
        Body:
        {
            "resume_id": "uuid" (optional),
            "resume_text": "text" (optional, required if resume_id not provided),
            "job_description": "text" (required)
        }
        
        Returns:
        {
            "match_score": 75,
            "missing_keywords": ["JavaScript", "React"],
            "matched_keywords": ["Python", "AWS"],
            "category_matches": {...},
            "recommendations": [...]
        }
        """
        serializer = JobMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_supabase_user_id(request)
        if not user_id:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        resume_id = serializer.validated_data.get('resume_id')
        resume_text = serializer.validated_data.get('resume_text')
        job_description = serializer.validated_data.get('job_description')
        
        # Get resume data if resume_id is provided
        resume_data = None
        if resume_id:
            resume = self.resume_service.get_by_id(resume_id)
            
            if not resume:
                return Response(
                    {'error': 'Resume not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify ownership
            if str(resume.get('user_id')) != user_id:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get resume with all details
            resume_data = self.resume_service.get_resume_with_details(resume_id)
        
        # Match resume with job
        try:
            match_results = self.job_matcher.match(
                resume_data=resume_data or {},
                job_description=job_description,
                resume_text=resume_text
            )
            
            response_serializer = JobMatchResponseSerializer(match_results)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Job matching failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='enhance_summary',
        request={
            'type': 'object',
            'properties': {
                'summary_text': {'type': 'string', 'description': 'The summary text to enhance'},
                'resume_data': {'type': 'object', 'description': 'Optional resume data for context'},
                'tone': {'type': 'string', 'enum': ['professional', 'confident', 'friendly', 'enthusiastic'], 'default': 'professional'}
            },
            'required': ['summary_text']
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'enhanced_summary': {'type': 'string'},
                'tone': {'type': 'string'}
            }
        }},
        tags=['AI Services']
    )
    @throttle_classes([GuestThrottle])
    @action(detail=False, methods=['post'], url_path='enhance-summary', permission_classes=[AllowAny])
    def enhance_summary(self, request):
        """
        Enhance an existing summary using AI.
        Works for both authenticated and guest users.
        
        Guest users are limited to 1 call per 24 hours.
        Authenticated users have unlimited access.
        
        POST /api/v1/ai/enhance-summary/
        
        Body:
        {
            "summary_text": "text" (required),
            "resume_data": {...} (optional, for better context),
            "tone": "professional" (optional)
        }
        
        Returns:
        {
            "enhanced_summary": "Enhanced summary text",
            "tone": "professional"
        }
        """
        # Note: Throttling is handled by GuestThrottle decorator above
        # No need for manual _guest_rate_limit check here
        
        summary_text = request.data.get('summary_text')
        if not summary_text or not summary_text.strip():
            return Response(
                {'error': 'summary_text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resume_data = request.data.get('resume_data')
        tone = request.data.get('tone', 'professional')
        
        try:
            enhanced_summary = self.summary_generator.enhance(
                summary_text=summary_text,
                resume_data=resume_data,
                tone=tone
            )
            
            return Response({
                'enhanced_summary': enhanced_summary,
                'tone': tone
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Summary enhancement failed: {e}")
            return Response(
                {'error': f'Summary enhancement failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        operation_id='apply_suggestions',
        request={
            'type': 'object',
            'properties': {
                'resume_text': {'type': 'string', 'description': 'The current resume text'},
                'suggestions': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'type': {'type': 'string'},
                            'text': {'type': 'string'},
                            'priority': {'type': 'string'}
                        }
                    },
                    'description': 'List of suggestions to apply'
                },
                'missing_keywords': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of missing keywords to include'
                }
            },
            'required': ['resume_text', 'suggestions']
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'optimized_text': {'type': 'string'},
                'changes_applied': {'type': 'array', 'items': {'type': 'string'}}
            }
        }},
        tags=['AI Services']
    )
    @action(detail=False, methods=['post'], url_path='apply-suggestions', permission_classes=[AllowAny])
    def apply_suggestions(self, request):
        """
        Apply AI suggestions to resume by updating Supabase directly.
        Works for both authenticated and guest users.
        
        POST /api/v1/ai/apply-suggestions/
        
        Body:
        {
            "resume_id": "uuid" (required for authenticated users),
            "resume_text": "text" (optional, for guest users),
            "suggestions": [
                {
                    "type": "keyword|formatting|content|readability|achievement",
                    "text": "suggestion text",
                    "priority": "high|medium|low"
                }
            ],
            "missing_keywords": ["keyword1", "keyword2"] (optional)
        }
        
        Returns:
        {
            "resume_data": {...},  # Updated structured data
            "optimized_text": "Improved resume text",
            "changes_applied": ["List of changes made"]
        }
        """
        throttle_response = self._guest_rate_limit(request, 'apply_suggestions')
        if throttle_response:
            return throttle_response
        
        user_id = get_supabase_user_id(request)
        resume_id = request.data.get('resume_id')
        resume_text = request.data.get('resume_text')
        suggestions = request.data.get('suggestions', [])
        missing_keywords = request.data.get('missing_keywords', [])
        
        # For authenticated users with resume_id: update Supabase directly
        if user_id and resume_id:
            # Verify ownership
            resume = self.resume_service.get_by_id(resume_id)
            if not resume:
                return Response(
                    {'error': 'Resume not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if str(resume.get('user_id')) != user_id:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get resume data
            resume_data = self.resume_service.get_resume_with_details(resume_id)
            
            if not suggestions:
                return Response(
                    {'error': 'suggestions list is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Apply suggestions using enhanced service (updates Supabase)
            try:
                result = self.suggestion_applier.apply_suggestions(
                    resume_id=resume_id,
                    resume_data=resume_data,
                    suggestions=suggestions,
                    missing_keywords=missing_keywords,
                    resume_text=resume_text
                )
                
                # Add upsell message
                result = self._add_upsell_message(result, user_id)
                
                # Return full updated resume JSON (already in result['resume_data'])
                return Response(result, status=status.HTTP_200_OK)
            
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.exception(f"Failed to apply suggestions: {e}")
                return Response(
                    {'error': f'Failed to apply suggestions: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Text-only mode (for guests or authenticated users without resume_id)
        if not resume_text or not resume_text.strip():
            return Response(
                {'error': 'resume_text is required when resume_id is not provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not suggestions or len(suggestions) == 0:
            return Response(
                {'error': 'suggestions list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try to use OpenAI for AI-powered suggestion application
            try:
                from config.ai.utils import get_openai_client
                client = get_openai_client()
                
                # Build context for AI
                suggestions_text = '\n'.join([
                    f"- {s.get('text', '')} (Priority: {s.get('priority', 'medium')})"
                    for s in suggestions[:10]  # Limit to top 10 suggestions
                ])
                
                keywords_text = ''
                if missing_keywords:
                    keywords_text = f"\n\nMissing Keywords to incorporate: {', '.join(missing_keywords[:15])}"
                
                prompt = f"""You are an expert ATS resume optimizer. Apply the following suggestions to improve the resume text. Make sure to:

1. Naturally incorporate missing keywords into appropriate sections (preferably Skills or relevant experience descriptions)
2. Convert appropriate sentences to bullet points with action verbs and quantifiable metrics
3. Add quantifiable achievements with numbers, percentages, or metrics where appropriate
4. Improve formatting and readability by using concise sentences and proper structure
5. Enhance action verbs and professional language

Current Resume Text:
{resume_text[:3000]}

Suggestions to Apply:
{suggestions_text}{keywords_text}

Return the OPTIMIZED resume text with ALL suggestions applied. Do not add explanations or comments - only return the improved resume text. Maintain all original information while applying improvements."""

                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert ATS resume optimizer. Apply suggestions to improve resumes while maintaining all original information. Return only the optimized resume text, no explanations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.7,
                )
                
                optimized_text = response.choices[0].message.content.strip()
                
                # Clean up response (remove any markdown formatting if present)
                if '```' in optimized_text:
                    # Extract text from code blocks
                    parts = optimized_text.split('```')
                    if len(parts) > 1:
                        optimized_text = parts[1] if len(parts) > 1 else parts[0]
                        if optimized_text.startswith('text\n'):
                            optimized_text = optimized_text.replace('text\n', '', 1)
                        optimized_text = optimized_text.strip()
                
                # Generate list of changes applied
                changes_applied = [
                    f"Applied {len(suggestions)} suggestion(s) using AI",
                    f"Incorporated {len(missing_keywords)} missing keywords" if missing_keywords else "Enhanced resume structure and formatting"
                ]
                
                return Response({
                    'optimized_text': optimized_text,
                    'changes_applied': changes_applied
                }, status=status.HTTP_200_OK)
                
            except ValueError:
                # OpenAI not available - fallback to basic rule-based application
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("OpenAI not available, using rule-based suggestion application")
                return self._apply_suggestions_rule_based(resume_text, suggestions, missing_keywords)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error applying suggestions: {e}")
            
            # Try fallback rule-based approach
            try:
                return self._apply_suggestions_rule_based(resume_text, suggestions, missing_keywords)
            except Exception as fallback_error:
                logger.exception(f"Fallback suggestion application also failed: {fallback_error}")
                return Response(
                    {'error': f'Failed to apply suggestions: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _apply_suggestions_rule_based(
        self,
        resume_text: str,
        suggestions: List[Dict[str, Any]],
        missing_keywords: List[str]
    ) -> Response:
        """Fallback rule-based suggestion application."""
        import re
        from rest_framework.response import Response
        from rest_framework import status
        
        optimized_text = resume_text
        changes_applied = []
        
        # Apply keyword suggestions
        if missing_keywords:
            keywords_to_add = missing_keywords[:10]
            # Find or create Skills section
            skills_match = re.search(r'(skills|technologies|technical skills)[:.\s]*([^\n]*)', optimized_text, re.IGNORECASE)
            if skills_match:
                existing_skills = skills_match.group(2) or ''
                new_skills = ', '.join(k.title() for k in keywords_to_add)
                optimized_text = optimized_text.replace(
                    skills_match.group(0),
                    f"{skills_match.group(1)}: {existing_skills}, {new_skills}" if existing_skills.strip() else f"{skills_match.group(1)}: {new_skills}"
                )
            else:
                # Add Skills section
                optimized_text = f"Skills: {', '.join(k.title() for k in keywords_to_add)}\n\n{optimized_text}"
            changes_applied.append(f"Added {len(keywords_to_add)} keywords")
        
        # Apply formatting suggestions - convert to bullets
        bullets_before = len(re.findall(r'[•\-\*]', optimized_text))
        lines = optimized_text.split('\n')
        improved_lines = []
        in_experience = False
        
        for line in lines:
            line_stripped = line.strip()
            if re.match(r'^(experience|work|employment|achievements)', line_stripped, re.IGNORECASE):
                in_experience = True
            elif re.match(r'^(education|skills|summary)', line_stripped, re.IGNORECASE):
                in_experience = False
            
            # Convert to bullet if in experience section
            if in_experience and line_stripped and not line_stripped.startswith(('•', '-', '*')) and len(line_stripped) > 30:
                action_verbs = ['developed', 'implemented', 'created', 'managed', 'led', 'achieved', 'increased', 'improved']
                if any(verb in line_stripped.lower() for verb in action_verbs):
                    improved_lines.append(f"• {line_stripped}")
                    continue
            
            improved_lines.append(line)
        
        optimized_text = '\n'.join(improved_lines)
        bullets_after = len(re.findall(r'[•\-\*]', optimized_text))
        if bullets_after > bullets_before:
            changes_applied.append(f"Added {bullets_after - bullets_before} bullet points")
        
        return Response({
            'optimized_text': optimized_text,
            'changes_applied': changes_applied or ['Applied basic formatting improvements']
        }, status=status.HTTP_200_OK)



