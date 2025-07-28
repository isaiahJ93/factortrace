# backend/app/api/v1/endpoints/emissions.py
"""
Enhanced Emissions endpoints for FactorTrace API
Handles CRUD operations, sophisticated emissions calculations, and evidence uploads
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import csv
import io
import json

# App imports - Fixed: removed duplicate deps import
from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.emission import Emission, EmissionScope
from app.models.user import User
from app.models.emission_factor import EmissionFactor
from app.models.evidence_document import EvidenceDocument
from app.schemas.emission import (
    EmissionCreate, 
    EmissionResponse, 
    EmissionsSummary,
    EmissionUpdate
)
from app.schemas.api_schemas import EmissionFactorInput

# Import data quality calculation
from app.api.v1.endpoints.data_quality import calculate_data_quality_score

# Import from emissions calculator
from app.services.emissions_calculator import (
    calculate_scope3_emissions,
    EliteEmissionsCalculator,
    CalculationContext,
    CalculationInput,
    calculate_emissions as calc_emissions,
    DataQualityIndicators,
    TierLevelEnum,
    CalculationMethodEnum,
    GWPVersionEnum
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx'}

# Constants - define these if they're not imported
SCOPE3_CATEGORIES = {
    "purchased_goods_services": {
        "id": 1,
        "display_name": "Purchased Goods and Services",
        "ghg_protocol_id": "3.1",
        "description": "Extraction, production, and transportation of goods and services purchased",
        "material_sectors": ["Manufacturing", "Retail", "Construction"],
        "calculation_guidance": "Use supplier-specific or average-data method"
    },
    "capital_goods": {
        "id": 2,
        "display_name": "Capital Goods",
        "ghg_protocol_id": "3.2",
        "description": "Extraction, production, and transportation of capital goods purchased",
        "material_sectors": ["All sectors"],
        "calculation_guidance": "Use supplier-specific or average-data method"
    },
    "fuel_energy_activities": {
        "id": 3,
        "display_name": "Fuel- and Energy-Related Activities",
        "ghg_protocol_id": "3.3",
        "description": "Extraction, production, and transportation of fuels and energy purchased",
        "material_sectors": ["All sectors"],
        "calculation_guidance": "Use average-data method"
    },
    "upstream_transportation": {
        "id": 4,
        "display_name": "Upstream Transportation and Distribution",
        "ghg_protocol_id": "3.4",
        "description": "Transportation and distribution of products purchased",
        "material_sectors": ["Manufacturing", "Retail"],
        "calculation_guidance": "Use distance-based or spend-based method"
    },
    "waste_operations": {
        "id": 5,
        "display_name": "Waste Generated in Operations",
        "ghg_protocol_id": "3.5",
        "description": "Disposal and treatment of waste generated",
        "material_sectors": ["All sectors"],
        "calculation_guidance": "Use waste-type-specific method"
    },
    "business_travel": {
        "id": 6,
        "display_name": "Business Travel",
        "ghg_protocol_id": "3.6",
        "description": "Transportation of employees for business-related activities",
        "material_sectors": ["All sectors"],
        "calculation_guidance": "Use distance-based method"
    },
    "employee_commuting": {
        "id": 7,
        "display_name": "Employee Commuting",
        "ghg_protocol_id": "3.7",
        "description": "Transportation of employees between homes and worksites",
        "material_sectors": ["All sectors"],
        "calculation_guidance": "Use average-data method"
    },
    "upstream_leased_assets": {
        "id": 8,
        "display_name": "Upstream Leased Assets",
        "ghg_protocol_id": "3.8",
        "description": "Operation of assets leased by the company",
        "material_sectors": ["All sectors"],
        "calculation_guidance": "Use asset-specific method"
    },
    "downstream_transportation": {
        "id": 9,
        "display_name": "Downstream Transportation and Distribution",
        "ghg_protocol_id": "3.9",
        "description": "Transportation and distribution of products sold",
        "material_sectors": ["Manufacturing", "Retail"],
        "calculation_guidance": "Use distance-based method"
    },
    "processing_sold_products": {
        "id": 10,
        "display_name": "Processing of Sold Products",
        "ghg_protocol_id": "3.10",
        "description": "Processing of intermediate products sold",
        "material_sectors": ["Manufacturing"],
        "calculation_guidance": "Use average-data method"
    },
    "use_of_sold_products": {
        "id": 11,
        "display_name": "Use of Sold Products",
        "ghg_protocol_id": "3.11",
        "description": "End use of goods and services sold",
        "material_sectors": ["Manufacturing", "Technology"],
        "calculation_guidance": "Use product lifetime method"
    },
    "end_of_life_treatment": {
        "id": 12,
        "display_name": "End-of-Life Treatment of Sold Products",
        "ghg_protocol_id": "3.12",
        "description": "Waste disposal and treatment of products sold",
        "material_sectors": ["Manufacturing"],
        "calculation_guidance": "Use waste-type-specific method"
    },
    "downstream_leased_assets": {
        "id": 13,
        "display_name": "Downstream Leased Assets",
        "ghg_protocol_id": "3.13",
        "description": "Operation of assets owned and leased to others",
        "material_sectors": ["Real Estate", "Finance"],
        "calculation_guidance": "Use asset-specific method"
    },
    "franchises": {
        "id": 14,
        "display_name": "Franchises",
        "ghg_protocol_id": "3.14",
        "description": "Operation of franchises",
        "material_sectors": ["Retail", "Hospitality"],
        "calculation_guidance": "Use franchise-specific method"
    },
    "investments": {
        "id": 15,
        "display_name": "Investments",
        "ghg_protocol_id": "3.15",
        "description": "Operation of investments",
        "material_sectors": ["Finance"],
        "calculation_guidance": "Use investment-specific method"
    }
}

# Pydantic models for request validation
class Scope3CalculationRequest(BaseModel):
    category: str
    activity_data: List[Dict[str, Any]]
    reporting_period: str

class MaterialityAssessmentRequest(BaseModel):
    sector: str
    annual_revenue: Optional[float] = None
    current_emissions: Optional[Dict[str, float]] = None

router = APIRouter()

# ===== EVIDENCE UPLOAD ENDPOINTS =====

def validate_file(file: UploadFile) -> bool:
    """Validate file type and size."""
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    return True


@router.get("/categories")
async def get_emission_categories(
    scope: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get emission categories - redirect to emission-factors endpoint"""
    # For now, return mock data to get the frontend working
    if scope == 3:
        return list(SCOPE3_CATEGORIES.keys())
    return ["Fuel & Energy Activities", "Transportation", "Waste", "Other"]

