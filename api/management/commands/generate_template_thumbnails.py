"""
Django management command to generate thumbnail images from PDF template previews.

This command converts the first page of each template PDF to a PNG thumbnail image.
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    PYMUPDF_VERSION = fitz.version
except ImportError:
    try:
        # Try alternative import
        import PyMuPDF as fitz
        PYMUPDF_AVAILABLE = True
        PYMUPDF_VERSION = fitz.version
    except ImportError:
        PYMUPDF_AVAILABLE = False
        PYMUPDF_VERSION = None

try:
    from PIL import Image as PILImage
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class Command(BaseCommand):
    help = 'Generate thumbnail images from PDF template previews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-dir',
            type=str,
            default=None,
            help='Source directory containing PDF files (default: media/templates/previews)',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Output directory for thumbnails (default: media/templates/thumbnails)',
        )
        parser.add_argument(
            '--width',
            type=int,
            default=380,
            help='Thumbnail width in pixels (default: 380)',
        )
        parser.add_argument(
            '--dpi',
            type=int,
            default=150,
            help='DPI for rendering PDF page (default: 150)',
        )

    def handle(self, *args, **options):
        if not PYMUPDF_AVAILABLE:
            self.stdout.write(
                self.style.ERROR(
                    'PyMuPDF (fitz) is not installed.\n'
                    'Please install it with one of the following commands:\n'
                    '  poetry install\n'
                    '  poetry add PyMuPDF\n'
                    '  pip install PyMuPDF'
                )
            )
            return

        if not PILLOW_AVAILABLE:
            self.stdout.write(
                self.style.ERROR(
                    'Pillow is not installed. Please install it with:\n'
                    '  poetry install\n'
                    '  pip install Pillow'
                )
            )
            return

        # Set up directories
        media_root = Path(settings.MEDIA_ROOT)
        
        source_dir = Path(options['source_dir']) if options['source_dir'] else media_root / 'templates' / 'previews'
        output_dir = Path(options['output_dir']) if options['output_dir'] else media_root / 'templates' / 'thumbnails'
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        width = options['width']
        dpi = options['dpi']
        
        if PYMUPDF_VERSION:
            self.stdout.write(f'Using PyMuPDF version: {PYMUPDF_VERSION}')
        self.stdout.write(f'Source directory: {source_dir}')
        self.stdout.write(f'Output directory: {output_dir}')
        self.stdout.write(f'Thumbnail width: {width}px')
        self.stdout.write(f'DPI: {dpi}')
        self.stdout.write('')
        
        # Template IDs to process
        template_ids = [
            'modern-indigo',
            'minimalist-black',
            'creative-violet',
            'executive-gold',
            'tech-cyan',
            'sidebar-teal',
            'ats-classic',
            'elegant-emerald',
        ]
        
        success_count = 0
        error_count = 0
        
        for template_id in template_ids:
            # Look for PDF file
            pdf_filename = f'resume_{template_id}.pdf'
            pdf_path = source_dir / pdf_filename
            
            if not pdf_path.exists():
                self.stdout.write(
                    self.style.WARNING(f'  WARNING: PDF not found: {pdf_path}')
                )
                error_count += 1
                continue
            
            # Output thumbnail filename
            thumbnail_filename = f'{template_id}-thumb.png'
            thumbnail_path = output_dir / thumbnail_filename
            
            try:
                # Open PDF
                pdf_document = fitz.open(str(pdf_path))
                
                if len(pdf_document) == 0:
                    self.stdout.write(
                        self.style.WARNING(f'  WARNING: PDF has no pages: {pdf_filename}')
                    )
                    pdf_document.close()
                    error_count += 1
                    continue
                
                # Get first page
                first_page = pdf_document[0]
                
                # Calculate zoom factor for desired DPI
                # Default PDF is 72 DPI, so zoom = desired_dpi / 72
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                
                # Render page to pixmap
                pix = first_page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Target dimensions: 380×500px
                target_width = width  # 380px
                target_height = 500
                
                # Resize to exact thumbnail size (maintains aspect ratio, may crop)
                img.thumbnail((target_width, target_height), PILImage.Resampling.LANCZOS)
                
                # If image is smaller than target, create a canvas and center it
                if img.width < target_width or img.height < target_height:
                    canvas = PILImage.new("RGB", (target_width, target_height), (255, 255, 255))
                    x_offset = (target_width - img.width) // 2
                    y_offset = (target_height - img.height) // 2
                    canvas.paste(img, (x_offset, y_offset))
                    img = canvas
                
                # Save thumbnail
                img.save(thumbnail_path, 'PNG', optimize=True)
                
                pdf_document.close()
                
                self.stdout.write(
                    self.style.SUCCESS(f'  OK Generated: {thumbnail_filename} ({img.width}x{img.height})')
                )
                success_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ERROR processing {pdf_filename}: {str(e)}')
                )
                error_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {success_count} thumbnails'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'{error_count} errors occurred'))

