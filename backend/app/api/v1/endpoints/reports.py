# app/api/v1/endpoints/reports.py
"""
CSRD/ESRS Report Generation Endpoints
======================================
Endpoints for generating CSRD-compliant reports with iXBRL tags.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report import (
    CSRDSummaryRequest,
    CSRDSummaryResponse,
    ReportError,
)
from app.services.reports import generate_csrd_summary

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
) -> CSRDSummaryResponse:
    """
    Generate a CSRD-style summary report.

    Aggregates emissions data from the database and generates an XHTML document
    with embedded iXBRL tags conforming to ESRS E1 disclosure requirements.
    """
    try:
        return generate_csrd_summary(db, request)
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
):
    """
    Generate and return the CSRD report as a downloadable XHTML file.

    The file can be opened in any browser and contains valid iXBRL markup
    for regulatory submission.
    """
    try:
        report = generate_csrd_summary(db, request)

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
