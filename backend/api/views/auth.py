"""
Authentication views for Supabase Auth integration.
"""
import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from supabase import Client
from config.supabase import get_supabase_client
from api.serializers.auth import (
    RegisterSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    TokenResponseSerializer
)
from api.auth.utils import get_user_from_request

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.ViewSet):
    """
    Authentication viewset for Supabase Auth.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='register',
        request=RegisterSerializer,
        responses={201: TokenResponseSerializer},
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """
        Register a new user.
        
        POST /api/v1/auth/register/
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        full_name = serializer.validated_data.get('full_name', '')
        
        try:
            supabase: Client = get_supabase_client()
            
            # Create user in Supabase Auth
            response = supabase.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'full_name': full_name
                    }
                }
            })
            
            if response.user:
                # Get auth tokens
                session = response.session
                
                # Check if email confirmation is required (session is None)
                email_confirmation_required = session is None
                
                # If email confirmation is required and we have service role key, 
                # try to auto-confirm the user for immediate login (development only)
                if email_confirmation_required:
                    from django.conf import settings
                    if settings.DEBUG and settings.SUPABASE_SERVICE_ROLE_KEY:
                        try:
                            # Auto-confirm the user using admin API
                            supabase.auth.admin.update_user_by_id(
                                response.user.id,
                                {'email_confirm': True}
                            )
                            
                            # Sign in to get tokens
                            login_response = supabase.auth.sign_in_with_password({
                                'email': email,
                                'password': password
                            })
                            
                            if login_response.session:
                                session = login_response.session
                                email_confirmation_required = False
                                logger.info(f"Auto-confirmed user {response.user.id} for immediate login")
                        except Exception as admin_error:
                            # If auto-confirmation fails, continue with email confirmation flow
                            logger.warning(f"Could not auto-confirm user: {admin_error}")
                
                response_data = {
                    'access_token': session.access_token if session else None,
                    'refresh_token': session.refresh_token if session else None,
                    'expires_in': session.expires_in if session else None,
                    'token_type': 'Bearer',
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'full_name': full_name
                    }
                }
                
                # Add message if email confirmation is still required
                if email_confirmation_required:
                    response_data['message'] = 'Registration successful! Please check your email to confirm your account before logging in.'
                    response_data['email_confirmation_required'] = True
                else:
                    response_data['message'] = 'Registration successful! You can now login.'
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to create user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {
                    'error': 'Email already registered. Please sign in instead.'
                    if 'already registered' in str(e).lower()
                    else str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id='login',
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        Login user and get access token.
        
        POST /api/v1/auth/login/
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            supabase: Client = get_supabase_client()
            
            # Authenticate user
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if response.user and response.session:
                session = response.session
                
                return Response({
                    'access_token': session.access_token,
                    'refresh_token': session.refresh_token,
                    'expires_in': session.expires_in,
                    'token_type': 'Bearer',
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'user_metadata': response.user.user_metadata
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        except Exception as e:
            return Response(
                {'error': 'Invalid credentials' if 'Invalid' in str(e) else str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @extend_schema(
        operation_id='logout',
        responses={200: {'message': 'Successfully logged out'}},
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user.
        
        POST /api/v1/auth/logout/
        """
        try:
            supabase: Client = get_supabase_client()
            
            # Get token from request
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                # Sign out using token
                supabase.auth.sign_out()
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id='me',
        responses={200: {'user': 'dict'}},
        tags=['Authentication']
    )
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user information.
        
        GET /api/v1/auth/me/
        """
        user = get_user_from_request(request)
        
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            supabase: Client = get_supabase_client()
            
            # Get user from Supabase
            supabase_user_id = user.username  # Supabase user_id is stored as username
            user_response = supabase.auth.admin.get_user_by_id(supabase_user_id)
            
            # Get user profile
            from config.services.user_service import UserProfileService
            profile_service = UserProfileService()
            profile = profile_service.get_user_profile(supabase_user_id)
            
            return Response({
                'user': {
                    'id': user_response.user.id if user_response and user_response.user else supabase_user_id,
                    'email': user_response.user.email if user_response and user_response.user else user.email,
                    'user_metadata': user_response.user.user_metadata if user_response and user_response.user else {},
                    'profile': profile
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Fallback to Django user info
            return Response({
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email if hasattr(user, 'email') else None,
                    'is_authenticated': user.is_authenticated
                }
            }, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='forgot_password',
        request=PasswordResetRequestSerializer,
        responses={200: {'message': 'Password reset email sent'}},
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        """
        Request password reset email.
        
        POST /api/v1/auth/forgot-password/
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            supabase: Client = get_supabase_client()
            
            # Send password reset email
            supabase.auth.reset_password_for_email(email)
            
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id='reset_password',
        request=PasswordResetSerializer,
        responses={200: {'message': 'Password reset successful'}},
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """
        Reset password with token.
        
        POST /api/v1/auth/reset-password/
        """
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            supabase: Client = get_supabase_client()
            
            # Update password using token
            response = supabase.auth.update_user({
                'password': password
            })
            
            return Response(
                {'message': 'Password reset successful'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )




