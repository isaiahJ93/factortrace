from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.schemas.ghg_schemas import (
    CalculationRequest,
    CalculationResponse,
    CategoryCalculationResponse
)
from app.services.ghg_calculation_service import GHGCalculationService
from app.models.ghg_tables import GHGCalculationResult

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=CalculationResponse)
async def create_calculation(
    request: CalculationRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Submit a new GHG calculation request"""
    service = GHGCalculationService(db)
    
    try:
        logger.info(f"Creating calculation for org: {request.organization_id}")
        result = await service.create_calculation(request)
        logger.info(f"Calculation created successfully: {result.calculation_id}")
        return result
    except Exception as e:
        logger.error(f"Error creating calculation: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{calculation_id}")
async def get_calculation(
    calculation_id: UUID,
    db: Session = Depends(get_db)
):
    """Get calculation results"""
    service = GHGCalculationService(db)
    
    calculation = await service.get_calculation(calculation_id)
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    return {
        "calculation_id": calculation.id,
        "status": calculation.status,
        "total_emissions": calculation.total_emissions,
        "organization_id": calculation.organization_id,
        "reporting_period": {
            "start": calculation.reporting_period_start,
            "end": calculation.reporting_period_end
        },
        "created_at": calculation.created_at,
        "completed_at": calculation.completed_at
    }

@router.get("/")
async def list_calculations(
    organization_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List calculations"""
    query = db.query(GHGCalculationResult)
    
    if organization_id:
        query = query.filter(GHGCalculationResult.organization_id == str(organization_id))
    
    calculations = query.offset(skip).limit(limit).all()
    
    return {
        "calculations": calculations,
        "total": query.count()
    }
