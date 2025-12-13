# app/services/pdf_report_service.py
"""
PDF Report Generation Service.

Generates compliance reports in PDF format with:
- Company information
- Emissions summary (Scope 1, 2, 3)
- Breakdown tables
- QR code for verification
- Signature metadata

Uses ReportLab for PDF generation.
See docs/features/verification-layer.md for verification integration.
"""
import io
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.wizard import ComplianceWizardSession
from app.services.crypto_service import generate_verification_qr

logger = logging.getLogger(__name__)


# =============================================================================
# STYLES
# =============================================================================

def _get_custom_styles():
    """Get custom paragraph styles for the report."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor("#1a1a2e"),
        alignment=TA_CENTER,
    ))

    # Subtitle style
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.HexColor("#4a4a68"),
        alignment=TA_CENTER,
    ))

    # Section header
    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor("#1a1a2e"),
    ))

    # Body text
    styles.add(ParagraphStyle(
        name="BodyText",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=8,
        textColor=colors.HexColor("#333333"),
    ))

    # Footer text
    styles.add(ParagraphStyle(
        name="FooterText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
    ))

    # Verification badge
    styles.add(ParagraphStyle(
        name="VerifiedBadge",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#2e7d32"),
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))

    return styles


# =============================================================================
# TABLE HELPERS
# =============================================================================

def _create_table_style() -> TableStyle:
    """Create standard table style for report tables."""
    return TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),

        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),

        # Alternating row colors
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),

        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ])


def _create_summary_table(emissions: Dict[str, Any]) -> Table:
    """Create emissions summary table."""
    data = [
        ["Scope", "Emissions (tCO₂e)", "% of Total"],
        ["Scope 1 (Direct)", f"{emissions.get('scope1_tco2e', 0):.2f}", ""],
        ["Scope 2 (Indirect)", f"{emissions.get('scope2_tco2e', 0):.2f}", ""],
        ["Scope 3 (Value Chain)", f"{emissions.get('scope3_tco2e', 0):.2f}", ""],
        ["Total", f"{emissions.get('total_tco2e', 0):.2f}", "100%"],
    ]

    # Calculate percentages
    total = emissions.get("total_tco2e", 0) or 1  # Avoid division by zero
    for i, scope_key in enumerate(["scope1_tco2e", "scope2_tco2e", "scope3_tco2e"], start=1):
        scope_val = emissions.get(scope_key, 0)
        pct = (scope_val / total) * 100 if total > 0 else 0
        data[i][2] = f"{pct:.1f}%"

    table = Table(data, colWidths=[8*cm, 5*cm, 4*cm])
    table.setStyle(_create_table_style())

    # Bold the total row
    table.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8e8e8")),
    ]))

    return table


def _create_breakdown_table(breakdown: list) -> Table:
    """Create detailed emissions breakdown table."""
    if not breakdown:
        return None

    data = [
        ["Category", "Activity", "Factor", "Emissions (tCO₂e)"],
    ]

    for item in breakdown:
        data.append([
            item.get("category", "Unknown"),
            f"{item.get('activity_value', 0):.2f} {item.get('activity_unit', '')}",
            f"{item.get('emission_factor', 0):.4f} {item.get('factor_unit', '')}",
            f"{item.get('emissions_tco2e', 0):.4f}",
        ])

    table = Table(data, colWidths=[5*cm, 4*cm, 5*cm, 3*cm])
    table.setStyle(_create_table_style())

    return table


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_compliance_pdf(
    session: ComplianceWizardSession,
    include_qr_code: bool = True,
) -> bytes:
    """
    Generate a compliance report PDF from a wizard session.

    Args:
        session: Completed wizard session with emissions data
        include_qr_code: Whether to include verification QR code

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = _get_custom_styles()
    story = []

    # Extract data
    company = session.company_profile or {}
    emissions = session.calculated_emissions or {}
    breakdown = emissions.get("breakdown", [])

    company_name = company.get("name", company.get("company_name", "Unknown Company"))
    country = company.get("country", "N/A")
    industry = company.get("industry_nace", company.get("industry", "N/A"))
    reporting_year = company.get("reporting_year", datetime.now().year)

    # ==========================================================================
    # COVER PAGE / HEADER
    # ==========================================================================

    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("CSRD Compliance Report", styles["ReportTitle"]))
    story.append(Paragraph("Scope 3 Emissions Summary", styles["ReportSubtitle"]))
    story.append(Spacer(1, 1*cm))

    # Company info
    story.append(Paragraph(f"<b>{company_name}</b>", styles["BodyText"]))
    story.append(Paragraph(f"Country: {country}", styles["BodyText"]))
    story.append(Paragraph(f"Industry: {industry}", styles["BodyText"]))
    story.append(Paragraph(f"Reporting Year: {reporting_year}", styles["BodyText"]))
    story.append(Spacer(1, 1*cm))

    # Report metadata
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Report Generated: {generated_at}", styles["BodyText"]))
    story.append(Paragraph(f"Report ID: {session.id}", styles["BodyText"]))

    # ==========================================================================
    # VERIFICATION SECTION
    # ==========================================================================

    if session.signature and include_qr_code:
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Verification", styles["SectionHeader"]))

        # Verification badge
        story.append(Paragraph(
            "✓ DIGITALLY SIGNED",
            styles["VerifiedBadge"]
        ))

        # QR Code
        try:
            qr_bytes = generate_verification_qr(str(session.id))
            qr_image = Image(io.BytesIO(qr_bytes), width=3*cm, height=3*cm)
            story.append(qr_image)
        except Exception as e:
            logger.warning(f"Failed to generate QR code for PDF: {e}")

        # Verification details
        story.append(Paragraph(
            f"Signed: {session.signed_at.strftime('%Y-%m-%d %H:%M UTC') if session.signed_at else 'N/A'}",
            styles["BodyText"]
        ))
        story.append(Paragraph(
            f"Hash: {session.report_hash[:16]}...{session.report_hash[-8:] if session.report_hash else 'N/A'}",
            styles["BodyText"]
        ))
        if session.verification_url:
            story.append(Paragraph(
                f"Verify: {session.verification_url}",
                styles["BodyText"]
            ))

    story.append(Spacer(1, 1*cm))

    # ==========================================================================
    # EMISSIONS SUMMARY
    # ==========================================================================

    story.append(Paragraph("Emissions Summary", styles["SectionHeader"]))
    story.append(_create_summary_table(emissions))
    story.append(Spacer(1, 0.5*cm))

    # Methodology note
    methodology = emissions.get("methodology_notes", "")
    if methodology:
        story.append(Paragraph(
            f"<i>Methodology: {methodology}</i>",
            styles["BodyText"]
        ))

    # ==========================================================================
    # DETAILED BREAKDOWN
    # ==========================================================================

    if breakdown:
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Detailed Breakdown", styles["SectionHeader"]))

        breakdown_table = _create_breakdown_table(breakdown)
        if breakdown_table:
            story.append(breakdown_table)

    # ==========================================================================
    # FOOTER / DISCLAIMER
    # ==========================================================================

    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        "This report has been generated by FactorTrace using DEFRA 2024 and EXIOBASE 2020 emission factors. "
        "The calculations are based on activity data provided by the reporting company. "
        "For regulatory filing, please ensure compliance with applicable CSRD/ESRS requirements.",
        styles["FooterText"]
    ))

    if session.signature:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            "This report is digitally signed and can be verified at the URL above or by scanning the QR code.",
            styles["FooterText"]
        ))

    # Build PDF
    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "generate_compliance_pdf",
]
