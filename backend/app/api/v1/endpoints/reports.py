# app/api/v1/endpoints/reports.py
"""
CSRD/ESRS Report Generation Endpoints
======================================
Endpoints for generating CSRD-compliant reports with iXBRL tags,
PDF exports, and CBAM declaration reports.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import date
from io import BytesIO
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.auth_schemas import CurrentUser
from app.schemas.report import (
    CSRDSummaryRequest,
    CSRDSummaryResponse,
    ReportError,
)
from app.services.reports import generate_csrd_summary, generate_esrs_e1_report
from app.services.pdf_generator import generate_csrd_pdf, generate_cbam_pdf
from app.services.cbam_report import (
    generate_cbam_declaration,
    export_cbam_declaration_csv,
    get_cbam_declaration_lines,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/csrd-summary",
    response_model=CSRDSummaryResponse,
    responses={
        200: {
            "description": "CSRD summary report generated successfully",
            "model": CSRDSummaryResponse,
        },
        422: {
            "description": "Validation error",
            "model": ReportError,
        },
    },
    summary="Generate CSRD Summary Report",
    description="""
Generate a CSRD-style ESRS E1 summary report with embedded iXBRL tags.

The report includes:
- **E1-6 Disclosure**: Gross Scopes 1, 2, 3 and Total GHG emissions
- **iXBRL Tags**: Machine-readable tags using ESRS taxonomy
- **Methodology Notes**: Optional notes on calculation methodology

The response includes both structured JSON data and the complete XHTML document
in the `xhtml_content` field.
""",
)
async def create_csrd_summary(
    request: CSRDSummaryRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CSRDSummaryResponse:
    """
    Generate a CSRD-style summary report.

    Aggregates emissions data from the database and generates an XHTML document
    with embedded iXBRL tags conforming to ESRS E1 disclosure requirements.

    MULTI-TENANT: Only includes emissions belonging to the current tenant.
    """
    try:
        return generate_csrd_summary(db, request, tenant_id=current_user.tenant_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "REPORT_GENERATION_FAILED",
                "message": str(e),
            },
        )


@router.post(
    "/csrd-summary/xhtml",
    response_class=Response,
    responses={
        200: {
            "description": "XHTML document with iXBRL tags",
            "content": {"application/xhtml+xml": {}},
        },
    },
    summary="Download CSRD Report as XHTML",
    description="Generate and download the CSRD report as a standalone XHTML file.",
)
async def download_csrd_xhtml(
    request: CSRDSummaryRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate and return the CSRD report as a downloadable XHTML file.

    The file can be opened in any browser and contains valid iXBRL markup
    for regulatory submission.

    MULTI-TENANT: Only includes emissions belonging to the current tenant.
    """
    try:
        report = generate_csrd_summary(db, request, tenant_id=current_user.tenant_id)

        # Generate filename
        filename = (
            f"esrs_e1_{request.organization_name.replace(' ', '_')}"
            f"_{request.reporting_year}.xhtml"
        )

        return Response(
            content=report.xhtml_content,
            media_type="application/xhtml+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "XHTML_GENERATION_FAILED",
                "message": str(e),
            },
        )


# =============================================================================
# ESRS E1 Full Report Endpoints (with data quality and Scope 3 breakdown)
# =============================================================================

