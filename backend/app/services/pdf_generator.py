# app/services/pdf_generator.py
"""
PDF Generator Service
=====================
Converts XHTML reports to professionally formatted PDF documents.

Uses WeasyPrint for HTML-to-PDF conversion with support for:
- CSS styling
- Page headers/footers
- Professional formatting
- Company branding placeholders
"""
from typing import Optional, Dict, Any
from datetime import datetime
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class PDFGeneratorError(Exception):
    """Raised when PDF generation fails."""
    pass


class PDFGenerator:
    """
    Generates PDF documents from XHTML content.

    Uses WeasyPrint for high-quality HTML-to-PDF rendering.
    Falls back to a simple HTML wrapper if WeasyPrint is unavailable.
    """

    def __init__(
        self,
        company_name: Optional[str] = None,
        company_logo_url: Optional[str] = None,
        include_page_numbers: bool = True,
        include_header: bool = True,
        include_footer: bool = True,
    ):
        self.company_name = company_name
        self.company_logo_url = company_logo_url
        self.include_page_numbers = include_page_numbers
        self.include_header = include_header
        self.include_footer = include_footer
        self._weasyprint_available = self._check_weasyprint()

    def _check_weasyprint(self) -> bool:
        """Check if WeasyPrint is available."""
        try:
            import weasyprint
            return True
        except ImportError:
            logger.warning(
                "WeasyPrint not available. PDF generation will use fallback mode. "
                "Install with: pip install weasyprint"
            )
            return False

    def generate_pdf(
        self,
        xhtml_content: str,
        title: Optional[str] = None,
        add_print_styles: bool = True,
    ) -> bytes:
        """
        Generate PDF from XHTML content.

        Args:
            xhtml_content: XHTML string (with or without iXBRL tags)
            title: Document title for PDF metadata
            add_print_styles: Add print-optimized CSS

        Returns:
            PDF document as bytes

        Raises:
            PDFGeneratorError: If PDF generation fails
        """
        if not self._weasyprint_available:
            return self._fallback_pdf(xhtml_content, title)

        try:
            import weasyprint

            # Add print styles if requested
            if add_print_styles:
                xhtml_content = self._inject_print_styles(xhtml_content)

            # Add header/footer CSS for paged media
            if self.include_header or self.include_footer:
                xhtml_content = self._inject_page_margin_content(xhtml_content)

            # Generate PDF
            html = weasyprint.HTML(string=xhtml_content)
            pdf_bytes = html.write_pdf()

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise PDFGeneratorError(f"Failed to generate PDF: {e}")

    def _inject_print_styles(self, xhtml_content: str) -> str:
        """Inject print-optimized CSS into XHTML."""
        print_css = """
        @media print {
            body {
                font-size: 10pt;
                line-height: 1.4;
                color: #000;
                background: #fff;
            }
            h1 { font-size: 18pt; page-break-after: avoid; }
            h2 { font-size: 14pt; page-break-after: avoid; }
            h3 { font-size: 12pt; page-break-after: avoid; }
            table { page-break-inside: avoid; }
            .metadata { font-size: 8pt; }
            a { color: #000; text-decoration: none; }
        }
        @page {
            size: A4;
            margin: 2cm 1.5cm;
        }
        """

        # Insert before </style> or before </head>
        if "</style>" in xhtml_content:
            xhtml_content = xhtml_content.replace("</style>", f"{print_css}</style>")
        elif "</head>" in xhtml_content:
            xhtml_content = xhtml_content.replace(
                "</head>",
                f"<style>{print_css}</style></head>"
            )

        return xhtml_content

    def _inject_page_margin_content(self, xhtml_content: str) -> str:
        """Inject CSS for page headers and footers."""
        margin_css = []

        if self.include_header:
            header_content = self.company_name or "FactorTrace Report"
            margin_css.append(f"""
            @page {{
                @top-center {{
                    content: "{header_content}";
                    font-size: 9pt;
                    color: #666;
                }}
            }}
            """)

        if self.include_footer:
            footer_parts = []
            if self.include_page_numbers:
                footer_parts.append("Page " + "counter(page)" + " of " + "counter(pages)")

            margin_css.append(f"""
            @page {{
                @bottom-center {{
                    content: "Generated by FactorTrace - {datetime.utcnow().strftime('%Y-%m-%d')}";
                    font-size: 8pt;
                    color: #999;
                }}
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 8pt;
                    color: #999;
                }}
            }}
            """)

        if margin_css:
            combined_css = "\n".join(margin_css)
            if "</style>" in xhtml_content:
                xhtml_content = xhtml_content.replace("</style>", f"{combined_css}</style>")
            elif "</head>" in xhtml_content:
                xhtml_content = xhtml_content.replace(
                    "</head>",
                    f"<style>{combined_css}</style></head>"
                )

        return xhtml_content

    def _fallback_pdf(self, xhtml_content: str, title: Optional[str]) -> bytes:
        """
        Fallback when WeasyPrint is unavailable.

        Returns a basic PDF-like HTML document that can be printed.
        In production, this should be replaced with an alternative PDF library.
        """
        # Try using reportlab as fallback
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            import re

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            styles = getSampleStyleSheet()
            story = []

            # Add title
            if title:
                story.append(Paragraph(title, styles['Title']))
                story.append(Spacer(1, 0.5*cm))

            # Extract text content from HTML (basic extraction)
            # Remove script and style tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', xhtml_content, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            # Remove XML/HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Clean up whitespace
            text = ' '.join(text.split())

            # Split into paragraphs
            paragraphs = text.split('\n\n')
            for para in paragraphs[:50]:  # Limit to first 50 paragraphs
                if para.strip():
                    story.append(Paragraph(para.strip()[:1000], styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))

            doc.build(story)
            return buffer.getvalue()

        except ImportError:
            logger.warning("ReportLab not available either. Returning HTML as UTF-8 bytes.")
            # Ultimate fallback: return HTML as bytes
            return xhtml_content.encode('utf-8')


