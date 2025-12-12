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

# App imports
from app.core.auth import get_current_user
from app.schemas.auth_schemas import CurrentUser
from app.db.session import get_db
from app.models.emission import Emission, EmissionScope
from app.models.emission_factor import EmissionFactor
from app.models.evidence_document import EvidenceDocument
from app.core.tenant import tenant_query, get_tenant_record, delete_tenant_record, soft_delete_tenant_record, restore_tenant_record
from app.core.queries import paginate_query
from app.schemas.common import PaginationMeta
from app.schemas.emission import (
    EmissionCreate,
    EmissionResponse,
    EmissionsSummary,
    EmissionUpdate,
    EmissionCalculationRequest,
    EmissionCalculationResponse,
    EmissionCalculationMethod,
    EmissionDatasetPreference,
)
from app.schemas.api_schemas import EmissionFactorInput

# Import spend-based calculation service
from app.services.spend_based_calculation import (
    calculate_spend_based_emissions,
    SpendBasedCalculationError,
)

# Import data quality calculation
from app.api.v1.endpoints.data_quality import calculate_data_quality_score

# Import audit logging service
from app.services.audit import log_create, log_delete, log_restore

# Import number sanitization for locale handling
from app.utils.format import sanitize_number, NumberFormatError

# Import unit validation for Pint-based unit checking
from app.utils.units import validate_unit, UnitError

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

# Import from centralized emission factor service
from app.services.emission_factors import get_factor, normalize_scope

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


# =============================================================================
# UNIFIED CALCULATION ENDPOINT (Production-Grade)
# =============================================================================

def _resolve_dataset_for_country(country_code: str, method: str) -> str:
    """Resolve dataset based on country code when AUTO is specified."""
    if method == "spend_based":
        return "EXIOBASE_2020"

    country_upper = country_code.upper() if country_code else "GLOBAL"
    if country_upper == "GB":
        return "DEFRA_2024"
    elif country_upper == "US":
        return "EPA_2024"
    else:
        return "DEFRA_2024"  # Default to DEFRA for other countries


