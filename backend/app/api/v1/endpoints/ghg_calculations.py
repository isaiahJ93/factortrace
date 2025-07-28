from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.schemas.ghg_schemas import (
    CalculationRequest,
    CalculationResponse
)
from app.services.ghg_calculation_service import GHGCalculationService
from app.models.ghg_tables import GHGCalculationResult

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=CalculationResponse)
async def create_calculation(
    request: CalculationRequest,
    db: Session = Depends(get_db)
):
    """Submit a new GHG calculation request"""
    try:
        service = GHGCalculationService(db)
        result = await service.create_calculation(request)
        return result
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{calculation_id}")
async def get_calculation(
    calculation_id: str,  # Changed from UUID to str
    db: Session = Depends(get_db)
):
    """Get calculation results"""
    calc = db.query(GHGCalculationResult).filter(
        GHGCalculationResult.id == calculation_id
    ).first()
    
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    return {
        "calculation_id": calc.id,
        "status": calc.status,
        "total_emissions": calc.total_emissions,
        "organization_id": calc.organization_id,
        "created_at": calc.created_at,
        "completed_at": calc.completed_at
    }

@router.get("/")
async def list_calculations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List calculations"""
    calculations = db.query(GHGCalculationResult).offset(skip).limit(limit).all()
    
    return {
        "calculations": calculations,
        "total": db.query(GHGCalculationResult).count()
    }