def generate_pdf_from_xhtml(
    xhtml_content: str,
    title: Optional[str] = None,
    company_name: Optional[str] = None,
    include_page_numbers: bool = True,
) -> bytes:
    """
    Convenience function to generate PDF from XHTML.

    Args:
        xhtml_content: XHTML string
        title: Document title
        company_name: Company name for header
        include_page_numbers: Include page numbers

    Returns:
        PDF document as bytes
    """
    generator = PDFGenerator(
        company_name=company_name,
        include_page_numbers=include_page_numbers,
    )
    return generator.generate_pdf(xhtml_content, title=title)


def generate_csrd_pdf(
    report_data: Dict[str, Any],
    xhtml_content: str,
) -> bytes:
    """
    Generate PDF specifically for CSRD reports.

    Args:
        report_data: CSRD report data dict
        xhtml_content: XHTML content from report service

    Returns:
        PDF document as bytes
    """
    organization = report_data.get("report_data", {}).get("organization_name", "Organization")
    year = report_data.get("report_data", {}).get("reporting_year", datetime.now().year)

    generator = PDFGenerator(
        company_name=organization,
        include_page_numbers=True,
        include_header=True,
        include_footer=True,
    )

    return generator.generate_pdf(
        xhtml_content,
        title=f"ESRS E1 Climate Disclosure - {organization} - {year}",
    )