@router.post(
    "/calculate",
    response_model=EmissionCalculationResponse,
    summary="Unified Emission Calculation",
    description="""
Calculate emissions using either activity-based or spend-based methods.

## Activity-Based Calculation (DEFRA/EPA)
For physical activity data like electricity consumption, fuel usage, travel distances.

**Required fields:**
- `method`: "activity_data"
- `scope`: 1, 2, or 3
- `country_code`: ISO country code (e.g., "DE", "GB", "US")
- `amount`: Activity quantity (e.g., kWh, liters)
- `unit`: Unit of measurement
- `category`: Emission category (e.g., "electricity", "stationary_combustion")
- `activity_type`: Specific activity (e.g., "Electricity - Grid Average")

**Dataset selection:**
- AUTO: GB→DEFRA_2024, US→EPA_2024, others→DEFRA_2024
- DEFRA_2024: UK Government factors
- EPA_2024: US EPA factors

## Spend-Based Calculation (EXIOBASE)
For financial data (spend in EUR) when activity data is unavailable.

**Required fields:**
- `method`: "spend_based"
- `scope`: 3 (typically)
- `country_code`: ISO country code
- `amount`: Spend in EUR
- `unit`: "EUR"
- `sector_label`: User-friendly sector (e.g., "IT Services") OR
- `exiobase_activity_type`: Exact EXIOBASE sector name

**Notes:**
- EXIOBASE factors with values >100 kgCO2e/EUR are flagged as potential outliers
- Country fallback: country → ROW_region → GLOBAL
    """,
    responses={
        200: {"description": "Calculation successful"},
        422: {
            "description": "Factor not found or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "FACTOR_NOT_FOUND",
                        "lookup_key": {
                            "scope": "SCOPE_2",
                            "category": "electricity",
                            "activity_type": "Unknown",
                            "country_code": "XX",
                            "dataset": "DEFRA_2024"
                        }
                    }
                }
            }
        }
    },
    tags=["Emissions"]
)
async def calculate_emissions_unified(
    payload: EmissionCalculationRequest,
    db: Session = Depends(get_db),
):
    """
    Unified emission calculation endpoint.

    Supports both activity-based (DEFRA/EPA) and spend-based (EXIOBASE) methods.
    Does NOT create database records - pure calculation only.

    TODO: Add authentication when auth system is finalized.
    """
    import logging
    logger = logging.getLogger(__name__)

    method = payload.method
    amount = float(payload.amount)
    country_code = payload.country_code.upper()

    # Resolve dataset
    if payload.dataset == "AUTO" or payload.dataset == EmissionDatasetPreference.auto:
        dataset = _resolve_dataset_for_country(country_code, method)
    else:
        dataset = payload.dataset if isinstance(payload.dataset, str) else payload.dataset.value

    logger.info(f"Calculation request: method={method}, dataset={dataset}, country={country_code}, amount={amount}")

    # =========================================================================
    # SPEND-BASED CALCULATION (EXIOBASE)
    # =========================================================================
    if method == "spend_based" or method == EmissionCalculationMethod.spend_based:
        # Validate spend-based specific fields
        if not payload.sector_label and not payload.exiobase_activity_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "MISSING_SECTOR",
                    "message": "For spend_based method, provide either 'sector_label' or 'exiobase_activity_type'"
                }
            )

        try:
            result = calculate_spend_based_emissions(
                db=db,
                spend_amount_eur=amount,
                country_code=country_code,
                exiobase_sector=payload.exiobase_activity_type,
                sector_label=payload.sector_label,
                activity_type=payload.activity_type,
            )

            # Build notes for warnings
            notes = None
            if result.factor_outlier_warning:
                notes = f"Factor outlier warning: {result.factor_value:.2f} kgCO2e/EUR exceeds 100 threshold (potential MRIO artifact)"

            return EmissionCalculationResponse(
                emissions_kg_co2e=result.emissions_kg_co2e,
                factor_value=result.factor_value,
                factor_unit=result.factor_unit,
                dataset_used=result.dataset,
                method_used="spend_based",
                scope=payload.scope,
                country_code=result.country_code_used,
                activity_type_used=None,
                sector_used=result.activity_type_used,
                notes=notes,
            )

        except SpendBasedCalculationError as e:
            logger.warning(f"Spend-based calculation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "FACTOR_NOT_FOUND",
                    "message": str(e),
                    "lookup_key": {
                        "method": "spend_based",
                        "country_code": country_code,
                        "sector_label": payload.sector_label,
                        "exiobase_activity_type": payload.exiobase_activity_type,
                        "dataset": "EXIOBASE_2020"
                    }
                }
            )

    # =========================================================================
    # ACTIVITY-BASED CALCULATION (DEFRA/EPA)
    # =========================================================================
    else:
        # Validate activity-based specific fields
        if not payload.category or not payload.activity_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "MISSING_FIELDS",
                    "message": "For activity_data method, provide both 'category' and 'activity_type'"
                }
            )

        # Normalize scope
        scope_str = normalize_scope(payload.scope)

        # Look up factor from database
        factor_value = get_factor(
            db,
            scope=payload.scope,
            category=payload.category,
            activity_type=payload.activity_type,
            country_code=country_code,
            year=2024,
            dataset=dataset if dataset != "AUTO" else None,
        )

        if factor_value is None:
            lookup_key = {
                "scope": scope_str,
                "category": payload.category,
                "activity_type": payload.activity_type,
                "country_code": country_code,
                "year": 2024,
                "dataset": dataset
            }
            logger.warning(f"No emission factor found: {lookup_key}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "FACTOR_NOT_FOUND",
                    "lookup_key": lookup_key
                }
            )

        # Calculate emissions (factor is kgCO2e/unit)
        emissions_kg_co2e = amount * factor_value

        # Determine factor unit based on user's unit
        factor_unit = f"kgCO2e/{payload.unit}"

        return EmissionCalculationResponse(
            emissions_kg_co2e=emissions_kg_co2e,
            factor_value=factor_value,
            factor_unit=factor_unit,
            dataset_used=dataset,
            method_used="activity_data",
            scope=payload.scope,
            country_code=country_code,
            activity_type_used=payload.activity_type,
            sector_used=None,
            notes=None,
        )


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