@router.post(
    "/csrd/generate",
    summary="Generate Full ESRS E1 Report",
    description="""
Generate a comprehensive ESRS E1 report with:
- Data quality scoring
- Scope 3 category breakdown (15 GHG Protocol categories)
- Methodology disclosure (factor sources)
- XHTML with iXBRL tags
""",
)
async def generate_csrd_report(
    organization_name: str,
    reporting_year: int,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    lei: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate a full ESRS E1 report with data quality metrics and Scope 3 breakdown.

    MULTI-TENANT: Only includes emissions belonging to the current tenant.
    """
    try:
        # Set default period if not provided
        if not period_start:
            period_start = date(reporting_year, 1, 1)
        if not period_end:
            period_end = date(reporting_year, 12, 31)

        report_data = generate_esrs_e1_report(
            db=db,
            tenant_id=current_user.tenant_id,
            organization_name=organization_name,
            reporting_year=reporting_year,
            period_start=period_start,
            period_end=period_end,
            lei=lei,
        )

        return report_data

    except Exception as e:
        logger.error(f"CSRD report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "REPORT_GENERATION_FAILED",
                "message": str(e),
            },
        )


@router.get(
    "/csrd/{report_id}/download",
    summary="Download CSRD Report",
    description="Download a generated CSRD report in various formats.",
)
async def download_csrd_report(
    report_id: str,
    format: Literal["xhtml", "pdf", "json"] = Query(
        default="xhtml",
        description="Output format: xhtml (iXBRL), pdf, or json"
    ),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Download a CSRD report in the specified format.

    Note: This endpoint currently generates the report on-demand.
    In production, reports would be cached/stored by ID.

    MULTI-TENANT: Only allows download of reports belonging to the current tenant.
    """
    # For MVP, report_id is expected to be: "org_year" format
    # e.g., "acme_2024"
    try:
        parts = report_id.rsplit("_", 1)
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report_id format. Expected: organization_year"
            )

        org_name = parts[0].replace("_", " ")
        year = int(parts[1])

        # Generate the report
        report_data = generate_esrs_e1_report(
            db=db,
            tenant_id=current_user.tenant_id,
            organization_name=org_name,
            reporting_year=year,
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
        )

        if format == "json":
            return report_data

        elif format == "xhtml":
            xhtml_content = report_data.get("xhtml_content", "")
            if not xhtml_content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="XHTML content not generated"
                )

            filename = f"esrs_e1_{report_id}.xhtml"
            return Response(
                content=xhtml_content,
                media_type="application/xhtml+xml",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

        elif format == "pdf":
            xhtml_content = report_data.get("xhtml_content", "")
            if not xhtml_content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="XHTML content not generated for PDF conversion"
                )

            pdf_bytes = generate_csrd_pdf(report_data, xhtml_content)
            filename = f"esrs_e1_{report_id}.pdf"

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSRD report download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "REPORT_DOWNLOAD_FAILED",
                "message": str(e),
            },
        )


# =============================================================================
# CBAM Declaration Report Endpoints
# =============================================================================

@router.get(
    "/cbam/declarations/{declaration_id}",
    summary="Get CBAM Declaration Report",
    description="Get a comprehensive CBAM declaration report with breakdowns.",
)
async def get_cbam_declaration_report(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get a CBAM declaration report with:
    - Product breakdown by CN code
    - Country of origin breakdown
    - Sector breakdown
    - Total embedded emissions

    MULTI-TENANT: Only returns declaration belonging to the current tenant.
    """
    try:
        report = generate_cbam_declaration(
            db=db,
            tenant_id=current_user.tenant_id,
            declaration_id=declaration_id,
        )
        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"CBAM declaration report failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CBAM_REPORT_FAILED",
                "message": str(e),
            },
        )


@router.post(
    "/cbam/declarations/{declaration_id}/export",
    summary="Export CBAM Declaration",
    description="Export CBAM declaration in CSV or PDF format.",
)
async def export_cbam_declaration(
    declaration_id: int,
    format: Literal["csv", "pdf"] = Query(
        default="csv",
        description="Export format: csv or pdf"
    ),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Export a CBAM declaration for regulatory submission.

    - CSV: Suitable for data processing and submission systems
    - PDF: Human-readable report for review and archiving

    MULTI-TENANT: Only exports declaration belonging to the current tenant.
    """
    try:
        if format == "csv":
            csv_content = export_cbam_declaration_csv(
                db=db,
                tenant_id=current_user.tenant_id,
                declaration_id=declaration_id,
            )

            filename = f"cbam_declaration_{declaration_id}.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

        elif format == "pdf":
            # Get declaration data for PDF
            report = generate_cbam_declaration(
                db=db,
                tenant_id=current_user.tenant_id,
                declaration_id=declaration_id,
            )

            lines = get_cbam_declaration_lines(
                db=db,
                tenant_id=current_user.tenant_id,
                declaration_id=declaration_id,
            )

            pdf_bytes = generate_cbam_pdf(
                declaration_data=report.get("declaration", {}),
                lines_data=lines,
            )

            filename = f"cbam_declaration_{declaration_id}.pdf"
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"CBAM declaration export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CBAM_EXPORT_FAILED",
                "message": str(e),
            },
        )


@router.get(
    "/cbam/declarations/{declaration_id}/lines",
    summary="Get CBAM Declaration Line Items",
    description="Get all line items for a CBAM declaration.",
)
async def get_cbam_lines(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get all line items for a CBAM declaration.

    Returns detailed information about each imported product including:
    - CN code and description
    - Quantity and unit
    - Country of origin
    - Embedded emissions

    MULTI-TENANT: Only returns lines for declarations belonging to the current tenant.
    """
    try:
        lines = get_cbam_declaration_lines(
            db=db,
            tenant_id=current_user.tenant_id,
            declaration_id=declaration_id,
        )
        return {"declaration_id": declaration_id, "lines": lines, "count": len(lines)}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"CBAM lines fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CBAM_LINES_FAILED",
                "message": str(e),
            },
        )
