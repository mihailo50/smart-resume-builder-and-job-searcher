"""
Premium Resume PDF Generator with WeasyPrint and Tailwind CSS.

Generates stunning, professional resumes with multiple template options.
"""
import logging
import io
import requests
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage
import base64

# Try to import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Try to import WeasyPrint (preferred method)
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    logger.warning(f"WeasyPrint not available: {e}")
    logger.warning("Falling back to reportlab. For WeasyPrint, install GTK runtime on Windows.")

# Try to import Playwright (fallback for complex gradients/icons)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = False  # Disabled by default, enable when needed
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Try to import qrcode for QR code generation
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    logger.warning("qrcode not available. QR codes will be skipped.")


class PremiumResumePDFGenerator:
    """
    Generates stunning, professional resumes using WeasyPrint and Tailwind CSS.
    
    Features:
    - 8+ professional templates
    - Beautiful typography and colors
    - Icons, gradients, shadows
    - ATS-friendly mode
    - Multiple font combinations
    """
    
    AVAILABLE_TEMPLATES = [
        'modern-indigo',
        'minimalist-black',
        'creative-violet',
        'executive-gold',
        'tech-cyan',
        'sidebar-teal',
        'ats-classic',
        'elegant-emerald',
    ]
    
    FONT_COMBINATIONS = {
        'modern': {
            'heading': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            'body': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        },
        'classic': {
            'heading': '"Roboto Slab", Georgia, serif',
            'body': '"Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
        },
        'creative': {
            'heading': '"Space Grotesk", -apple-system, sans-serif',
            'body': '"Poppins", -apple-system, BlinkMacSystemFont, sans-serif',
        },
    }
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.template_dir = Path(settings.BASE_DIR) / 'templates' / 'resumes'
        self.static_dir = Path(settings.BASE_DIR) / 'static'
        
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint is required for PDF generation. Install with: pip install weasyprint")
    
    def generate_pdf(
        self,
        resume_data: Dict[str, Any],
        template_name: str = 'modern-indigo',
        font_combination: str = 'modern',
        ats_mode: bool = False,
        photo_data: Optional[bytes] = None,
        photo_url: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Generate a stunning PDF resume.
        
        Args:
            resume_data: Dictionary containing resume data
            template_name: Name of the template to use
            font_combination: Font combination name (modern, classic, creative)
            ats_mode: If True, generate ATS-friendly version (no columns/graphics)
            photo_data: Optional photo image bytes
            
        Returns:
            Tuple of (pdf_bytes, html_preview)
        """
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is required. Install with: pip install weasyprint")
        
        # Validate template
        if template_name not in self.AVAILABLE_TEMPLATES:
            template_name = 'modern-indigo'
            logger.warning(f"Invalid template '{template_name}', using 'modern-indigo'")
        
        # Get font configuration
        fonts = self.FONT_COMBINATIONS.get(font_combination, self.FONT_COMBINATIONS['modern'])
        
        # Prepare template context
        context = self._prepare_context(resume_data, template_name, fonts, ats_mode, photo_data, photo_url)
        
        # Generate QR codes for header (LinkedIn/Portfolio) and footer (portfolio view)
        qr_code_data = None
        qr_code_footer_data = None
        linkedin_url = resume_data.get('linkedin_url') or resume_data.get('user_profile', {}).get('linkedin_url', '')
        portfolio_url = resume_data.get('portfolio_url') or resume_data.get('user_profile', {}).get('portfolio_url', '')
        resume_id = str(resume_data.get('id', ''))
        portfolio_view_url = f"https://resumeai.pro/view/{resume_id}" if resume_id else (portfolio_url or linkedin_url)
        
        # Header QR code (LinkedIn or Portfolio)
        if linkedin_url or portfolio_url:
            qr_code_data = self._generate_qr_code(linkedin_url or portfolio_url)
            if qr_code_data:
                context['qr_code'] = qr_code_data
        
        # Footer QR code (portfolio view URL)
        if portfolio_view_url:
            qr_code_footer_data = self._generate_qr_code(portfolio_view_url)
            if qr_code_footer_data:
                context['qr_code_footer'] = qr_code_footer_data
                context['portfolio_view_url'] = portfolio_view_url
        
        # Render HTML
        template_path = f'resumes/{template_name}.html'
        html_content = render_to_string(template_path, context)
        
        # Debug logging for PDF generation
        logger.debug(f"=== PDF GENERATION DEBUG ===")
        logger.debug(f"Template: {template_name}")
        logger.debug(f"Full name: '{context.get('full_name', 'MISSING')}'")
        logger.debug(f"Title: '{context.get('title', 'MISSING')}'")
        logger.debug(f"Summary length: {len(context.get('summary', ''))}")
        logger.debug(f"Experiences count: {len(context.get('experiences', []))}")
        logger.debug(f"Projects count: {len(context.get('projects', []))}")
        logger.debug(f"Skills count: {len(context.get('skills', []))}")
        logger.debug(f"Educations count: {len(context.get('educations', []))}")
        logger.debug(f"Certifications count: {len(context.get('certifications', []))}")
        logger.debug(f"HTML length: {len(html_content)}")
        logger.debug(f"HTML preview (first 500 chars): {html_content[:500]}")
        
        # Generate PDF
        try:
            pdf_bytes = self._generate_pdf_from_html(html_content, template_name)
            logger.debug(f"PDF generated: {len(pdf_bytes)} bytes")
            return (pdf_bytes, html_content)
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def _prepare_context(
        self,
        resume_data: Dict[str, Any],
        template_name: str,
        fonts: Dict[str, str],
        ats_mode: bool,
        photo_data: Optional[bytes],
        photo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare context for template rendering."""
        # Process photo - download and resize external images to prevent memory issues
        photo_base64 = None
        
        if photo_url:
            # Download and resize external image to prevent WeasyPrint memory issues
            logger.debug(f"Processing photo URL: {photo_url}")
            processed_image = self._download_and_resize_image(photo_url, max_size=200)
            if processed_image:
                # Extract base64 data (remove data URI prefix)
                if processed_image.startswith('data:'):
                    # Keep full data URI for template
                    photo_base64 = processed_image.split(',')[1] if ',' in processed_image else None
                else:
                    photo_base64 = processed_image
                logger.debug(f"Photo processed successfully")
            else:
                logger.warning(f"Failed to process photo from URL, will use initials fallback")
        elif photo_data:
            # Process provided photo data - resize if needed
            if PIL_AVAILABLE:
                try:
                    with Image.open(io.BytesIO(photo_data)) as img:
                        # Convert and resize
                        if img.mode in ('RGBA', 'P', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        if img.width > 200 or img.height > 200:
                            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                        
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=85, optimize=True)
                        photo_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Error processing photo data: {e}")
                    photo_base64 = base64.b64encode(photo_data).decode('utf-8')
            else:
                photo_base64 = base64.b64encode(photo_data).decode('utf-8')
        
        # Get user profile data
        user_profile = resume_data.get('user_profile', {})
        
        # Prepare name and title - use title field as name if full_name not available
        full_name = (
            resume_data.get('full_name') or 
            user_profile.get('full_name') or 
            resume_data.get('title', '') or 
            'Your Name'
        )
        
        # Generate initials for fallback
        initials = self._generate_initials(full_name)
        
        # Prepare contact info
        contact_info = {
            'email': resume_data.get('email') or user_profile.get('email', ''),
            'phone': resume_data.get('phone') or user_profile.get('phone', ''),
            'location': resume_data.get('location') or user_profile.get('location', ''),
            'linkedin': resume_data.get('linkedin_url') or user_profile.get('linkedin_url', ''),
            'github': resume_data.get('github_url') or user_profile.get('github_url', ''),
            'portfolio': resume_data.get('portfolio_url') or user_profile.get('portfolio_url', ''),
        }
        
        # Professional title/tagline - DO NOT use resume_data.get('title') as fallback
        # because 'title' field in DB stores the person's full name, not their job title
        title = (
            resume_data.get('professional_tagline') or 
            resume_data.get('position_title', '')
        )
        
        # Sort experiences by start date (most recent first)
        # CRITICAL: Ensure we have a list, not None
        experiences_raw = resume_data.get('experiences') or []
        logger.debug(f"RAW experiences from resume_data: {type(experiences_raw)}, length: {len(experiences_raw) if isinstance(experiences_raw, list) else 'NOT A LIST'}")
        if isinstance(experiences_raw, list) and len(experiences_raw) > 0:
            experiences = sorted(
                experiences_raw,
                key=lambda x: x.get('start_date', '') if isinstance(x, dict) else '',
                reverse=True
            )
        else:
            experiences = []
        
        # Sort education by start date (most recent first)
        educations_raw = resume_data.get('educations') or []
        if isinstance(educations_raw, list) and len(educations_raw) > 0:
            educations = sorted(
                educations_raw,
                key=lambda x: x.get('start_date', '') if isinstance(x, dict) else '',
                reverse=True
            )
        else:
            educations = []
        
        # Group skills by category
        skills_by_category = {}
        for skill in resume_data.get('skills', []):
            category = skill.get('category', 'General')
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)
        
        # Generate initials for fallback
        initials = self._generate_initials(full_name)
        
        summary_text = resume_data.get('optimized_summary') or resume_data.get('summary', '')
        
        # Log data counts for debugging
        logger.info(
            f"Context data counts - "
            f"experiences: {len(experiences)}, "
            f"educations: {len(educations)}, "
            f"skills: {len(resume_data.get('skills', []))}, "
            f"projects: {len(resume_data.get('projects', []))}, "
            f"certifications: {len(resume_data.get('certifications', []))}, "
            f"languages: {len(resume_data.get('languages', []))}, "
            f"interests: {len(resume_data.get('interests', []))}, "
            f"full_name: '{full_name}', "
            f"title: '{title}', "
            f"summary_length: {len(summary_text)}"
        )
        
        # CRITICAL: Ensure all lists are actual lists, never None
        skills_list = resume_data.get('skills') or []
        
        # Fix project objects - add 'name' field from 'title' for template compatibility
        projects_raw = resume_data.get('projects') or []
        projects_list = []
        for p in projects_raw:
            project = dict(p) if isinstance(p, dict) else {}
            project['name'] = project.get('title', project.get('name', ''))
            projects_list.append(project)
        
        # Fix certification objects - add both 'name' and 'title' fields for template compatibility
        certs_raw = resume_data.get('certifications') or []
        certifications_list = []
        for c in certs_raw:
            cert = dict(c) if isinstance(c, dict) else {}
            # Ensure both name and title exist
            cert['name'] = cert.get('name') or cert.get('title', '')
            cert['title'] = cert.get('title') or cert.get('name', '')
            certifications_list.append(cert)
        
        languages_list = resume_data.get('languages') or []
        interests_list = resume_data.get('interests') or []
        
        logger.debug(f"=== CONTEXT PREPARATION ===")
        logger.debug(f"Experiences (sorted): {len(experiences)}")
        logger.debug(f"Projects: {len(projects_list)}")
        logger.debug(f"Skills: {len(skills_list)}")
        logger.debug(f"Educations: {len(educations)}")
        logger.debug(f"Certifications: {len(certifications_list)}")
        logger.debug(f"Languages: {len(languages_list)}")
        logger.debug(f"Full name: '{full_name}'")
        logger.debug(f"Title: '{title}'")
        logger.debug(f"Summary: '{summary_text[:100] if summary_text else 'EMPTY'}...'")
        
        context = {
            'resume': resume_data,  # Include full resume data for template access
            'full_name': full_name,
            'title': title,
            'professional_tagline': resume_data.get('professional_tagline', ''),
            'summary': summary_text,
            'contact': contact_info,
            'experiences': experiences,  # Already a list
            'educations': educations,  # Already a list
            'skills': skills_list,  # Guaranteed to be a list
            'skills_by_category': skills_by_category,
            'projects': projects_list,  # Guaranteed to be a list
            'certifications': certifications_list,  # Guaranteed to be a list
            'languages': languages_list,  # Guaranteed to be a list
            'interests': interests_list,  # Guaranteed to be a list
            'template_name': template_name,
            'fonts': fonts,
            'ats_mode': ats_mode,
            'photo_base64': photo_base64,
            'photo_url': None,  # Always use photo_base64 to prevent WeasyPrint memory issues
            'photo_hexagon': template_name in ['tech-cyan', 'sidebar-teal'],
            'initials': initials,
        }
        
        return context
    
    def _generate_initials(self, full_name: str) -> str:
        """Generate initials from full name."""
        if not full_name:
            return 'N/A'
        
        parts = full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        else:
            return 'N/A'
    
    def _generate_qr_code(self, url: str) -> Optional[str]:
        """Generate QR code as base64 data URL."""
        if not QRCODE_AVAILABLE or not url:
            return None
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.warning(f"Error generating QR code: {e}")
            return None
    
    def _download_and_resize_image(self, url: str, max_size: int = 200) -> Optional[str]:
        """
        Download an image from URL, resize it, and return as base64.
        This prevents memory issues with large external images.
        
        Args:
            url: The image URL to download
            max_size: Maximum dimension (width or height) in pixels
            
        Returns:
            Base64 data URI string or None if failed
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, skipping image download")
            return None
        
        try:
            # Download image with timeout
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check content length - skip if too large (> 10MB)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:
                logger.warning(f"Image too large ({content_length} bytes), skipping")
                return None
            
            # Read image data
            image_data = io.BytesIO()
            bytes_read = 0
            max_bytes = 10 * 1024 * 1024  # 10MB limit
            
            for chunk in response.iter_content(chunk_size=8192):
                bytes_read += len(chunk)
                if bytes_read > max_bytes:
                    logger.warning(f"Image exceeded {max_bytes} bytes during download, skipping")
                    return None
                image_data.write(chunk)
            
            image_data.seek(0)
            
            # Open and resize image
            with Image.open(image_data) as img:
                # Convert to RGB if necessary (handles RGBA, P mode, etc.)
                if img.mode in ('RGBA', 'P', 'LA'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if larger than max_size
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    logger.debug(f"Resized image to {img.size}")
                
                # Save to bytes as JPEG (smaller than PNG)
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                img_bytes = output.getvalue()
                
                # Convert to base64
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                logger.debug(f"Downloaded and processed image: {len(img_bytes)} bytes")
                
                return f"data:image/jpeg;base64,{img_base64}"
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout downloading image from {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error downloading image from {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error processing image from {url}: {e}")
            return None
    
    def _generate_pdf_from_html(self, html_content: str, template_name: str) -> bytes:
        """Generate PDF from HTML using WeasyPrint - NO FALLBACK."""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "WeasyPrint is REQUIRED for styled PDF generation. "
                "Install with: pip install weasyprint. "
                "ReportLab fallback has been removed to prevent blank/styled PDFs."
            )
        
        # Log first 1000 chars of HTML for debugging
        html_preview = html_content[:1000] if len(html_content) > 1000 else html_content
        logger.info(f"Generating PDF with WeasyPrint for template: {template_name}")
        logger.info(f"HTML preview (first 1000 chars): {html_preview}")
        logger.info(f"Full HTML length: {len(html_content)} chars")
        
        try:
            # Configure fonts
            font_config = FontConfiguration()
            
            # CRITICAL FIX: WeasyPrint needs base_url=None to resolve absolute URLs
            # But we also need to ensure CSS is processed
            # Try with None first (allows absolute URLs like https://fonts.googleapis.com)
            html_doc = HTML(string=html_content, base_url=None)
            
            logger.debug(f"=== WEASYPRINT GENERATION ===")
            logger.debug(f"HTML doc created, length: {len(html_content)}")
            
            # Generate PDF - WeasyPrint automatically processes inline <style> tags
            pdf_bytes = html_doc.write_pdf(stylesheets=[], font_config=font_config)
            
            logger.debug(f"PDF bytes generated: {len(pdf_bytes)}")
            
            logger.info(f"✓ Successfully generated PDF with WeasyPrint ({len(pdf_bytes)} bytes)")
            if len(pdf_bytes) < 10000:
                logger.warning(f"⚠ PDF is suspiciously small ({len(pdf_bytes)} bytes) - may be blank!")
            
            return pdf_bytes
        
        except Exception as e:
            logger.error(f"✗ CRITICAL: WeasyPrint PDF generation failed: {e}")
            logger.exception("Full traceback:")
            # NO FALLBACK - fail hard so we know something is wrong
            raise RuntimeError(
                f"WeasyPrint PDF generation failed: {str(e)}. "
                "This is a critical error - PDF exports are disabled until fixed."
            ) from e
    
    def _generate_pdf_with_reportlab(self, html_content: str, template_name: str) -> bytes:
        """Fallback PDF generation using reportlab with styled templates."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from html.parser import HTMLParser
            import re
        except ImportError:
            raise ImportError("reportlab is required as fallback. Install with: pip install reportlab")
        
        # For now, generate PDF from resume data directly (not HTML parsing)
        # This is a simplified fallback - the proper solution is to fix WeasyPrint installation
        logger.warning("Using simplified reportlab fallback. WeasyPrint is recommended for full template support.")
        
        # Use the resume data from context (we need to pass it differently)
        # For now, return a basic PDF with a note
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=1
        )
        
        # Add note
        story.append(Paragraph(
            "WeasyPrint Templates Available",
            title_style
        ))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            "This is a fallback PDF generator. To use the premium templates, please install WeasyPrint system dependencies.",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            "For Windows, install GTK runtime from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer",
            styles['Normal']
        ))
        
        doc.build(story)
        return buffer.getvalue()
    
    def get_template_preview_html(
        self,
        resume_data: Dict[str, Any],
        template_name: str = 'modern-indigo',
        font_combination: str = 'modern'
    ) -> str:
        """Get HTML preview of the resume (for frontend preview)."""
        fonts = self.FONT_COMBINATIONS.get(font_combination, self.FONT_COMBINATIONS['modern'])
        context = self._prepare_context(resume_data, template_name, fonts, False, None)
        template_path = f'resumes/{template_name}.html'
        return render_to_string(template_path, context)

