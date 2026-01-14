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

# Lazy-loaded WeasyPrint components (loaded only when PDF generation is needed)
_weasyprint_html = None
_weasyprint_css = None
_weasyprint_font_config = None
_weasyprint_checked = False
_weasyprint_available = None

def _ensure_weasyprint():
    """Lazy-load WeasyPrint only when PDF generation is actually needed."""
    global _weasyprint_html, _weasyprint_css, _weasyprint_font_config, _weasyprint_checked, _weasyprint_available
    
    if _weasyprint_checked:
        return _weasyprint_available
    
    _weasyprint_checked = True
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        _weasyprint_html = HTML
        _weasyprint_css = CSS
        _weasyprint_font_config = FontConfiguration
        _weasyprint_available = True
        logger.info("WeasyPrint loaded successfully for PDF generation")
        return True
    except (ImportError, OSError) as e:
        _weasyprint_available = False
        logger.warning(f"WeasyPrint not available: {e}")
        logger.warning("PDF generation will fail. For WeasyPrint, install GTK runtime on Windows.")
        return False

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
        # WeasyPrint is now lazy-loaded, no check needed at init time
    
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
        # Lazy-load WeasyPrint only when actually generating a PDF
        if not _ensure_weasyprint():
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
        # Process photo - try photo_url first, then photo_data
        photo_base64 = None
        photo_url_actual = None
        
        if photo_url:
            photo_url_actual = photo_url
        elif photo_data:
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
        
        # Prepare contact info - check multiple sources
        contact_email = (
            resume_data.get('email') or 
            user_profile.get('email') or 
            resume_data.get('user_profile', {}).get('email', '')
        )
        contact_phone = (
            resume_data.get('phone') or 
            user_profile.get('phone_number') or  # user_profiles table uses phone_number
            user_profile.get('phone') or 
            resume_data.get('user_profile', {}).get('phone_number', '') or
            resume_data.get('user_profile', {}).get('phone', '')
        )
        contact_location = (
            resume_data.get('location') or 
            user_profile.get('location') or 
            resume_data.get('user_profile', {}).get('location', '')
        )
        contact_linkedin = (
            resume_data.get('linkedin_url') or 
            user_profile.get('linkedin_url') or 
            resume_data.get('user_profile', {}).get('linkedin_url', '')
        )
        contact_github = (
            resume_data.get('github_url') or 
            user_profile.get('github_url') or 
            resume_data.get('user_profile', {}).get('github_url', '')
        )
        contact_portfolio = (
            resume_data.get('portfolio_url') or 
            user_profile.get('portfolio_url') or 
            resume_data.get('user_profile', {}).get('portfolio_url', '')
        )
        
        # Log contact info for debugging
        logger.info(f"Contact info - email: '{contact_email}', phone: '{contact_phone}', location: '{contact_location}'")
        
        contact_info = {
            'email': contact_email,
            'phone': contact_phone,
            'location': contact_location,
            'linkedin': contact_linkedin,
            'github': contact_github,
            'portfolio': contact_portfolio,
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
        
        # Fix double punctuation in company names (e.g., "Phuket d.o.o." + "." = "Phuket d.o.o..")
        for exp in experiences:
            if isinstance(exp, dict):
                company = exp.get('company', '')
                # Store original company name, template should handle separator logic
                exp['company_raw'] = company
                # Add flag if company name ends with period (for template logic)
                exp['company_ends_with_period'] = company.rstrip().endswith('.') if company else False
        
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
        
        # Clean up education titles
        for edu in educations:
            if isinstance(edu, dict):
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                
                # Fix specific degree: "Python Developer in Python programming language" -> "Certified Python Developer"
                if degree and 'python developer' in degree.lower() and 'python programming language' in degree.lower():
                    edu['degree_display'] = 'Certified Python Developer'
                    edu['degree_cleaned'] = True
                else:
                    edu['degree_display'] = degree
                
                # Check if this is a High School entry for special formatting
                combined_text = (degree + ' ' + institution).lower()
                is_high_school = any(term in combined_text for term in 
                    ['high school', 'secondary school', 'gymnasium', 'srednja škola', 'gimnazija', 
                     'general education', 'high school general'])
                edu['is_high_school'] = is_high_school
                
                # Clean up High School entries: "High School General - Vuk Karadzic" -> separate degree/institution
                if is_high_school:
                    # Set a clean degree name
                    if 'general' in degree.lower() or not degree or degree.lower() == institution.lower():
                        edu['degree_display'] = 'High School Diploma'
                    elif 'gymnasium' in degree.lower() or 'gimnazija' in degree.lower():
                        edu['degree_display'] = 'Gymnasium Diploma'
                    else:
                        edu['degree_display'] = degree
                    
                    # Clean up institution name (remove "High School" prefix if redundant)
                    inst_clean = institution
                    if ' - ' in institution:
                        # Handle "High School General - Vuk Karadzic" format
                        parts = institution.split(' - ')
                        if len(parts) == 2:
                            inst_clean = parts[1].strip() + ' High School'
                    elif institution.lower().startswith('high school '):
                        inst_clean = institution[12:].strip() + ' High School'
                    
                    edu['institution_display'] = inst_clean if inst_clean else institution
        
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
        # Also prioritize specific projects: Holograph, Translatr, Smart Resume Builder
        projects_raw = resume_data.get('projects') or []
        projects_list = []
        priority_projects = []
        other_projects = []
        
        # Priority project names (case-insensitive partial match)
        priority_names = ['holograph', 'translatr', 'smart resume', 'resume builder']
        
        for p in projects_raw:
            project = dict(p) if isinstance(p, dict) else {}
            project['name'] = project.get('title', project.get('name', ''))
            project_title = project['name'].lower() if project['name'] else ''
            
            # Check if this is a priority project
            is_priority = any(pn in project_title for pn in priority_names)
            
            if is_priority:
                priority_projects.append(project)
            else:
                other_projects.append(project)
        
        # Combine: priority projects first, then others
        projects_list = priority_projects + other_projects
        
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
            # Also add individual contact variables for direct access in templates
            'contact_email': contact_email,
            'contact_phone': contact_phone,
            'contact_location': contact_location,
            'contact_linkedin': contact_linkedin,
            'contact_github': contact_github,
            'contact_portfolio': contact_portfolio,
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
        """Generate PDF from HTML using WeasyPrint - NO FALLBACK."""
        # Ensure WeasyPrint is loaded (lazy import)
        if not _ensure_weasyprint():
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
            # Configure fonts using lazy-loaded FontConfiguration
            font_config = _weasyprint_font_config()
            
            # CRITICAL FIX: WeasyPrint needs base_url=None to resolve absolute URLs
            # But we also need to ensure CSS is processed
            # Try with None first (allows absolute URLs like https://fonts.googleapis.com)
            html_doc = _weasyprint_html(string=html_content, base_url=None)
            
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