def generate_cbam_pdf(
    declaration_data: Dict[str, Any],
    lines_data: list,
) -> bytes:
    """
    Generate PDF for CBAM declaration.

    Args:
        declaration_data: CBAM declaration data
        lines_data: List of declaration line items

    Returns:
        PDF document as bytes
    """
    # Build XHTML for CBAM declaration
    from xml.sax.saxutils import escape as xml_escape

    declaration_ref = declaration_data.get("declaration_reference", "N/A")
    importer_name = declaration_data.get("importer_name", "N/A")
    period_start = declaration_data.get("period_start", "N/A")
    period_end = declaration_data.get("period_end", "N/A")
    total_emissions = declaration_data.get("total_embedded_emissions_tco2e", 0)
    total_quantity = declaration_data.get("total_quantity", 0)
    status = declaration_data.get("status", "draft")

    # Build line items table
    line_rows = []
    for line in lines_data:
        line_rows.append(f"""
            <tr>
                <td>{xml_escape(str(line.get('cn_code', 'N/A')))}</td>
                <td>{xml_escape(str(line.get('product_description', 'N/A')[:50]))}</td>
                <td>{xml_escape(str(line.get('country_of_origin', 'N/A')))}</td>
                <td class="numeric">{line.get('quantity', 0):,.2f}</td>
                <td class="numeric">{line.get('embedded_emissions_tco2e', 0):,.4f}</td>
            </tr>
        """)

    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>CBAM Declaration - {xml_escape(declaration_ref)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; }}
        h1 {{ color: #1a365d; border-bottom: 2px solid #2b6cb0; padding-bottom: 0.5rem; }}
        h2 {{ color: #2c5282; margin-top: 2rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #2c5282; color: white; }}
        .numeric {{ text-align: right; font-family: monospace; }}
        .total {{ font-weight: bold; background-color: #ebf8ff; }}
        .status {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem; }}
        .status-draft {{ background-color: #fef3cd; color: #856404; }}
        .status-submitted {{ background-color: #d4edda; color: #155724; }}
        .metadata {{ color: #718096; font-size: 0.875rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    <h1>CBAM Declaration Report</h1>

    <section id="declaration-info">
        <h2>Declaration Information</h2>
        <table>
            <tbody>
                <tr>
                    <td><strong>Declaration Reference</strong></td>
                    <td>{xml_escape(declaration_ref)}</td>
                </tr>
                <tr>
                    <td><strong>Importer</strong></td>
                    <td>{xml_escape(importer_name)}</td>
                </tr>
                <tr>
                    <td><strong>Reporting Period</strong></td>
                    <td>{xml_escape(str(period_start))} to {xml_escape(str(period_end))}</td>
                </tr>
                <tr>
                    <td><strong>Status</strong></td>
                    <td><span class="status status-{status}">{status.upper()}</span></td>
                </tr>
            </tbody>
        </table>
    </section>

    <section id="summary">
        <h2>Emissions Summary</h2>
        <table>
            <tbody>
                <tr>
                    <td><strong>Total Quantity</strong></td>
                    <td class="numeric">{total_quantity:,.2f} tonnes</td>
                </tr>
                <tr class="total">
                    <td><strong>Total Embedded Emissions</strong></td>
                    <td class="numeric">{total_emissions:,.4f} tCO2e</td>
                </tr>
            </tbody>
        </table>
    </section>

    <section id="line-items">
        <h2>Declaration Line Items</h2>
        <table>
            <thead>
                <tr>
                    <th>CN Code</th>
                    <th>Product</th>
                    <th>Origin</th>
                    <th class="numeric">Quantity (t)</th>
                    <th class="numeric">Emissions (tCO2e)</th>
                </tr>
            </thead>
            <tbody>
                {''.join(line_rows) if line_rows else '<tr><td colspan="5">No line items</td></tr>'}
            </tbody>
        </table>
    </section>

    <footer class="metadata">
        <p>Generated by FactorTrace on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p>This document is for CBAM declaration purposes under EU Regulation 2023/956.</p>
    </footer>
</body>
</html>"""

    generator = PDFGenerator(
        company_name=importer_name,
        include_page_numbers=True,
    )

    return generator.generate_pdf(xhtml, title=f"CBAM Declaration - {declaration_ref}")