# Activity types organized by category (for cascading dropdown)
ACTIVITY_TYPES_BY_CATEGORY = {
    # Scope 1 categories
    "stationary_combustion": [
        {"activity_type": "Natural Gas", "unit": "m³", "factor_value": 0.18454, "source": "EPA"},
        {"activity_type": "Fuel Oil", "unit": "L", "factor_value": 2.753, "source": "EPA"},
        {"activity_type": "Propane", "unit": "L", "factor_value": 1.51, "source": "EPA"},
        {"activity_type": "Coal", "unit": "kg", "factor_value": 2.42, "source": "EPA"},
    ],
    "mobile_combustion": [
        {"activity_type": "Diesel - Vehicles", "unit": "L", "factor_value": 2.68, "source": "EPA"},
        {"activity_type": "Gasoline - Vehicles", "unit": "L", "factor_value": 2.31, "source": "EPA"},
        {"activity_type": "Jet Fuel", "unit": "L", "factor_value": 2.55, "source": "EPA"},
    ],
    "process_emissions": [
        {"activity_type": "CO2 Process Emissions", "unit": "tCO2", "factor_value": 1000.0, "source": "Direct"},
    ],
    "refrigerants": [
        {"activity_type": "R-134a Refrigerant", "unit": "kg", "factor_value": 1430, "source": "IPCC"},
        {"activity_type": "R-410A Refrigerant", "unit": "kg", "factor_value": 2088, "source": "IPCC"},
    ],
    # Scope 2 categories
    "electricity": [
        {"activity_type": "Electricity - Grid Average", "unit": "kWh", "factor_value": 0.233, "source": "EPA eGRID"},
        {"activity_type": "Electricity - Renewable", "unit": "kWh", "factor_value": 0.0, "source": "EPA"},
    ],
    "heating_cooling": [
        {"activity_type": "District Heating", "unit": "kWh", "factor_value": 0.215, "source": "EPA"},
        {"activity_type": "District Cooling", "unit": "kWh", "factor_value": 0.198, "source": "EPA"},
    ],
    "steam": [
        {"activity_type": "Steam", "unit": "kg", "factor_value": 0.068, "source": "EPA"},
    ],
    # Scope 3 categories
    "purchased_goods_services": [
        {"activity_type": "Office Paper", "unit": "kg", "factor_value": 0.92, "source": "EPA"},
        {"activity_type": "Plastic Products", "unit": "kg", "factor_value": 1.89, "source": "EPA"},
        {"activity_type": "Steel", "unit": "kg", "factor_value": 1.85, "source": "EPA"},
        {"activity_type": "Aluminum", "unit": "kg", "factor_value": 11.89, "source": "EPA"},
        {"activity_type": "Concrete", "unit": "m³", "factor_value": 385, "source": "EPA"},
        {"activity_type": "Electronics", "unit": "USD", "factor_value": 0.42, "source": "EPA"},
        {"activity_type": "Textiles", "unit": "kg", "factor_value": 8.1, "source": "EPA"},
        {"activity_type": "Food & Beverages", "unit": "USD", "factor_value": 0.89, "source": "EPA"},
    ],
    "capital_goods": [
        {"activity_type": "IT Equipment", "unit": "USD", "factor_value": 0.65, "source": "EPA"},
        {"activity_type": "Office Furniture", "unit": "USD", "factor_value": 0.45, "source": "EPA"},
        {"activity_type": "Vehicles", "unit": "USD", "factor_value": 0.89, "source": "EPA"},
        {"activity_type": "Buildings", "unit": "m²", "factor_value": 125.0, "source": "EPA"},
        {"activity_type": "Manufacturing Equipment", "unit": "USD", "factor_value": 0.78, "source": "EPA"},
    ],
    "fuel_energy_activities": [
        {"activity_type": "Upstream Electricity", "unit": "kWh", "factor_value": 0.045, "source": "EPA"},
        {"activity_type": "T&D Losses", "unit": "kWh", "factor_value": 0.023, "source": "EPA"},
        {"activity_type": "WTT - Natural Gas", "unit": "m³", "factor_value": 0.031, "source": "EPA"},
        {"activity_type": "WTT - Gasoline", "unit": "L", "factor_value": 0.62, "source": "EPA"},
        {"activity_type": "WTT - Diesel", "unit": "L", "factor_value": 0.58, "source": "EPA"},
    ],
    "upstream_transportation": [
        {"activity_type": "Road Freight", "unit": "tonne-km", "factor_value": 0.105, "source": "EPA"},
        {"activity_type": "Rail Freight", "unit": "tonne-km", "factor_value": 0.027, "source": "EPA"},
        {"activity_type": "Air Freight", "unit": "tonne-km", "factor_value": 1.13, "source": "EPA"},
        {"activity_type": "Sea Freight", "unit": "tonne-km", "factor_value": 0.016, "source": "EPA"},
    ],
    "waste_operations": [
        {"activity_type": "Landfill - Mixed Waste", "unit": "tonnes", "factor_value": 467.0, "source": "EPA"},
        {"activity_type": "Recycling - Paper", "unit": "tonnes", "factor_value": 21.0, "source": "EPA"},
        {"activity_type": "Recycling - Plastic", "unit": "tonnes", "factor_value": 32.0, "source": "EPA"},
        {"activity_type": "Composting", "unit": "tonnes", "factor_value": 55.0, "source": "EPA"},
        {"activity_type": "Incineration", "unit": "tonnes", "factor_value": 895.0, "source": "EPA"},
    ],
    "business_travel": [
        {"activity_type": "Air Travel - Short Haul", "unit": "passenger-km", "factor_value": 0.215, "source": "EPA"},
        {"activity_type": "Air Travel - Long Haul", "unit": "passenger-km", "factor_value": 0.115, "source": "EPA"},
        {"activity_type": "Rail Travel", "unit": "passenger-km", "factor_value": 0.041, "source": "EPA"},
        {"activity_type": "Taxi/Uber", "unit": "km", "factor_value": 0.21, "source": "EPA"},
        {"activity_type": "Hotel Stay", "unit": "nights", "factor_value": 15.3, "source": "EPA"},
        {"activity_type": "Rental Car", "unit": "km", "factor_value": 0.171, "source": "EPA"},
    ],
    "employee_commuting": [
        {"activity_type": "Car - Average", "unit": "km", "factor_value": 0.171, "source": "EPA"},
        {"activity_type": "Bus", "unit": "passenger-km", "factor_value": 0.089, "source": "EPA"},
        {"activity_type": "Metro/Subway", "unit": "passenger-km", "factor_value": 0.033, "source": "EPA"},
        {"activity_type": "Motorcycle", "unit": "km", "factor_value": 0.113, "source": "EPA"},
        {"activity_type": "Bicycle", "unit": "km", "factor_value": 0.0, "source": "EPA"},
        {"activity_type": "Remote Work", "unit": "days", "factor_value": 2.5, "source": "EPA"},
    ],
    "upstream_leased_assets": [
        {"activity_type": "Leased Buildings", "unit": "m²-year", "factor_value": 45.0, "source": "EPA"},
        {"activity_type": "Leased Vehicles", "unit": "km", "factor_value": 0.171, "source": "EPA"},
        {"activity_type": "Leased Equipment", "unit": "USD", "factor_value": 0.32, "source": "EPA"},
    ],
    "downstream_transportation": [
        {"activity_type": "Product Delivery - Road", "unit": "tonne-km", "factor_value": 0.105, "source": "EPA"},
        {"activity_type": "Product Delivery - Rail", "unit": "tonne-km", "factor_value": 0.027, "source": "EPA"},
        {"activity_type": "Product Delivery - Air", "unit": "tonne-km", "factor_value": 1.13, "source": "EPA"},
        {"activity_type": "Product Delivery - Sea", "unit": "tonne-km", "factor_value": 0.016, "source": "EPA"},
    ],
    "processing_sold_products": [
        {"activity_type": "Manufacturing Process", "unit": "kg", "factor_value": 0.85, "source": "EPA"},
        {"activity_type": "Assembly Process", "unit": "unit", "factor_value": 12.5, "source": "EPA"},
        {"activity_type": "Packaging Process", "unit": "kg", "factor_value": 0.45, "source": "EPA"},
    ],
    "use_of_sold_products": [
        {"activity_type": "Electronics - Use Phase", "unit": "unit-year", "factor_value": 125.0, "source": "EPA"},
        {"activity_type": "Appliances - Use Phase", "unit": "unit-year", "factor_value": 450.0, "source": "EPA"},
        {"activity_type": "Vehicles - Use Phase", "unit": "km", "factor_value": 0.171, "source": "EPA"},
        {"activity_type": "Software - Use Phase", "unit": "user-year", "factor_value": 8.5, "source": "EPA"},
    ],
    "end_of_life_treatment": [
        {"activity_type": "Landfill Disposal", "unit": "tonnes", "factor_value": 467.0, "source": "EPA"},
        {"activity_type": "Recycling", "unit": "tonnes", "factor_value": 21.0, "source": "EPA"},
        {"activity_type": "Incineration", "unit": "tonnes", "factor_value": 895.0, "source": "EPA"},
        {"activity_type": "E-waste Treatment", "unit": "kg", "factor_value": 2.5, "source": "EPA"},
    ],
    "downstream_leased_assets": [
        {"activity_type": "Leased Real Estate", "unit": "m²-year", "factor_value": 45.0, "source": "EPA"},
        {"activity_type": "Leased Equipment", "unit": "USD", "factor_value": 0.32, "source": "EPA"},
        {"activity_type": "Leased Vehicles", "unit": "vehicle-year", "factor_value": 4500.0, "source": "EPA"},
    ],
    "franchises": [
        {"activity_type": "Franchise Operations", "unit": "m²-year", "factor_value": 55.0, "source": "EPA"},
        {"activity_type": "Franchise Energy Use", "unit": "kWh", "factor_value": 0.233, "source": "EPA"},
        {"activity_type": "Franchise Waste", "unit": "tonnes", "factor_value": 467.0, "source": "EPA"},
    ],
    "investments": [
        {"activity_type": "Equity Investments", "unit": "USD", "factor_value": 0.00012, "source": "EPA"},
        {"activity_type": "Debt Investments", "unit": "USD", "factor_value": 0.00008, "source": "EPA"},
        {"activity_type": "Project Finance", "unit": "USD", "factor_value": 0.00015, "source": "EPA"},
    ],
}

