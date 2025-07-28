"""Generation endpoints for reports and documents"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from datetime import date

router = APIRouter()


class ReportGenerationRequest(BaseModel):
    """Request model for report generation"""
    report_type: str
    start_date: date
    end_date: date
    include_scope3: bool = True
    format: str = "pdf"


@router.post("/report")
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate compliance reports asynchronously"""
    # Add to background tasks
    background_tasks.add_task(
        generate_report_task,
        request.report_type,
        request.start_date,
        request.end_date,
    )
    
    return {
        "status": "generation_started",
        "report_type": request.report_type,
        "estimated_time": "5-10 minutes",
    }


async def generate_report_task(report_type: str, start_date: date, end_date: date):
    """Background task for report generation"""
    # Placeholder for actual report generation logic
    pass


@router.post("/ixbrl")
async def generate_ixbrl_document(voucher_id: str):
    """Generate iXBRL document for a voucher"""
    # Deferred import to avoid circular dependencies
    try:
        from generator.xhtml_generator import generate_ixbrl
        
        # Generate in background or return path
        output_path = f"output/ixbrl_{voucher_id}.xhtml"
        
        # In production, this would be async/queued
        return {
            "status": "generation_queued",
            "voucher_id": voucher_id,
            "output_path": output_path,
        }
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="iXBRL generator not available",
        )
