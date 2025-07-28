from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.ghg_schemas import EmissionFactorQuery

router = APIRouter()

@router.get("/")
async def get_emission_factors(
    query: EmissionFactorQuery = Depends(),
    db: Session = Depends(get_db)
):
    """Get emission factors"""
    return {
        "factors": [],
        "total": 0,
        "limit": query.limit,
        "offset": query.offset
    }

@router.get("/providers")
async def get_providers():
    """Get available emission factor providers"""
    return {
        "providers": ["EPA", "DEFRA", "ADEME", "Custom"]
    }