def normalize_scope_input(scope_input) -> Optional[int]:
    """Normalize various scope input formats to integer 1, 2, or 3.

    Handles: 1, "1", "SCOPE_1", "Scope 1", etc.
    """
    if scope_input is None:
        return None

    s_str = str(scope_input).strip().upper()
    print(f"DEBUG normalize_scope_input: input={scope_input}, type={type(scope_input)}, s_str={s_str}")

    if "1" in s_str:
        return 1
    elif "2" in s_str:
        return 2
    elif "3" in s_str:
        return 3

    return None


@router.get("/countries")
async def get_available_countries(
    db: Session = Depends(get_db)
) -> List[str]:
    """Get unique country codes available in the emission factors database.

    Returns a sorted list of country codes (e.g., ["DE", "FR", "GLOBAL", "US"]).
    GLOBAL appears first, then alphabetically sorted country codes.
    """
    # Query distinct country codes from the emission_factors table
    country_codes = db.query(EmissionFactor.country_code).distinct().all()

    # Extract strings from tuples and filter out None/empty
    codes = [code[0] for code in country_codes if code[0]]

    # Sort with GLOBAL first, then alphabetically
    global_codes = [c for c in codes if c.upper() == 'GLOBAL']
    other_codes = sorted([c for c in codes if c.upper() != 'GLOBAL'])

    return global_codes + other_codes


