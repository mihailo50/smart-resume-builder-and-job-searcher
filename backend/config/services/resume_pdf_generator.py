"""
Premium Resume PDF Generator with WeasyPrint and Tailwind CSS.

Generates stunning, professional resumes with multiple template options.
"""
import logging
import io
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage
import base64

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
        
        # Generate PDF
        try:
            pdf_bytes = self._generate_pdf_from_html(html_content, template_name)
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
        # Process photo - try photo_url first, then photo_data
        photo_base64 = None
        photo_url_actual = None
        
        if photo_url:
            photo_url_actual = photo_url
        elif photo_data:
            photo_base64 = base64.b64encode(photo_data).decode('utf-8')
        
        # Get user profile data
        user_profile = resume_data.get('user_profile', {})
        
        # Prepare name and title
        full_name = resume_data.get('full_name') or user_profile.get('full_name') or resume_data.get('title', 'Your Name')
        
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
        title = resume_data.get('title') or resume_data.get('position_title', '')
        
        # Sort experiences by start date (most recent first)
        experiences = sorted(
            resume_data.get('experiences', []),
            key=lambda x: x.get('start_date', ''),
            reverse=True
        )
        
        # Sort education by start date (most recent first)
        educations = sorted(
            resume_data.get('educations', []),
            key=lambda x: x.get('start_date', ''),
            reverse=True
        )
        
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
        
        context = {
            'resume': resume_data,
            'full_name': full_name,
            'title': title,
            'summary': summary_text,
            'contact': contact_info,
            'experiences': experiences,
            'educations': educations,
            'skills': resume_data.get('skills', []),
            'skills_by_category': skills_by_category,
            'projects': resume_data.get('projects', []),
            'certifications': resume_data.get('certifications', []),
            'languages': resume_data.get('languages', []),
            'interests': resume_data.get('interests', []),
            'template_name': template_name,
            'fonts': fonts,
            'ats_mode': ats_mode,
            'photo_base64': photo_base64,
            'photo_url': photo_url_actual,
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
    
    def _generate_pdf_from_html(self, html_content: str, template_name: str) -> bytes:
        """Generate PDF from HTML using WeasyPrint or fallback to reportlab."""
        if not WEASYPRINT_AVAILABLE:
            # Fallback to reportlab-based generator
            logger.info("Using reportlab fallback for PDF generation")
            return self._generate_pdf_with_reportlab(html_content, template_name)
        
        try:
            # Configure fonts
            font_config = FontConfiguration()
            
            # Generate PDF
            # Use static directory as base_url for resolving assets
            base_url = str(self.static_dir.parent)  # Points to backend directory
            
            html_doc = HTML(string=html_content, base_url=base_url)
            
            # Try to load external CSS if available
            css_path = self.static_dir / 'css' / 'resume.css'
            stylesheets = []
            
            if css_path.exists():
                try:
                    with open(css_path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    css_doc = CSS(string=css_content, font_config=font_config)
                    stylesheets.append(css_doc)
                except Exception as e:
                    logger.warning(f"Could not load CSS file: {e}")
            
            # Generate PDF
            pdf_bytes = html_doc.write_pdf(stylesheets=stylesheets, font_config=font_config)
            
            return pdf_bytes
        
        except Exception as e:
            logger.error(f"Error generating PDF with WeasyPrint: {e}")
            logger.info("Falling back to reportlab")
            return self._generate_pdf_with_reportlab(html_content, template_name)
    
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

