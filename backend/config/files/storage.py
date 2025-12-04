"""
File storage service wrapper supporting both local and Supabase Storage.
"""
import os
import logging
from typing import Optional, BinaryIO, Dict, Any
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Try to import Supabase (optional)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available. Using local storage only.")


class FileStorageService:
    """
    Service for handling file uploads and downloads.
    Supports both local storage (default) and Supabase Storage (optional).
    """
    
    def __init__(self, use_supabase: Optional[bool] = None, force_supabase: bool = False):
        """
        Initialize file storage service.
        
        Args:
            use_supabase: Force Supabase usage if True, local if False, auto-detect if None
            force_supabase: If True, always use Supabase (for exports) - raises error if not configured
        """
        self.url = getattr(settings, 'SUPABASE_URL', '')
        self.service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')
        self.use_supabase = False
        
        # Storage bucket names (must be defined early, before Supabase initialization)
        self.BUCKET_RESUMES = os.getenv('SUPABASE_STORAGE_BUCKET_RESUMES', 'resumes')
        self.BUCKET_EXPORTS = os.getenv('SUPABASE_STORAGE_BUCKET_EXPORTS', 'exports')
        self.BUCKET_AVATARS = os.getenv('SUPABASE_STORAGE_BUCKET_AVATARS', 'avatars')
        self.BUCKET_TEMPLATES = os.getenv('SUPABASE_STORAGE_BUCKET_TEMPLATES', 'templates')
        
        # Local storage directories
        self.LOCAL_RESUMES_DIR = 'resumes'
        self.LOCAL_EXPORTS_DIR = 'exports'
        self.LOCAL_AVATARS_DIR = 'avatars'
        self.LOCAL_TEMPLATES_DIR = 'templates'
        
        # Force Supabase for exports
        if force_supabase:
            if not SUPABASE_AVAILABLE or not self.url or not self.service_role_key:
                raise ValueError(
                    "Supabase Storage is required but not configured. "
                    "Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
                )
            self.use_supabase = True
        # Determine if we should use Supabase Storage
        elif use_supabase is None:
            # Auto-detect: use Supabase if configured
            self.use_supabase = (
                SUPABASE_AVAILABLE and
                self.url and
                self.service_role_key and
                os.getenv('USE_SUPABASE_STORAGE', 'true').lower() == 'true'
            )
        else:
            self.use_supabase = use_supabase and SUPABASE_AVAILABLE and self.url and self.service_role_key
        
        # Initialize Supabase Storage if enabled
        if self.use_supabase:
            try:
                self.client: Client = create_client(self.url, self.service_role_key)
                self.storage = self.client.storage
                logger.info("Using Supabase Storage for file operations")
                
                # Ensure required buckets exist
                if force_supabase:
                    self._ensure_bucket_exists(self.BUCKET_EXPORTS, public=False)
            except Exception as e:
                if force_supabase:
                    raise ValueError(f"Failed to initialize Supabase Storage: {e}")
                logger.warning(f"Failed to initialize Supabase Storage: {e}. Falling back to local storage.")
                self.use_supabase = False
        else:
            logger.info("Using local file storage for file operations")
        
        # Ensure local directories exist
        if not self.use_supabase:
            self._ensure_local_directories()
    
    def _ensure_local_directories(self):
        """Ensure local storage directories exist."""
        media_root = Path(settings.MEDIA_ROOT)
        for directory in [self.LOCAL_RESUMES_DIR, self.LOCAL_EXPORTS_DIR, 
                          self.LOCAL_AVATARS_DIR, self.LOCAL_TEMPLATES_DIR]:
            dir_path = media_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _ensure_bucket_exists(self, bucket_name: str, public: bool = False):
        """
        Check if a Supabase Storage bucket exists and provide helpful error if not.
        
        Note: Buckets must be created manually in Supabase Dashboard.
        This method provides a clear error message with setup instructions.
        
        Args:
            bucket_name: Name of the bucket
            public: Whether the bucket should be public (default: False for private buckets)
        """
        if not self.use_supabase:
            return
        
        try:
            # Try to list buckets to check if it exists
            try:
                buckets_response = self.storage.list_buckets()
                bucket_exists = False
                
                # Handle different response formats
                if hasattr(buckets_response, '__iter__'):
                    for bucket in buckets_response:
                        if hasattr(bucket, 'name'):
                            if bucket.name == bucket_name:
                                bucket_exists = True
                                break
                        elif isinstance(bucket, dict):
                            if bucket.get('name') == bucket_name or bucket.get('id') == bucket_name:
                                bucket_exists = True
                                break
                
                if bucket_exists:
                    logger.debug(f"Bucket '{bucket_name}' exists")
                    return
            except Exception as list_error:
                # If we can't list buckets, we'll try the upload and let it fail with a clearer error
                logger.debug(f"Could not verify bucket existence: {list_error}")
                return
            
            # Bucket doesn't exist - provide clear instructions
            error_message = (
                f"\n{'='*70}\n"
                f"SUPABASE STORAGE BUCKET NOT FOUND\n"
                f"{'='*70}\n"
                f"The bucket '{bucket_name}' does not exist in your Supabase Storage.\n\n"
                f"To fix this, create the bucket manually:\n"
                f"1. Go to your Supabase Dashboard: https://app.supabase.com\n"
                f"2. Select your project\n"
                f"3. Navigate to: Storage (left sidebar)\n"
                f"4. Click 'New bucket' button\n"
                f"5. Enter bucket name: {bucket_name}\n"
                f"6. Set visibility: {'Public' if public else 'Private'} (Private recommended for exports)\n"
                f"7. Click 'Create bucket'\n\n"
                f"After creating the bucket, try exporting again.\n"
                f"{'='*70}\n"
            )
            logger.error(error_message)
            raise ValueError(
                f"Bucket '{bucket_name}' not found in Supabase Storage. "
                f"Please create it in Supabase Dashboard: Storage > New bucket > Name: '{bucket_name}' > Private"
            )
        except ValueError:
            # Re-raise ValueError with instructions
            raise
        except Exception as e:
            # For other errors, log but don't fail - let the upload attempt show the real error
            logger.warning(f"Error checking bucket existence ({bucket_name}): {e}")
    
    def _get_local_path(self, directory: str, file_path: str) -> str:
        """Get local file path for a given directory and file path."""
        return f"{directory}/{file_path}"
    
    def _get_local_url(self, file_path: str) -> str:
        """Get local file URL."""
        return f"{settings.MEDIA_URL}{file_path}"
    
    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_content: BinaryIO | bytes,
        file_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to storage (Supabase or local).
        
        Args:
            bucket: Storage bucket name
            file_path: Path within the bucket (e.g., 'user_id/resume.pdf')
            file_content: File content as BinaryIO or bytes
            file_options: Optional upload options (e.g., {'content-type': 'application/pdf'})
            
        Returns:
            Dict with file URL and metadata
        """
        if self.use_supabase:
            return self._upload_to_supabase(bucket, file_path, file_content, file_options)
        else:
            return self._upload_to_local(bucket, file_path, file_content, file_options)
    
    def _upload_to_supabase(
        self,
        bucket: str,
        file_path: str,
        file_content: BinaryIO | bytes,
        file_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload file to Supabase Storage."""
        try:
            # Ensure bucket exists before uploading
            self._ensure_bucket_exists(bucket, public=False)
            
            bucket_client = self.storage.from_(bucket)
            
            # Ensure file_content is bytes
            if hasattr(file_content, 'read'):
                # It's a file-like object, read it
                file_bytes = file_content.read()
            elif isinstance(file_content, bytes):
                file_bytes = file_content
            else:
                # Try to convert to bytes
                file_bytes = bytes(file_content)
            
            # Prepare file options (for HTTP headers - must be strings)
            options = file_options.copy() if file_options else {}
            
            # Extract upsert parameter (not an HTTP header)
            upsert = options.pop('upsert', False)
            
            # Ensure content-type is set (must be string)
            if 'content-type' not in options and 'content_type' not in options:
                # Try to infer from file extension
                if file_path.endswith('.pdf'):
                    options['content-type'] = 'application/pdf'
                elif file_path.endswith('.docx'):
                    options['content-type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            # Filter file_options to only include valid HTTP headers (strings/bytes)
            # Remove any non-string values that aren't valid headers
            clean_options = {}
            for k, v in options.items():
                if isinstance(v, (str, bytes)):
                    clean_options[k] = v
                elif k == 'content-type' and isinstance(v, (str, bytes)):
                    clean_options[k] = v
            
            # If upsert is True, try to delete existing file first, then upload
            # This ensures we can overwrite files
            if upsert:
                try:
                    bucket_client.remove([file_path])
                    logger.debug(f"Removed existing file before upload: {file_path}")
                except Exception as e:
                    # File might not exist, which is fine
                    logger.debug(f"File doesn't exist or couldn't be removed (will upload anyway): {e}")
            
            # Upload file to Supabase Storage
            # file_options only contains HTTP headers (strings/bytes)
            response = bucket_client.upload(
                path=file_path,
                file=file_bytes,
                file_options=clean_options if clean_options else None
            )
            
            logger.info(f"Successfully uploaded file to Supabase Storage: {bucket}/{file_path}")
            
            # Return path (we'll use signed URLs, not public URLs)
            return {
                'url': '',  # We use signed URLs instead
                'path': file_path,
                'bucket': bucket,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {e}")
            raise
    
    def _upload_to_local(
        self,
        bucket: str,
        file_path: str,
        file_content: BinaryIO | bytes,
        file_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload file to local storage."""
        try:
            # Map bucket to local directory
            bucket_to_dir = {
                self.BUCKET_RESUMES: self.LOCAL_RESUMES_DIR,
                self.BUCKET_EXPORTS: self.LOCAL_EXPORTS_DIR,
                self.BUCKET_AVATARS: self.LOCAL_AVATARS_DIR,
                self.BUCKET_TEMPLATES: self.LOCAL_TEMPLATES_DIR,
            }
            directory = bucket_to_dir.get(bucket, bucket)
            
            # Create local path
            local_path = self._get_local_path(directory, file_path)
            
            # Ensure bytes
            if hasattr(file_content, 'read'):
                file_content = file_content.read()
            
            # Save file
            saved_path = default_storage.save(local_path, ContentFile(file_content))
            
            # Get URL
            file_url = self._get_local_url(saved_path)
            
            return {
                'url': file_url,
                'path': saved_path,
                'bucket': bucket,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error uploading file to local storage: {e}")
            raise
    
    def upload_resume(
        self,
        user_id: str,
        resume_id: str,
        file_content: BinaryIO | bytes,
        filename: str,
        content_type: str = 'application/pdf'
    ) -> Dict[str, Any]:
        """
        Upload a resume file to the resumes bucket.
        
        Args:
            user_id: User ID
            resume_id: Resume ID
            file_content: File content
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Dict with file URL and metadata
        """
        # Create path: user_id/resume_id/filename
        file_path = f"{user_id}/{resume_id}/{filename}"
        
        file_options = {
            'content-type': content_type,
            'upsert': False  # Don't overwrite existing files
        }
        
        return self.upload_file(
            bucket=self.BUCKET_RESUMES,
            file_path=file_path,
            file_content=file_content,
            file_options=file_options
        )
    
    def upload_export(
        self,
        user_id: str,
        resume_id: str,
        file_content: BinaryIO | bytes,
        format: str = 'pdf',
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an exported resume to the exports bucket.
        
        Args:
            user_id: User ID
            resume_id: Resume ID
            file_content: File content
            format: Export format ('pdf' or 'docx')
            template_id: Optional template ID
            
        Returns:
            Dict with file URL and metadata
        """
        # Create filename
        filename = f"resume_{resume_id}.{format}"
        if template_id:
            filename = f"resume_{resume_id}_template_{template_id}.{format}"
        
        # Create path: user_id/resume_id/filename
        file_path = f"{user_id}/{resume_id}/{filename}"
        
        content_type = 'application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        file_options = {
            'content-type': content_type,
            'upsert': True  # Overwrite existing exports
        }
        
        return self.upload_file(
            bucket=self.BUCKET_EXPORTS,
            file_path=file_path,
            file_content=file_content,
            file_options=file_options
        )
    
    def upload_avatar(
        self,
        user_id: str,
        file_content: BinaryIO | bytes,
        filename: str,
        content_type: str = 'image/jpeg'
    ) -> Dict[str, Any]:
        """
        Upload a user avatar to the avatars bucket.
        
        Args:
            user_id: User ID
            file_content: File content
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Dict with file URL and metadata
        """
        # Create path: user_id/avatar.ext
        file_ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        file_path = f"{user_id}/avatar.{file_ext}"
        
        file_options = {
            'content-type': content_type,
            'upsert': True  # Overwrite existing avatar
        }
        
        return self.upload_file(
            bucket=self.BUCKET_AVATARS,
            file_path=file_path,
            file_content=file_content,
            file_options=file_options
        )
    
    def download_file(self, bucket: str, file_path: str) -> bytes:
        """
        Download a file from Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            file_path: Path within the bucket
            
        Returns:
            File content as bytes
            
        Raises:
            Exception: If download fails
        """
        try:
            bucket_client = self.storage.from_(bucket)
            response = bucket_client.download(file_path)
            
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, bytes):
                return response
            else:
                return bytes(response)
        
        except Exception as e:
            logger.error(f"Error downloading file from Supabase Storage: {e}")
            raise
    
    def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            file_path: Path within the bucket
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            bucket_client = self.storage.from_(bucket)
            response = bucket_client.remove([file_path])
            return True
        
        except Exception as e:
            logger.error(f"Error deleting file from Supabase Storage: {e}")
            return False
    
    def get_public_url(self, bucket: str, file_path: str) -> str:
        """
        Get public URL for a file in Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            file_path: Path within the bucket
            
        Returns:
            Public URL string
        """
        try:
            bucket_client = self.storage.from_(bucket)
            return bucket_client.get_public_url(file_path)
        
        except Exception as e:
            logger.error(f"Error getting public URL from Supabase Storage: {e}")
            raise
    
    def get_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Get a signed URL for a file (temporary access).
        
        Args:
            bucket: Storage bucket name
            file_path: Path within the bucket
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL string
            
        Raises:
            ValueError: If Supabase Storage is not configured
        """
        if not self.use_supabase:
            raise ValueError(
                "Signed URLs require Supabase Storage. "
                "Please configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
            )
        
        try:
            bucket_client = self.storage.from_(bucket)
            response = bucket_client.create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            # Handle different response formats from supabase-py
            if isinstance(response, dict):
                return response.get('signedURL', response.get('signed_url', ''))
            elif isinstance(response, str):
                return response
            else:
                # Try to get signedURL attribute if it's an object
                return getattr(response, 'signedURL', getattr(response, 'signed_url', str(response)))
        
        except Exception as e:
            logger.error(f"Error creating signed URL from Supabase Storage: {e}")
            raise