@router.get("/categories")
async def get_emission_categories(
    scope: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> List[str]:
    """Get emission categories for a scope. Returns a flat array of category names."""
    print(f"DEBUG get_emission_categories: scope={scope}, type={type(scope)}")

    # Categories organized by scope
    categories_by_scope = {
        1: ["stationary_combustion", "mobile_combustion", "process_emissions", "refrigerants"],
        2: ["electricity", "heating_cooling", "steam"],
        3: list(SCOPE3_CATEGORIES.keys())
    }

    # Normalize scope input
    normalized_scope = normalize_scope_input(scope)
    print(f"DEBUG get_emission_categories: normalized_scope={normalized_scope}")

    if normalized_scope is not None:
        result = categories_by_scope.get(normalized_scope, [])
        print(f"DEBUG get_emission_categories: returning {len(result)} categories for scope {normalized_scope}")
        return result

    # Return all categories flattened
    all_categories = []
    for cats in categories_by_scope.values():
        all_categories.extend(cats)
    result = list(set(all_categories))
    print(f"DEBUG get_emission_categories: returning all {len(result)} categories")
    return result

@router.get("/factors")
async def get_activity_types_for_category(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get activity types (emission factors) for a specific category.

    Returns array of objects with: activity_type, unit, factor_value, source
    """
    print(f"DEBUG get_activity_types_for_category: category={category}, type={type(category)}")

    if category is None:
        # Return all activity types across all categories
        all_factors = []
        for cat_factors in ACTIVITY_TYPES_BY_CATEGORY.values():
            all_factors.extend(cat_factors)
        print(f"DEBUG get_activity_types_for_category: returning all {len(all_factors)} factors")
        return all_factors

    # Normalize category (strip whitespace, handle case)
    normalized_category = category.strip().lower().replace(" ", "_").replace("-", "_")
    print(f"DEBUG get_activity_types_for_category: normalized_category={normalized_category}")

    # Try exact match first
    if category in ACTIVITY_TYPES_BY_CATEGORY:
        result = ACTIVITY_TYPES_BY_CATEGORY[category]
        print(f"DEBUG get_activity_types_for_category: exact match, returning {len(result)} factors")
        return result

    # Try normalized match
    if normalized_category in ACTIVITY_TYPES_BY_CATEGORY:
        result = ACTIVITY_TYPES_BY_CATEGORY[normalized_category]
        print(f"DEBUG get_activity_types_for_category: normalized match, returning {len(result)} factors")
        return result

    print(f"DEBUG get_activity_types_for_category: no match found for '{category}'")
    return []


@router.post("/upload-evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    emission_id: int = Form(...),
    evidence_type: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Upload evidence document for an emission entry."""

    # MULTI-TENANT: Validate emission exists AND belongs to current tenant
    emission = get_tenant_record(db, Emission, emission_id, current_user.tenant_id)
    
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
        # MULTI-TENANT: Set tenant_id on evidence document
        evidence_doc = EvidenceDocument(
            tenant_id=current_user.tenant_id,
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
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete evidence document."""
    # MULTI-TENANT: Validate evidence belongs to current tenant
    evidence = get_tenant_record(db, EvidenceDocument, evidence_id, current_user.tenant_id)

    # Delete file from storage
    file_path = Path(evidence.file_path)
    if file_path.exists():
        file_path.unlink()

    # Update emission (also tenant-scoped)
    emission = db.query(Emission).filter(
        Emission.id == evidence.emission_id,
        Emission.tenant_id == current_user.tenant_id
    ).first()
    if emission:
        emission.evidence_type = None
        emission.document_url = None
        emission.quality_score = calculate_data_quality_score(emission)['total_score']

    # Delete database record
    db.delete(evidence)
    db.commit()

    return {"message": "Evidence deleted successfully"}

# ===== EXISTING ENDPOINTS (Enhanced) =====

@router.get(
    "/",
    summary="List all Emission records",
    description="""
Retrieve a paginated list of emission records with optional filtering.

## Filtering Options
- **scope**: Filter by GHG Protocol scope (1, 2, or 3)
- **category**: Filter by emission category (exact match)
- **start_date / end_date**: Filter by creation date range

## Pagination
- **page**: Page number (1-indexed, default: 1)
- **per_page**: Items per page (default: 20, max: 100)

Results are sorted by creation date (newest first).

## Response Format
Returns paginated response with metadata:
```json
{
    "items": [...],
    "meta": {
        "total": 100,
        "page": 1,
        "per_page": 20,
        "pages": 5,
        "has_next": true,
        "has_prev": false
    }
}
```
    """,
    responses={
        200: {"description": "Paginated list of emission records"},
        401: {"description": "Not authenticated"}
    },
    tags=["Emissions"]
)
async def get_emissions(
    scope: Optional[int] = Query(None, ge=1, le=3, description="Filter by GHG Protocol scope"),
    category: Optional[str] = Query(None, description="Filter by emission category (exact match)"),
    start_date: Optional[datetime] = Query(None, description="Filter records created after this date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter records created before this date (ISO 8601)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, Emission, current_user.tenant_id)

    if scope:
        query = query.filter(Emission.scope == scope)

    if category:
        query = query.filter(Emission.category == category)

    if start_date:
        query = query.filter(Emission.created_at >= start_date)

    if end_date:
        query = query.filter(Emission.created_at <= end_date)

    query = query.order_by(Emission.created_at.desc())

    # Apply pagination using the standardized helper
    emissions, meta = paginate_query(query, page=page, per_page=per_page)

    # Serialize emissions using actual model attributes
    items = []
    for emission in emissions:
        emission_dict = {
            "id": emission.id,
            "tenant_id": emission.tenant_id,
            "scope": emission.scope.value if hasattr(emission.scope, 'value') else emission.scope,
            "category": emission.category,
            "subcategory": emission.subcategory,
            "activity_data": emission.activity_data,
            "unit": emission.unit,
            "emission_factor": emission.emission_factor,
            "emission_factor_source": emission.emission_factor_source,
            "amount": emission.amount,
            "data_source": emission.data_source.value if emission.data_source and hasattr(emission.data_source, 'value') else emission.data_source,
            "data_quality_score": emission.data_quality_score,
            "uncertainty_percentage": emission.uncertainty_percentage,
            "location": emission.location,
            "country_code": emission.country_code,
            "reporting_period_start": emission.reporting_period_start,
            "reporting_period_end": emission.reporting_period_end,
            "description": emission.description,
            "is_verified": emission.is_verified,
            "created_at": emission.created_at,
            "updated_at": emission.updated_at,
        }
        items.append(emission_dict)

    return {
        "items": items,
        "meta": meta.model_dump()
    }

@router.get(
    "/summary",
    response_model=EmissionsSummary,
    summary="Get Emissions Summary",
    description="""
Returns aggregated emission totals for dashboard displays and reporting.

## Response includes:
- **scope1_total**: Total direct emissions (tCO2e)
- **scope2_total**: Total purchased energy emissions (tCO2e)
- **scope3_total**: Total value chain emissions (tCO2e)
- **total_emissions**: Sum of all scopes (tCO2e)
- **by_category**: Breakdown by emission category

Useful for:
- Dashboard KPI widgets
- Executive summaries
- ESRS E1 reporting data
    """,
    responses={
        200: {"description": "Aggregated emissions summary"},
        401: {"description": "Not authenticated"}
    },
    tags=["Emissions"]
)
async def get_emissions_summary(
    reporting_period: Optional[str] = Query(None, description="Filter by reporting period (e.g., '2024', '2024-Q1')"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, Emission, current_user.tenant_id)

    if reporting_period:
        query = query.filter(Emission.reporting_period == reporting_period)
    
    # Calculate totals by scope (using 'amount' field from Emission model)
    # Import EmissionScope enum for proper comparison
    from app.models.emission import EmissionScope

    scope1_total = query.filter(Emission.scope == EmissionScope.SCOPE_1).with_entities(
        func.sum(Emission.amount)
    ).scalar() or 0

    scope2_total = query.filter(Emission.scope == EmissionScope.SCOPE_2).with_entities(
        func.sum(Emission.amount)
    ).scalar() or 0

    scope3_total = query.filter(Emission.scope == EmissionScope.SCOPE_3).with_entities(
        func.sum(Emission.amount)
    ).scalar() or 0

    # Get breakdown by category
    category_breakdown = {}
    categories = query.with_entities(
        Emission.category,
        func.sum(Emission.amount).label('total')
    ).group_by(Emission.category).all()

    for cat, total in categories:
        if cat:
            category_breakdown[cat] = float(total or 0)

    return EmissionsSummary(
        total_emissions=float(scope1_total + scope2_total + scope3_total),
        scope1_total=float(scope1_total),
        scope2_total=float(scope2_total),
        scope3_total=float(scope3_total),
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Advanced emissions calculation with uncertainty analysis

    Uses the sophisticated calculation engine with Monte Carlo simulation
    """
    try:
        # Create calculation context
        context = CalculationContext(
            user_id=str(current_user.id),
            organization_id=str(current_user.tenant_id),  # Use tenant_id
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
    current_user: CurrentUser = Depends(get_current_user)
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
            user_id=str(current_user.id),
            organization_id=str(current_user.tenant_id),  # Use tenant_id
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Assess materiality of Scope 3 categories for your sector

    Helps identify which categories should be prioritized for calculation
    """
    context = CalculationContext(
        user_id=str(current_user.id),
        organization_id=str(current_user.tenant_id),  # Use tenant_id
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate Scope 3 emissions for a specific category"""
    try:
        result = calculate_scope3_emissions(
            category=request.category,
            activity_data=request.activity_data,
            user_id=str(current_user.id),
            organization_id=str(current_user.tenant_id),  # Use tenant_id
            db_session=db
        )

        # Save to database
        # MULTI-TENANT: Set tenant_id from current user
        emission_entry = Emission(
            tenant_id=current_user.tenant_id,
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate compliance report for specific standard (ESRS, CDP, TCFD, SBTi)
    """
    # If emissions not provided, fetch from database
    if not emissions_by_category:
        # MULTI-TENANT: Filter by tenant_id
        emissions = tenant_query(db, Emission, current_user.tenant_id).filter(
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
        user_id=str(current_user.id),
        organization_id=str(current_user.tenant_id),  # Use tenant_id
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

# Main emission creation endpoint
@router.post(
    "/",
    summary="Create a new Emission record",
    description="""
Creates a new emission entry and automatically calculates the CO2e amount.

## Factor Resolution Logic
1. **Manual Override**: If `emission_factor` is provided in the payload, it will be used directly
2. **Database Lookup**: Otherwise, the API looks up the emission factor using the combination of:
   - `scope` (1, 2, or 3)
   - `category` (e.g., "Purchased Electricity")
   - `activity_type` (e.g., "Electricity")
   - `country_code` (e.g., "DE" for Germany)
3. **Error**: If no matching factor is found, returns 422 with the lookup key for debugging

## Calculation
The emission amount is calculated as:
```
amount (tCO2e) = activity_data × emission_factor / 1000
```

## Example Use Cases
- **Scope 1 Diesel**: 1000 liters of diesel in DE → ~2.65 tCO2e
- **Scope 2 Electricity**: 10000 kWh in DE → ~3.5 tCO2e
- **Scope 3 Business Travel**: 5000 km flight → varies by class
    """,
    response_description="The created emission record with calculated CO2e amount",
    responses={
        200: {
            "description": "Emission created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "scope": 2,
                        "category": "Purchased Electricity",
                        "activity_type": "Electricity",
                        "activity_data": 10000.0,
                        "unit": "kWh",
                        "country_code": "DE",
                        "emission_factor": 0.35,
                        "emission_factor_source": "Database",
                        "amount": 3.5,
                        "created_at": "2024-03-15T10:30:00Z"
                    }
                }
            }
        },
        401: {
            "description": "Not authenticated - Bearer token missing or invalid"
        },
        422: {
            "description": "Emission factor not found - The combination of scope/category/activity_type/country_code has no matching entry in the database",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No emission factor found for key: (scope_2, Purchased Electricity, Electricity, XX)"
                    }
                }
            }
        }
    },
    tags=["Emissions"]
)
async def create_emission(
    emission: EmissionCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    import logging
    logger = logging.getLogger(__name__)

    # STEP 0: Validate unit using Pint (per CLAUDE.md requirements)
    if emission.unit and not validate_unit(emission.unit):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INVALID_UNIT",
                "message": f"Unknown or invalid unit: '{emission.unit}'",
                "hint": "Use standard units like kWh, kg, L, km, m³, etc."
            }
        )

    factor_value: float | None = None
    factor_source: str = "Unknown"

    # STEP 1: Check for manual override
    if emission.emission_factor is not None:
        factor_value = emission.emission_factor
        factor_source = "Manual Override"
        logger.info(f"Using manual emission factor override: {factor_value}")

    # STEP 2: Lookup from centralized emission factor service (Database)
    if factor_value is None:
        scope_str = normalize_scope(emission.scope)
        # Use new get_factor signature: db is first positional, rest are keyword-only
        factor_value = get_factor(
            db,
            scope=emission.scope,
            category=emission.category,
            activity_type=emission.activity_type,
            country_code=emission.country_code,
            year=2024,  # Default year
            dataset=None,  # No specific dataset (will search all)
        )

        if factor_value is not None:
            factor_source = "Database"
            logger.info(
                f"Factor lookup success: ({scope_str}, {emission.category}, "
                f"{emission.activity_type}, {emission.country_code}) -> {factor_value}"
            )

    # STEP 3: Error if no factor found - include all key fields for debugging
    if factor_value is None:
        scope_str = normalize_scope(emission.scope)
        missing_key = {
            "scope": scope_str,
            "category": emission.category,
            "activity_type": emission.activity_type,
            "country_code": emission.country_code or "GLOBAL",
            "year": 2024,
            "dataset": None,
        }
        logger.error(f"No emission factor found for key: {missing_key}")
        raise HTTPException(
            status_code=422,
            detail=f"No emission factor found for key: {missing_key}"
        )

    # Calculate emissions (factor is in kgCO2e per unit, convert to tCO2e)
    amount = float(emission.activity_data) * factor_value / 1000

    # Create emission entry
    # MULTI-TENANT: Set tenant_id from current user
    emission_entry = Emission(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id if hasattr(current_user, 'id') else None,
        scope=emission.scope,
        category=emission.category,
        activity_data=emission.activity_data,
        unit=emission.unit,
        emission_factor=factor_value,
        emission_factor_source=factor_source,
        amount=amount,
        data_quality_score=int(emission.data_quality_score) if emission.data_quality_score else None,
        uncertainty_percentage=10.0,  # Default uncertainty
        description=emission.description,
        country_code=emission.country_code,
        location=emission.location,
    )

    db.add(emission_entry)
    db.flush()  # Get the ID before commit for audit log

    # Log CREATE action for audit trail (CSRD compliance)
    log_create(
        db=db,
        entity=emission_entry,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id if hasattr(current_user, 'id') else None
    )

    db.commit()
    db.refresh(emission_entry)

    # Return response
    return {
        "id": emission_entry.id,
        "scope": emission_entry.scope.value if hasattr(emission_entry.scope, 'value') else emission_entry.scope,
        "category": emission_entry.category,
        "activity_type": emission.activity_type,
        "activity_data": emission_entry.activity_data,
        "unit": emission_entry.unit,
        "country_code": emission_entry.country_code,
        "emission_factor": emission_entry.emission_factor,
        "emission_factor_source": factor_source,
        "amount": emission_entry.amount,
        "data_quality_score": emission_entry.data_quality_score,
        "uncertainty_percentage": emission_entry.uncertainty_percentage,
        "description": emission_entry.description,
        "location": emission_entry.location,
        "created_at": emission_entry.created_at,
        "updated_at": emission_entry.updated_at
    }

@router.get("/{emission_id}", response_model=EmissionResponse)
async def get_emission(
    emission_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific emission by ID"""
    # MULTI-TENANT: Validate emission belongs to current tenant
    emission = get_tenant_record(db, Emission, emission_id, current_user.tenant_id)
    return emission

@router.put("/{emission_id}", response_model=EmissionResponse)
async def update_emission(
    emission_id: int,
    emission: EmissionUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an existing emission entry"""
    # MULTI-TENANT: Validate emission belongs to current tenant
    db_emission = get_tenant_record(db, Emission, emission_id, current_user.tenant_id)
    
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Soft delete an emission entry.

    CSRD Compliance: Records are soft-deleted (deleted_at timestamp set) rather
    than physically removed. This preserves audit trail and allows recovery.

    Use POST /{emission_id}/restore to recover a soft-deleted record.
    """
    # MULTI-TENANT: Validate emission belongs to current tenant and soft delete
    emission = soft_delete_tenant_record(db, Emission, emission_id, current_user.tenant_id)

    # Log DELETE action for audit trail (CSRD compliance)
    log_delete(
        db=db,
        entity=emission,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id if hasattr(current_user, 'id') else None
    )

    db.commit()
    return {
        "message": "Emission soft-deleted successfully",
        "id": emission_id,
        "deleted_at": emission.deleted_at.isoformat() if emission else None
    }


@router.post("/{emission_id}/restore")
async def restore_emission(
    emission_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Restore a soft-deleted emission entry.

    Clears the deleted_at timestamp, making the record visible again in queries.
    """
    # MULTI-TENANT: Validate emission belongs to current tenant and restore
    emission = restore_tenant_record(db, Emission, emission_id, current_user.tenant_id)

    if emission:
        # Log RESTORE action for audit trail (CSRD compliance)
        log_restore(
            db=db,
            entity=emission,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id if hasattr(current_user, 'id') else None
        )

        db.commit()
        return {
            "message": "Emission restored successfully",
            "id": emission_id,
            "deleted_at": None
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emission not found"
        )

@router.get("/export/csv")
async def export_emissions_csv(
    scope: Optional[int] = Query(None, ge=1, le=3),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_uncertainty: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Export emissions data as CSV with optional uncertainty data"""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, Emission, current_user.tenant_id)
    
    if scope:
        query = query.filter(Emission.scope == scope)
    
    if start_date:
        query = query.filter(Emission.created_at >= start_date)
    
    if end_date:
        query = query.filter(Emission.created_at <= end_date)
    
    emissions = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)

    # Header with optional uncertainty columns (using actual model attributes)
    headers = [
        'ID', 'Tenant ID', 'Date', 'Scope', 'Category', 'Subcategory',
        'Activity Data', 'Unit', 'Emission Factor', 'Emission Factor Source',
        'Amount (tCO2e)', 'Data Source', 'Data Quality Score',
        'Location', 'Country Code', 'Description'
    ]

    if include_uncertainty:
        headers.extend(['Uncertainty %', 'Lower Bound', 'Upper Bound'])

    writer.writerow(headers)

    # Data rows using actual model attributes
    for emission in emissions:
        scope_value = emission.scope.value if hasattr(emission.scope, 'value') else emission.scope
        data_source = emission.data_source.value if emission.data_source and hasattr(emission.data_source, 'value') else (emission.data_source or '')
        row = [
            emission.id,
            emission.tenant_id,
            emission.created_at.strftime('%Y-%m-%d') if emission.created_at else '',
            scope_value,
            emission.category or '',
            emission.subcategory or '',
            emission.activity_data or '',
            emission.unit or '',
            emission.emission_factor or '',
            emission.emission_factor_source or '',
            emission.amount or '',
            data_source,
            emission.data_quality_score or '',
            emission.location or '',
            emission.country_code or '',
            emission.description or ''
        ]

        if include_uncertainty:
            uncertainty = emission.uncertainty_percentage or 10.0
            lower = (emission.amount or 0) * (1 - uncertainty / 100)
            upper = (emission.amount or 0) * (1 + uncertainty / 100)
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
    current_user: CurrentUser = Depends(get_current_user),
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

            # Sanitize numeric values (handles EU 1.234,56 vs US 1,234.56 formats)
            try:
                activity_data = sanitize_number(row.get('activity_data', 0)) or 0.0
            except NumberFormatError as e:
                errors.append(f"Row {row_num}: Invalid activity_data format - {e}")
                continue

            co2e_total = activity_data * float(factor.factor)

            # MULTI-TENANT: Set tenant_id from current user
            emission = Emission(
                tenant_id=current_user.tenant_id,
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