@router.get("/factors")
async def get_emission_factors(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get emission factors for a category"""
    # Mock data to get frontend working
    return [
        {"id": 1, "name": "Electricity", "unit": "kWh", "factor": 0.233},
        {"id": 2, "name": "Natural Gas", "unit": "m³", "factor": 2.02},
        {"id": 3, "name": "Diesel", "unit": "L", "factor": 2.68}
    ]


@router.post("/upload-evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    emission_id: int = Form(...),
    evidence_type: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload evidence document for an emission entry."""
    
    # Validate emission exists
    emission = db.query(Emission).filter(Emission.id == emission_id).first()
    if not emission:
        raise HTTPException(status_code=404, detail="Emission not found")
    
    # Validate file
    validate_file(file)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # Save file to local storage
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create evidence document record
        evidence_doc = EvidenceDocument(
            emission_id=emission_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_ext[1:],  # Remove the dot
            file_size=file.size,
            uploaded_at=datetime.utcnow(),
            evidence_type=evidence_type,
            description=description
        )
        db.add(evidence_doc)
        
        # Update emission with evidence info
        emission.evidence_type = evidence_type
        emission.document_url = f"/uploads/{unique_filename}"
        emission.quality_score = calculate_data_quality_score(emission)['total_score']
        
        db.commit()
        db.refresh(emission)
        
        # Return updated emission with quality scores
        quality_scores = calculate_data_quality_score(emission)
        
        return {
            "message": "Evidence uploaded successfully",
            "emission_id": emission_id,
            "evidence_document_id": evidence_doc.id,
            "filename": file.filename,
            "evidence_type": evidence_type,
            "quality_scores": quality_scores,
            "document_url": emission.document_url
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/evidence/{evidence_id}")
async def delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_db)
):
    """Delete evidence document."""
    evidence = db.query(EvidenceDocument).filter(EvidenceDocument.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence document not found")
    
    # Delete file from storage
    file_path = Path(evidence.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Update emission
    emission = db.query(Emission).filter(Emission.id == evidence.emission_id).first()
    if emission:
        emission.evidence_type = None
        emission.document_url = None
        emission.quality_score = calculate_data_quality_score(emission)['total_score']
    
    # Delete database record
    db.delete(evidence)
    db.commit()
    
    return {"message": "Evidence deleted successfully"}

# ===== EXISTING ENDPOINTS (Enhanced) =====

@router.get("/", response_model=List[EmissionResponse])
async def get_emissions(
    scope: Optional[int] = Query(None, ge=1, le=3),
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emissions with filtering, pagination, and quality scores"""
    query = db.query(Emission)
    
    if scope:
        query = query.filter(Emission.scope == scope)
    
    if category:
        query = query.filter(Emission.category == category)
    
    if start_date:
        query = query.filter(Emission.created_at >= start_date)
    
    if end_date:
        query = query.filter(Emission.created_at <= end_date)
    
    query = query.order_by(Emission.created_at.desc())
    emissions = query.offset(skip).limit(limit).all()
    
    # Enhance with quality scores
    results = []
    for emission in emissions:
        emission_dict = {
            "id": emission.id,
            "date": emission.created_at,
            "scope": emission.scope,
            "category": emission.category,
            "activity_type": emission.activity_type,
            "activity_data": emission.activity_data,
            "activity_unit": emission.activity_unit,
            "emission_factor_id": emission.emission_factor_id,
            "co2e_total": emission.co2e_total,
            "evidence_type": emission.evidence_type,
            "document_url": emission.document_url,
            "quality_score": emission.quality_score or calculate_data_quality_score(emission)['total_score'],
            "calculation_method": emission.calculation_method,
            "data_quality_score": emission.data_quality_score,
            "uncertainty_percentage": emission.uncertainty_percentage,
            "reporting_period": emission.reporting_period,
            "notes": emission.notes,
            "created_at": emission.created_at,
            "updated_at": emission.updated_at
        }
        results.append(emission_dict)
    
    return results

@router.get("/summary", response_model=EmissionsSummary)
async def get_emissions_summary(
    reporting_period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emissions summary with totals by scope and category"""
    query = db.query(Emission)
    
    if hasattr(current_user, 'organization_id'):
        pass
    
    if reporting_period:
        query = query.filter(Emission.reporting_period == reporting_period)
    
    # Calculate totals by scope
    scope1_total = query.filter(Emission.scope == 1).with_entities(
        func.sum(Emission.co2e_total)
    ).scalar() or 0
    
    scope2_total = query.filter(Emission.scope == 2).with_entities(
        func.sum(Emission.co2e_total)
    ).scalar() or 0
    
    scope3_total = query.filter(Emission.scope == 3).with_entities(
        func.sum(Emission.co2e_total)
    ).scalar() or 0
    
    # Get breakdown by category
    category_breakdown = {}
    categories = query.with_entities(
        Emission.category,
        func.sum(Emission.co2e_total).label('total')
    ).group_by(Emission.category).all()
    
    for cat, total in categories:
        if cat:
            category_breakdown[cat] = float(total or 0)
    
    return EmissionsSummary(
        total_emissions=float(scope1_total + scope2_total + scope3_total),
        scope1_emissions=float(scope1_total),
        scope2_emissions=float(scope2_total),
        scope3_emissions=float(scope3_total),
        by_category=category_breakdown
    )

# ===== NEW ENHANCED ENDPOINTS =====

@router.post("/calculate/advanced")
async def calculate_emissions_advanced(
    activity_data: List[Dict[str, Any]] = Body(..., example=[
        {
            "activity_amount": 1000,
            "activity_unit": "kWh",
            "emission_factor_id": "electricity_grid_us",
            "region": "US",
            "data_quality": {
                "temporal": 4,
                "geographical": 5,
                "technological": 4,
                "completeness": 5,
                "reliability": 4
            }
        }
    ]),
    calculation_options: Dict[str, Any] = Body(default={
        "uncertainty_method": "monte_carlo",
        "confidence_level": 95,
        "include_uncertainty": True
    }),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Advanced emissions calculation with uncertainty analysis
    
    Uses the sophisticated calculation engine with Monte Carlo simulation
    """
    try:
        # Create calculation context
        context = CalculationContext(
            user_id=str(current_user.id) if hasattr(current_user, 'id') else "anonymous",
            organization_id=str(current_user.organization_id) if hasattr(current_user, 'organization_id') else "default",
            gwp_version=GWPVersionEnum.AR6_100
        )
        
        # Create calculator
        calculator = EliteEmissionsCalculator(context, db_session=db)
        
        # Prepare calculation inputs
        calc_inputs = []
        for item in activity_data:
            # Get emission factor from database
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.name == item["emission_factor_id"],
                EmissionFactor.is_active == True
            ).first()
            
            if not factor:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Emission factor '{item['emission_factor_id']}' not found"
                )
            
            # Create emission factor input
            ef_input = EmissionFactorInput(
                factor_id=str(factor.id),
                value=Decimal(str(factor.factor)),
                unit=factor.unit,
                source=factor.source or "Database",
                source_year=factor.valid_from.year if factor.valid_from else datetime.now().year,
                tier=TierLevelEnum.TIER_2,
                uncertainty_percentage=Decimal(str(factor.uncertainty_percentage)) if factor.uncertainty_percentage else Decimal("15"),
                region=item.get("region"),
                scope3_category=factor.scope3_category,
                calculation_method=CalculationMethodEnum(factor.calculation_method) if factor.calculation_method else CalculationMethodEnum.ACTIVITY_BASED
            )
            
            # Create calculation input
            calc_input = CalculationInput(
                activity_data=Decimal(str(item["activity_amount"])),
                activity_unit=item["activity_unit"],
                emission_factor=ef_input,
                region=item.get("region"),
                data_quality_override=DataQualityIndicators(**item["data_quality"]) if "data_quality" in item else None
            )
            
            calc_inputs.append(calc_input)
        
        # Calculate emissions
        result = calculator.calculate_emissions(calc_inputs)
        
        # Return detailed results
        return {
            "calculation_id": result.calculation_id,
            "emissions_tco2e": float(result.emissions_tco2e),
            "uncertainty_percent": float(result.uncertainty_percent),
            "confidence_interval": {
                "lower": float(result.confidence_interval_lower),
                "upper": float(result.confidence_interval_upper),
                "confidence_level": float(context.confidence_level)
            },
            "percentiles": {
                "p5": float(result.percentile_5) if result.percentile_5 else None,
                "p25": float(result.percentile_25) if result.percentile_25 else None,
                "p75": float(result.percentile_75) if result.percentile_75 else None,
                "p95": float(result.percentile_95) if result.percentile_95 else None
            },
            "data_quality": {
                "overall_score": float(result.data_quality.overall_score),
                "dimensions": result.data_quality.dict()
            },
            "ghg_breakdown": [
                {
                    "gas_type": ghg.gas_type,
                    "amount": float(ghg.amount),
                    "unit": ghg.unit,
                    "gwp_factor": float(ghg.gwp_factor)
                }
                for ghg in result.ghg_breakdown
            ],
            "calculation_method": result.calculation_method,
            "tier_level": result.tier_level,
            "warnings": result.warnings
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/scope3/{category}")
async def calculate_scope3_category(
    category: str,
    activity_data: Dict[str, Dict[str, Any]] = Body(..., example={
        "steel": {"amount": 1000, "unit": "kg", "region": "EU"},
        "aluminum": {"amount": 500, "unit": "kg"}
    }),
    method: str = Query("activity_based", enum=["activity_based", "spend_based"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate emissions for a specific Scope 3 category
    
    Categories: purchased_goods_services, capital_goods, fuel_energy_activities,
    upstream_transportation, waste_operations, business_travel, employee_commuting,
    upstream_leased_assets, downstream_transportation, processing_sold_products,
    use_of_sold_products, end_of_life_treatment, downstream_leased_assets,
    franchises, investments
    """
    if category not in SCOPE3_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Scope 3 category. Valid categories: {list(SCOPE3_CATEGORIES.keys())}"
        )
    
    try:
        # Convert activity data to the format expected by calculate_scope3_emissions
        formatted_activity_data = []
        for name, data in activity_data.items():
            formatted_activity_data.append({
                "factor_name": name,
                "quantity": data["amount"],
                "unit": data["unit"],
                "calculation_method": method,
                "region": data.get("region")
            })
        
        result = calculate_scope3_emissions(
            category=category,
            activity_data=formatted_activity_data,
            user_id=str(current_user.id) if hasattr(current_user, 'id') else "anonymous",
            organization_id=str(current_user.organization_id) if hasattr(current_user, 'organization_id') else "default",
            db_session=db
        )
        
        return {
            "category": category,
            "category_name": SCOPE3_CATEGORIES[category]["display_name"],
            "emissions_tco2e": float(result.emissions_tco2e),
            "uncertainty_percent": float(result.uncertainty_percent),
            "confidence_interval": {
                "lower": float(result.confidence_interval_lower),
                "upper": float(result.confidence_interval_upper)
            },
            "calculation_method": method,
            "ghg_breakdown": [
                {
                    "gas_type": ghg.gas_type,
                    "amount": float(ghg.amount),
                    "unit": ghg.unit
                }
                for ghg in result.ghg_breakdown
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scope3/categories")
async def get_scope3_categories():
    """Get all Scope 3 categories with metadata"""
    return {
        category: {
            "id": info["id"],
            "display_name": info["display_name"],
            "ghg_protocol_id": info["ghg_protocol_id"],
            "description": info["description"],
            "material_sectors": info["material_sectors"],
            "calculation_guidance": info["calculation_guidance"]
        }
        for category, info in SCOPE3_CATEGORIES.items()
    }

@router.post("/materiality/assess")
async def assess_materiality(
    request: MaterialityAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assess materiality of Scope 3 categories for your sector
    
    Helps identify which categories should be prioritized for calculation
    """
    context = CalculationContext(
        user_id=str(current_user.id) if hasattr(current_user, 'id') else "anonymous",
        organization_id=str(current_user.organization_id) if hasattr(current_user, 'organization_id') else "default",
        gwp_version=GWPVersionEnum.AR6_100
    )
    
    calculator = EliteEmissionsCalculator(context, db_session=db)
    
    total_emissions = sum(request.current_emissions.values()) if request.current_emissions else None
    
    assessments = calculator.assess_scope3_materiality(
        sector=request.sector,
        total_emissions=Decimal(str(total_emissions)) if total_emissions else None,
        category_emissions={
            cat: Decimal(str(val)) 
            for cat, val in (request.current_emissions or {}).items()
        }
    )
    
    return {
        "sector": request.sector,
        "assessments": [
            {
                "category": assessment.category,
                "category_name": assessment.category_name,
                "is_material": assessment.is_material,
                "emissions_tco2e": float(assessment.emissions_tco2e) if assessment.emissions_tco2e else None,
                "percentage_of_total": float(assessment.percentage_of_total) if assessment.percentage_of_total else None,
                "threshold_percentage": float(assessment.threshold_percentage),
                "reasons": assessment.reasons,
                "recommendations": assessment.recommendations,
                "data_availability": assessment.data_availability,
                "calculation_feasibility": assessment.calculation_feasibility
            }
            for assessment in assessments
        ]
    }

@router.post("/emissions/scope3/calculate")
async def calculate_scope3(
    request: Scope3CalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate Scope 3 emissions for a specific category"""
    try:
        result = calculate_scope3_emissions(
            category=request.category,
            activity_data=request.activity_data,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            db_session=db
        )
        
        # Save to database
        emission_entry = Emission(
            organization_id=current_user.organization_id,
            scope=3,
            category=request.category,
            activity_type=f"Scope 3 - {request.category}",
            activity_data=request.activity_data[0]["quantity"],
            activity_unit=request.activity_data[0]["unit"],
            emission_factor_id=None,  # Multiple factors used
            co2e_total=float(result.emissions_tco2e),
            calculation_method=result.calculation_method.value,
            data_quality_score=result.data_quality.overall_score,
            uncertainty_percentage=float(result.uncertainty_percent),
            reporting_period=request.reporting_period,
            created_by=current_user.id
        )
        db.add(emission_entry)
        db.commit()
        
        return {
            "success": True,
            "emission_id": emission_entry.id,
            "emissions_tco2e": float(result.emissions_tco2e),
            "uncertainty_percent": float(result.uncertainty_percent),
            "confidence_interval": {
                "lower": float(result.confidence_interval_lower),
                "upper": float(result.confidence_interval_upper)
            },
            "data_quality_score": result.data_quality.overall_score,
            "calculation_hash": result.calculation_hash
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reports/compliance")
async def generate_compliance_report(
    standard: str = Query(..., enum=["ESRS", "CDP", "TCFD", "SBTi"]),
    reporting_period: str = Query(str(datetime.now().year)),
    emissions_by_category: Dict[str, float] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate compliance report for specific standard (ESRS, CDP, TCFD, SBTi)
    """
    # If emissions not provided, fetch from database
    if not emissions_by_category:
        emissions = db.query(Emission).filter(
            # Emission.organization_id == current_user.organization_id,
            Emission.reporting_period == reporting_period
        ).all()
        
        emissions_by_category = {}
        for emission in emissions:
            if emission.category:
                pass
                if emission.category not in emissions_by_category:
                    emissions_by_category[emission.category] = 0
                emissions_by_category[emission.category] += float(emission.co2e_total or 0)
    
    context = CalculationContext(
        user_id=str(current_user.id) if hasattr(current_user, 'id') else "anonymous",
        organization_id=str(current_user.organization_id) if hasattr(current_user, 'organization_id') else "default",
        gwp_version=GWPVersionEnum.AR6_100
    )
    
    calculator = EliteEmissionsCalculator(context, db_session=db)
    
    report = calculator.generate_compliance_report(
        standard=standard,
        emissions_by_category={
            cat: Decimal(str(val)) 
            for cat, val in emissions_by_category.items()
        },
        reporting_period=reporting_period
    )
    
    return {
        "standard": standard,
        "reporting_period": reporting_period,
        "total_emissions": float(report.total_emissions),
        "scope_breakdown": {
            scope: float(val) 
            for scope, val in report.scope_breakdown.items()
        },
        "compliance_status": report.compliance_status,
        "requirements_met": report.requirements_met,
        "requirements_pending": report.requirements_pending,
        "data_quality": report.overall_data_quality.dict() if hasattr(report, 'overall_data_quality') else None,
        "data_gaps": report.data_gaps if hasattr(report, 'data_gaps') else [],
        "recommendations": report.improvement_recommendations if hasattr(report, 'improvement_recommendations') else [],
        "priority_actions": report.priority_actions,
        "category_details": report.category_breakdown if hasattr(report, 'category_breakdown') else {}
    }

@router.get("/factors/search")
async def search_emission_factors(
    query: str = Query(None, description="Search term"),
    scope: Optional[int] = Query(None, ge=1, le=3),
    category: Optional[str] = None,
    region: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Search emission factors in the database"""
    factors_query = db.query(EmissionFactor).filter(EmissionFactor.is_active == True)
    
    if query:
        factors_query = factors_query.filter(
            EmissionFactor.name.ilike(f"%{query}%") |
            EmissionFactor.description.ilike(f"%{query}%")
        )
    
    if scope:
        factors_query = factors_query.filter(EmissionFactor.scope == scope)
    
    if category:
        factors_query = factors_query.filter(EmissionFactor.category == category)
    
    if region:
        factors_query = factors_query.filter(EmissionFactor.region == region)
    
    total = factors_query.count()
    factors = factors_query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "factors": [
            {
                "id": factor.id,
                "name": factor.name,
                "category": factor.category,
                "scope": factor.scope,
                "factor": factor.factor,
                "unit": factor.unit,
                "source": factor.source,
                "uncertainty_percentage": factor.uncertainty_percentage,
                "region": factor.region,
                "tier_level": factor.tier_level,
                "scope3_category": factor.scope3_category,
                "calculation_method": factor.calculation_method
            }
            for factor in factors
        ]
    }

@router.post("/calculate/simple")
async def calculate_emissions_simple(
    activity_value: float = Body(..., example=1000),
    emission_factor: float = Body(..., example=0.233),
    unit: str = Body("kgCO2e", example="kgCO2e"),
    uncertainty_percent: float = Body(10.0, example=10.0)
):
    """
    Simple emissions calculation without database lookup
    
    Quick calculation for testing or when you have your own emission factors
    """
    result = calc_emissions(
        activity_value=activity_value,
        emission_factor=emission_factor,
        uncertainty_percent=uncertainty_percent
    )
    
    # Convert units if needed
    emissions_value = result
    if unit.lower() in ['kg', 'kgco2', 'kgco2e']:
        emissions_value = result / 1000
        unit = "tCO2e"
    
    # Calculate uncertainty bounds
    lower_bound = emissions_value * (1 - uncertainty_percent / 100)
    upper_bound = emissions_value * (1 + uncertainty_percent / 100)
    
    return {
        "emissions": emissions_value,
        "unit": unit,
        "uncertainty_percent": uncertainty_percent,
        "confidence_interval": {
            "lower": lower_bound,
            "upper": upper_bound,
            "confidence_level": 95
        }
    }

# Keep the existing endpoints
@router.post("/", response_model=EmissionResponse)
async def create_emission(
    emission: EmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emission entry with automatic calculation"""
    # Get emission factor
    factor = db.query(EmissionFactor).filter(
        EmissionFactor.id == emission.emission_factor_id
    ).first()
    
    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    
    # Calculate emissions
    co2e_total = float(emission.activity_data) * float(factor.factor)
    
    emission_entry = Emission(
        organization_id=current_user.organization_id,
        scope=emission.scope,
        category=emission.category,
        activity_type=emission.activity_type,
        activity_data=emission.activity_data,
        activity_unit=emission.activity_unit,
        emission_factor_id=emission.emission_factor_id,
        co2e_total=co2e_total,
        calculation_method=emission.calculation_method or "activity_based",
        data_quality_score=emission.data_quality_score,
        uncertainty_percentage=factor.uncertainty_percentage if hasattr(factor, 'uncertainty_percentage') else None,
        reporting_period=emission.reporting_period,
        notes=getattr(emission, 'notes', None),
        created_by=current_user.id,
        quality_score=calculate_data_quality_score(emission_entry)['total_score'] if emission_entry else None
    )
    
    db.add(emission_entry)
    db.commit()
    db.refresh(emission_entry)
    
    return emission_entry

@router.get("/{emission_id}", response_model=EmissionResponse)
async def get_emission(
    emission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific emission by ID"""
    emission = db.query(Emission).filter(
        Emission.id == emission_id,    ).first()
    
    if not emission:
        raise HTTPException(status_code=404, detail="Emission not found")
    
    return emission

@router.put("/{emission_id}", response_model=EmissionResponse)
async def update_emission(
    emission_id: int,
    emission: EmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing emission entry"""
    db_emission = db.query(Emission).filter(
        Emission.id == emission_id,    ).first()
    
    if not db_emission:
        raise HTTPException(status_code=404, detail="Emission not found")
    
    update_data = emission.dict(exclude_unset=True)
    
    # Recalculate if activity data or factor changed
    if 'activity_data' in update_data or 'emission_factor_id' in update_data:
        factor_id = update_data.get('emission_factor_id', db_emission.emission_factor_id)
        activity_data = update_data.get('activity_data', db_emission.activity_data)
        
        factor = db.query(EmissionFactor).filter(EmissionFactor.id == factor_id).first()
        if factor:
            update_data['co2e_total'] = float(activity_data) * float(factor.factor)
    
    for field, value in update_data.items():
        setattr(db_emission, field, value)
    
    # Recalculate quality score
    db_emission.quality_score = calculate_data_quality_score(db_emission)['total_score']
    db_emission.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_emission)
    
    return db_emission

@router.delete("/{emission_id}")
async def delete_emission(
    emission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an emission entry"""
    db_emission = db.query(Emission).filter(
        Emission.id == emission_id,    ).first()
    
    if not db_emission:
        raise HTTPException(status_code=404, detail="Emission not found")
    
    db.delete(db_emission)
    db.commit()
    
    return {"message": "Emission deleted successfully", "id": emission_id}

@router.get("/export/csv")
async def export_emissions_csv(
    scope: Optional[int] = Query(None, ge=1, le=3),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_uncertainty: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export emissions data as CSV with optional uncertainty data"""
    query = db.query(Emission).filter(    )
    
    if scope:
        query = query.filter(Emission.scope == scope)
    
    if start_date:
        query = query.filter(Emission.created_at >= start_date)
    
    if end_date:
        query = query.filter(Emission.created_at <= end_date)
    
    emissions = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header with optional uncertainty columns
    headers = [
        'ID', 'Date', 'Scope', 'Category', 'Activity Type', 'Activity Data', 
        'Unit', 'Emission Factor ID', 'CO2e Total (tCO2e)', 'Calculation Method',
        'Data Quality Score', 'Evidence Type', 'Quality Score', 'Reporting Period', 'Notes'
    ]
    
    if include_uncertainty:
        headers.extend(['Uncertainty %', 'Lower Bound', 'Upper Bound'])
    
    writer.writerow(headers)
    
    # Data rows
    for emission in emissions:
        row = [
            emission.id,
            emission.created_at.strftime('%Y-%m-%d') if emission.created_at else '',
            emission.scope,
            emission.category or '',
            emission.activity_type or '',
            emission.activity_data or '',
            emission.activity_unit or '',
            emission.emission_factor_id or '',
            emission.co2e_total or '',
            emission.calculation_method or '',
            emission.data_quality_score or '',
            emission.evidence_type or '',
            emission.quality_score or '',
            emission.reporting_period or '',
            emission.notes or ''
        ]
        
        if include_uncertainty:
            uncertainty = emission.uncertainty_percentage or 10.0
            lower = (emission.co2e_total or 0) * (1 - uncertainty / 100)
            upper = (emission.co2e_total or 0) * (1 + uncertainty / 100)
            row.extend([uncertainty, lower, upper])
        
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=emissions_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@router.post("/bulk-upload")
async def bulk_upload_emissions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk upload emissions from CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    contents = await file.read()
    csv_reader = csv.DictReader(io.StringIO(contents.decode('utf-8')))
    
    created_count = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # Parse the row
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.name == row.get('emission_factor_name')
            ).first()
            
            if not factor:
                errors.append(f"Row {row_num}: Emission factor '{row.get('emission_factor_name')}' not found")
                continue
            
            activity_data = float(row.get('activity_data', 0))
            co2e_total = activity_data * float(factor.factor)
            
            emission = Emission(
                organization_id=current_user.organization_id,
                scope=int(row.get('scope', 1)),
                category=row.get('category'),
                activity_type=row.get('activity_type'),
                activity_data=activity_data,
                activity_unit=row.get('activity_unit'),
                emission_factor_id=factor.id,
                co2e_total=co2e_total,
                calculation_method=row.get('calculation_method', 'activity_based'),
                reporting_period=row.get('reporting_period'),
                created_by=current_user.id
            )
            
            # Calculate initial quality score
            emission.quality_score = calculate_data_quality_score(emission)['total_score']
            
            db.add(emission)
            created_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "created": created_count,
        "errors": errors,
        "total_rows": row_num - 1
    }
@router.post("/esrs-e1/export/esrs-e1-world-class")
async def generate_esrs_e1_report(data: dict):
    """Generate ESRS E1 compliant iXBRL report"""
    from .esrs_e1_full import generate_world_class_esrs_e1_ixbrl
    return generate_world_class_esrs_e1_ixbrl(data)

