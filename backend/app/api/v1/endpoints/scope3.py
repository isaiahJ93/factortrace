# backend/app/api/v1/endpoints/scope3.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal

from app.api import deps
from app.models.user import User
from app.models.emission import Emission
from app.services.emissions_calculator import (
    calculate_scope3_emissions,
    EliteEmissionsCalculator,
    CalculationContext,
    GWPVersionEnum
)

router = APIRouter()

class ActivityDataItem(BaseModel):
    factor_name: str
    quantity: float
    unit: str
    calculation_method: str = "activity_based"
    region: str = None
    allocation_factor: float = 1.0

class Scope3CalculationRequest(BaseModel):
    category: str
    activity_data: List[ActivityDataItem]
    reporting_period: str

class MaterialityAssessmentRequest(BaseModel):
    sector: str
    total_emissions: float = None
    category_emissions: Dict[str, float] = None

@router.post("/calculate/{category}")
async def calculate_category_emissions(
    category: str,
    request: Scope3CalculationRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Calculate Scope 3 emissions for a specific category"""
    try:
        # Convert request data
        activity_data = [
            {
                "factor_name": item.factor_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "calculation_method": item.calculation_method,
                "region": item.region,
                "allocation_factor": item.allocation_factor
            }
            for item in request.activity_data
        ]
        
        # Calculate emissions
        result = calculate_scope3_emissions(
            category=category,
            activity_data=activity_data,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            db_session=db
        )
        
        # Save to database
        emission = Emission(
            organization_id=current_user.organization_id,
            scope=3,
            category=category,
            activity_type=f"Scope 3 - {result.scope3_category_name}",
            activity_data=sum(item.quantity for item in request.activity_data),
            activity_unit="mixed",
            co2e_total=float(result.emissions_tco2e),
            calculation_method=result.calculation_method.value,
            data_quality_score=result.data_quality.overall_score,
            uncertainty_percentage=float(result.uncertainty_percent),
            reporting_period=request.reporting_period,
            calculation_metadata={
                "calculation_hash": result.calculation_hash,
                "confidence_interval": {
                    "lower": float(result.confidence_interval_lower),
                    "upper": float(result.confidence_interval_upper)
                },
                "esrs_requirements": result.esrs_mapping,
                "cdp_questions": result.cdp_mapping
            },
            created_by=current_user.id
        )
        db.add(emission)
        db.commit()
        
        return {
            "id": emission.id,
            "emissions_tco2e": float(result.emissions_tco2e),
            "uncertainty_percent": float(result.uncertainty_percent),
            "confidence_interval": {
                "lower": float(result.confidence_interval_lower),
                "upper": float(result.confidence_interval_upper)
            },
            "data_quality_score": result.data_quality.overall_score,
            "calculation_hash": result.calculation_hash,
            "esrs_requirements": result.esrs_mapping,
            "cdp_questions": result.cdp_mapping
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/materiality-assessment")
async def assess_materiality(
    request: MaterialityAssessmentRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Assess materiality of Scope 3 categories"""
    context = CalculationContext(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        gwp_version=GWPVersionEnum.AR6_100
    )
    
    calculator = EliteEmissionsCalculator(context, db_session=db)
    
    # Convert emissions data
    total_emissions = Decimal(str(request.total_emissions)) if request.total_emissions else None
    category_emissions = {
        k: Decimal(str(v)) 
        for k, v in request.category_emissions.items()
    } if request.category_emissions else None
    
    assessments = calculator.assess_scope3_materiality(
        sector=request.sector,
        total_emissions=total_emissions,
        category_emissions=category_emissions
    )
    
    return {
        "sector": request.sector,
        "assessments": [
            {
                "category": a.category,
                "category_name": a.category_name,
                "is_material": a.is_material,
                "threshold_percentage": float(a.threshold_percentage),
                "actual_percentage": float(a.actual_percentage) if a.actual_percentage else None,
                "reasons": a.reasons,
                "recommendations": a.recommendations,
                "data_availability": a.data_availability
            }
            for a in assessments
        ]
    }

@router.get("/emission-factors/{category}")
async def get_category_factors(
    category: str,
    calculation_method: str = None,
    region: str = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get available emission factors for a category"""
    from app.models.emission_factor import EmissionFactor
    
    query = db.query(EmissionFactor).filter(
        EmissionFactor.scope == 3,
        EmissionFactor.scope3_category == category,
        EmissionFactor.is_active == True
    )
    
    if calculation_method:
        query = query.filter(EmissionFactor.calculation_method == calculation_method)
    
    if region:
        query = query.filter(EmissionFactor.region == region)
    
    factors = query.all()
    
    return {
        "category": category,
        "factors": [
            {
                "id": f.id,
                "name": f.name,
                "factor": f.factor,
                "unit": f.unit,
                "calculation_method": f.calculation_method,
                "region": f.region,
                "uncertainty_percentage": f.uncertainty_percentage,
                "data_quality_score": f.data_quality_score,
                "source": f.source
            }
            for f in factors
        ]
    }

@router.get("/compliance-report/{standard}")
async def generate_compliance_report(
    standard: str,
    reporting_period: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Generate compliance report for specified standard"""
    # Get all emissions for the period
    emissions = db.query(Emission).filter(
        Emission.organization_id == current_user.organization_id,
        Emission.reporting_period == reporting_period
    ).all()
    
    # Group by category
    emissions_by_category = {}
    for e in emissions:
        if e.category:
            if e.category not in emissions_by_category:
                emissions_by_category[e.category] = Decimal("0")
            emissions_by_category[e.category] += Decimal(str(e.co2e_total))
    
    # Generate report
    context = CalculationContext(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        gwp_version=GWPVersionEnum.AR6_100
    )
    
    calculator = EliteEmissionsCalculator(context, db_session=db)
    report = calculator.generate_compliance_report(
        standard=standard,
        emissions_by_category=emissions_by_category,
        reporting_period=reporting_period
    )
    
    return {
        "standard": report.standard,
        "reporting_period": report.reporting_period,
        "total_emissions": float(report.total_emissions),
        "scope_breakdown": {k: float(v) for k, v in report.scope_breakdown.items()},
        "compliance_status": report.compliance_status,
        "completeness_percentage": float(report.completeness_percentage),
        "data_quality_score": float(report.data_quality_score),
        "requirements_met": report.requirements_met,
        "requirements_pending": report.requirements_pending,
        "priority_actions": report.priority_actions,
        "improvement_areas": report.improvement_areas
    }