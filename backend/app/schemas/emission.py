# backend/app/schemas/emission.py
"""
Pydantic schemas for emissions data - SaaS-Grade API Documentation

These schemas define the contract between the FactorTrace API and its clients.
Every field is documented for OpenAPI/Swagger generation.
"""
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, condecimal, constr
from typing import Optional, Dict, Literal, Union
from datetime import datetime
from enum import IntEnum, Enum


# =============================================================================
# ENUMS - Calculation Method and Dataset Selection
# =============================================================================

class EmissionCalculationMethod(str, Enum):
    """
    Supported emission calculation methods.

    - activity_data: Uses activity-based factors (kWh, liters, km, etc.)
    - spend_based: Uses EXIOBASE spend-based factors (kgCO2e per EUR)
    """
    activity_data = "activity_data"
    spend_based = "spend_based"


class EmissionDatasetPreference(str, Enum):
    """
    Preferred emission factor dataset for calculation.

    - AUTO: Automatically select based on country_code (GB→DEFRA, US→EPA, else DEFRA)
    - DEFRA_2024: UK Government emission factors 2024
    - EPA_2024: US EPA emission factors 2024
    - EXIOBASE_2020: EXIOBASE 3 spend-based factors (for spend_based method)
    """
    auto = "AUTO"
    defra_2024 = "DEFRA_2024"
    epa_2024 = "EPA_2024"
    exiobase_2020 = "EXIOBASE_2020"


class EmissionScope(IntEnum):
    """
    GHG Protocol emission scopes as defined by the Greenhouse Gas Protocol.

    - SCOPE_1: Direct emissions from owned or controlled sources
    - SCOPE_2: Indirect emissions from purchased electricity, steam, heating, cooling
    - SCOPE_3: All other indirect emissions in the value chain
    """
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class EmissionCreate(BaseModel):
    """
    Schema for creating a new emission record.

    Supports two calculation methods:

    **1. Activity-based (default):**
    The API will automatically look up the appropriate emission factor from the
    database based on scope, category, activity_type, and country_code.
    If no matching factor is found, a 422 error is returned.

    **2. Spend-based (EXIOBASE):**
    Set `calculation_method='spend_based'` and provide `spend_amount_eur` to use
    EXIOBASE_2020 spend-based emission factors (kgCO2e per EUR).

    For spend-based calculation, provide ONE of:
    - `exiobase_sector`: Exact EXIOBASE 3 sector name (highest priority)
    - `sector_label`: User-friendly label (e.g., "IT Services") that maps to EXIOBASE
    - `activity_type`: Will be used as fallback for sector mapping

    Country fallback chain: country_code -> ROW_region -> GLOBAL

    **Outlier Warning:**
    EXIOBASE factors >100 kgCO2e/EUR are flagged as potential MRIO artifacts.
    Check the response metadata for `factor_outlier_warning`.
    """

    # Required fields
    scope: int = Field(
        ...,
        ge=1,
        le=3,
        description="GHG Protocol emission scope. 1 = Direct emissions (fuel combustion, company vehicles). 2 = Indirect emissions (purchased electricity). 3 = Value chain emissions.",
        json_schema_extra={"example": 2}
    )

    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Emission category as defined in the emission factors database. Must match exactly. Examples: 'Purchased Electricity', 'Mobile Combustion', 'Stationary Combustion'.",
        json_schema_extra={"example": "Purchased Electricity"}
    )

    activity_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Specific activity type within the category. Must match an entry in the emission factors database. Examples: 'Electricity', 'Diesel', 'Natural Gas'.",
        json_schema_extra={"example": "Electricity"}
    )

    activity_data: float = Field(
        ...,
        gt=0,
        description="Quantity of the activity. The unit must match the emission factor's expected unit (e.g., kWh for electricity, liters for diesel).",
        json_schema_extra={"example": 10000.0}
    )

    unit: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unit of measurement for activity_data. Must be consistent with the emission factor. Common units: 'kWh', 'liters', 'kg', 'm³', 'km'.",
        json_schema_extra={"example": "kWh"}
    )

    # Country code for factor lookup
    country_code: str = Field(
        default="GLOBAL",
        min_length=2,
        max_length=10,
        description="ISO 3166-1 alpha-2 country code for region-specific emission factors. Use 'GLOBAL' for generic factors. Examples: 'DE' (Germany), 'FR' (France), 'US' (United States), 'GB' (United Kingdom).",
        json_schema_extra={"example": "DE"}
    )

    # Optional manual override
    emission_factor: Optional[float] = Field(
        default=None,
        gt=0,
        description="Manual emission factor override in kgCO2e per unit. If provided, bypasses database lookup. Use only when you have a verified custom factor.",
        json_schema_extra={"example": 0.4}
    )

    # Optional metadata
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable description of this emission entry. Useful for audit trails and reporting.",
        json_schema_extra={"example": "Office building electricity consumption Q1 2024"}
    )

    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Physical location or facility name associated with this emission.",
        json_schema_extra={"example": "Berlin HQ - Building A"}
    )

    data_source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Source of the activity data. Examples: 'Utility Invoice', 'Meter Reading', 'Estimate'.",
        json_schema_extra={"example": "Utility Invoice"}
    )

    calculation_method: Optional[str] = Field(
        default="activity_based",
        max_length=50,
        description="Method used for calculation. Values: 'activity_based', 'spend_based', 'average_data'. When 'spend_based', use spend_amount_eur and exiobase_sector fields.",
        json_schema_extra={"example": "activity_based"}
    )

    # Spend-based fields (EXIOBASE integration)
    spend_amount_eur: Optional[float] = Field(
        default=None,
        gt=0,
        description="Spend amount in EUR for spend-based calculation. Required when calculation_method='spend_based'. Uses EXIOBASE 3 emission factors (kgCO2e per EUR).",
        json_schema_extra={"example": 10000.0}
    )

    exiobase_sector: Optional[str] = Field(
        default=None,
        max_length=200,
        description="EXIOBASE sector name for spend-based calculation. Must match an EXIOBASE 3 sector (e.g., 'Motor vehicles', 'Computer programming, consultancy'). If not provided, activity_type will be used for mapping lookup.",
        json_schema_extra={"example": "Computer programming, consultancy and related activities"}
    )

    sector_label: Optional[str] = Field(
        default=None,
        max_length=200,
        description="User-friendly sector label that will be mapped to an EXIOBASE sector. Examples: 'IT Services', 'Office Supplies', 'Car Manufacturing'.",
        json_schema_extra={"example": "IT Services"}
    )

    data_quality_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Data quality score from 0-100 based on GHG Protocol guidance. Higher is better. Considers temporal, geographical, technological representativeness.",
        json_schema_extra={"example": 85.0}
    )

    reporting_period: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Reporting period identifier. Format: 'YYYY' for annual, 'YYYY-QN' for quarterly, 'YYYY-MM' for monthly.",
        json_schema_extra={"example": "2024-Q1"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Activity-based calculation (default)",
                    "description": "Standard activity-based emission calculation using kWh/liters/kg with database factor lookup",
                    "value": {
                        "scope": 2,
                        "category": "Purchased Electricity",
                        "activity_type": "Electricity",
                        "activity_data": 10000.0,
                        "unit": "kWh",
                        "country_code": "DE",
                        "description": "Office building electricity consumption Q1 2024",
                        "location": "Berlin HQ - Building A",
                        "data_source": "Utility Invoice",
                        "reporting_period": "2024-Q1"
                    }
                },
                {
                    "summary": "Spend-based calculation (EXIOBASE)",
                    "description": "Spend-based emission calculation using EXIOBASE_2020 factors (kgCO2e per EUR). Use sector_label for user-friendly input or exiobase_sector for exact EXIOBASE sector matching.",
                    "value": {
                        "scope": 3,
                        "category": "Purchased Goods",
                        "activity_type": "IT Services",
                        "activity_data": 1.0,
                        "unit": "EUR",
                        "country_code": "DE",
                        "calculation_method": "spend_based",
                        "spend_amount_eur": 50000.0,
                        "sector_label": "IT Services",
                        "description": "Software consulting services Q1 2024",
                        "location": "External Vendor",
                        "data_source": "Invoice",
                        "reporting_period": "2024-Q1"
                    }
                },
                {
                    "summary": "Spend-based with direct EXIOBASE sector",
                    "description": "Spend-based calculation using exact EXIOBASE 3 sector name. Use this for precise matching.",
                    "value": {
                        "scope": 3,
                        "category": "Purchased Goods",
                        "activity_type": "Motor vehicles",
                        "activity_data": 1.0,
                        "unit": "EUR",
                        "country_code": "DE",
                        "calculation_method": "spend_based",
                        "spend_amount_eur": 250000.0,
                        "exiobase_sector": "Motor vehicles",
                        "description": "Company vehicle fleet purchase 2024",
                        "data_source": "Purchase Order"
                    }
                }
            ]
        }
    )


class EmissionUpdate(BaseModel):
    """
    Schema for updating an existing emission record.

    All fields are optional. Only provided fields will be updated.
    The emission amount will be automatically recalculated if activity_data
    or emission_factor changes.
    """

    scope: Optional[int] = Field(
        default=None,
        ge=1,
        le=3,
        description="GHG Protocol emission scope (1, 2, or 3).",
        json_schema_extra={"example": 2}
    )

    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Emission category. Must match an entry in the emission factors database.",
        json_schema_extra={"example": "Purchased Electricity"}
    )

    activity_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Specific activity type within the category.",
        json_schema_extra={"example": "Electricity"}
    )

    activity_data: Optional[float] = Field(
        default=None,
        gt=0,
        description="Quantity of the activity. Updating this will trigger recalculation.",
        json_schema_extra={"example": 12000.0}
    )

    unit: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Unit of measurement for activity_data.",
        json_schema_extra={"example": "kWh"}
    )

    country_code: Optional[str] = Field(
        default=None,
        max_length=10,
        description="ISO 3166-1 alpha-2 country code.",
        json_schema_extra={"example": "DE"}
    )

    emission_factor: Optional[float] = Field(
        default=None,
        gt=0,
        description="Manual emission factor override in kgCO2e per unit.",
        json_schema_extra={"example": 0.4}
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable description of this emission entry.",
        json_schema_extra={"example": "Updated: Office building electricity consumption Q1 2024"}
    )

    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Physical location or facility name.",
        json_schema_extra={"example": "Berlin HQ - Building A"}
    )

    data_source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Source of the activity data.",
        json_schema_extra={"example": "Utility Invoice"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "activity_data": 12000.0,
                "description": "Updated: Office building electricity consumption Q1 2024"
            }
        }
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class EmissionResponse(BaseModel):
    """
    Schema for emission record responses.

    Contains the calculated emission amount and all associated metadata.
    The 'amount' field contains the calculated CO2e in tonnes (tCO2e).
    """

    id: int = Field(
        ...,
        description="Unique identifier for this emission record.",
        json_schema_extra={"example": 1}
    )

    scope: int = Field(
        ...,
        description="GHG Protocol emission scope (1, 2, or 3).",
        json_schema_extra={"example": 2}
    )

    category: str = Field(
        ...,
        description="Emission category.",
        json_schema_extra={"example": "Purchased Electricity"}
    )

    activity_type: Optional[str] = Field(
        default=None,
        description="Specific activity type within the category.",
        json_schema_extra={"example": "Electricity"}
    )

    activity_data: float = Field(
        ...,
        description="Quantity of the activity.",
        json_schema_extra={"example": 10000.0}
    )

    unit: str = Field(
        ...,
        description="Unit of measurement for activity_data.",
        json_schema_extra={"example": "kWh"}
    )

    country_code: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code used for factor lookup.",
        json_schema_extra={"example": "DE"}
    )

    emission_factor: Optional[float] = Field(
        default=None,
        description="Emission factor used for calculation in kgCO2e per unit.",
        json_schema_extra={"example": 0.35}
    )

    amount: float = Field(
        ...,
        description="Calculated emission amount in tonnes CO2 equivalent (tCO2e). This is the primary result of the calculation.",
        json_schema_extra={"example": 3.5}
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this emission entry.",
        json_schema_extra={"example": "Office building electricity consumption Q1 2024"}
    )

    location: Optional[str] = Field(
        default=None,
        description="Physical location or facility name.",
        json_schema_extra={"example": "Berlin HQ - Building A"}
    )

    data_quality_score: Optional[float] = Field(
        default=None,
        description="Data quality score from 0-100.",
        json_schema_extra={"example": 85.0}
    )

    uncertainty_percentage: Optional[float] = Field(
        default=None,
        description="Uncertainty percentage for the calculated emission (±%).",
        json_schema_extra={"example": 10.0}
    )

    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when this record was created (UTC).",
        json_schema_extra={"example": "2024-03-15T10:30:00Z"}
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when this record was last updated (UTC).",
        json_schema_extra={"example": "2024-03-15T10:30:00Z"}
    )

    user_id: Optional[int] = Field(
        default=None,
        description="ID of the user who created this record.",
        json_schema_extra={"example": 1}
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "scope": 2,
                "category": "Purchased Electricity",
                "activity_type": "Electricity",
                "activity_data": 10000.0,
                "unit": "kWh",
                "country_code": "DE",
                "emission_factor": 0.35,
                "amount": 3.5,
                "description": "Office building electricity consumption Q1 2024",
                "location": "Berlin HQ - Building A",
                "data_quality_score": 85.0,
                "uncertainty_percentage": 10.0,
                "created_at": "2024-03-15T10:30:00Z",
                "updated_at": "2024-03-15T10:30:00Z",
                "user_id": 1
            }
        }
    )


class EmissionsSummary(BaseModel):
    """
    Schema for aggregated emissions summary.

    Provides totals by scope and category breakdown for dashboard displays
    and regulatory reporting.
    """

    scope1_total: float = Field(
        default=0,
        description="Total Scope 1 emissions in tCO2e (direct emissions).",
        json_schema_extra={"example": 125.5}
    )

    scope2_total: float = Field(
        default=0,
        description="Total Scope 2 emissions in tCO2e (purchased energy).",
        json_schema_extra={"example": 89.3}
    )

    scope3_total: float = Field(
        default=0,
        description="Total Scope 3 emissions in tCO2e (value chain).",
        json_schema_extra={"example": 456.2}
    )

    total_emissions: float = Field(
        default=0,
        description="Total emissions across all scopes in tCO2e.",
        json_schema_extra={"example": 671.0}
    )

    by_category: Dict[str, float] = Field(
        default_factory=dict,
        description="Emissions breakdown by category in tCO2e. Keys are category names, values are totals.",
        json_schema_extra={"example": {"Purchased Electricity": 89.3, "Mobile Combustion": 125.5, "Business Travel": 200.0}}
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "scope1_total": 125.5,
                "scope2_total": 89.3,
                "scope3_total": 456.2,
                "total_emissions": 671.0,
                "by_category": {
                    "Purchased Electricity": 89.3,
                    "Mobile Combustion": 125.5,
                    "Business Travel": 200.0,
                    "Purchased Goods": 256.2
                }
            }
        }
    )


# =============================================================================
# ERROR RESPONSE SCHEMAS (for OpenAPI documentation)
# =============================================================================

class EmissionFactorNotFoundError(BaseModel):
    """
    Error response when no matching emission factor is found in the database.

    This typically occurs when the combination of scope/category/activity_type/country_code
    doesn't match any entry in the emission factors table.
    """

    detail: str = Field(
        ...,
        description="Error message describing the missing factor lookup key.",
        json_schema_extra={"example": "No emission factor found for key: (scope_2, Purchased Electricity, Electricity, XX)"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "No emission factor found for key: (scope_2, Purchased Electricity, Electricity, XX)"
            }
        }
    )


class ValidationErrorResponse(BaseModel):
    """
    Standard validation error response from FastAPI/Pydantic.
    """

    detail: list = Field(
        ...,
        description="List of validation errors with location and message.",
        json_schema_extra={
            "example": [
                {
                    "loc": ["body", "activity_data"],
                    "msg": "Input should be greater than 0",
                    "type": "greater_than"
                }
            ]
        }
    )


# =============================================================================
# UNIFIED CALCULATION API SCHEMAS (Production-Grade)
# =============================================================================

class EmissionCalculationRequest(BaseModel):
    """
    Unified request schema for emission calculations.

    Supports both activity-based (DEFRA/EPA) and spend-based (EXIOBASE) methods.

    **Activity-based calculation:**
    - Set `method="activity_data"`
    - Provide `amount` (activity quantity), `unit`, `category`, `activity_type`
    - Optional: `dataset` to specify DEFRA_2024 or EPA_2024 (default: AUTO)

    **Spend-based calculation:**
    - Set `method="spend_based"`
    - Provide `amount` (spend in EUR)
    - Provide `sector_label` (user-friendly) or `exiobase_activity_type` (exact EXIOBASE sector)
    """

    method: EmissionCalculationMethod = Field(
        ...,
        description="Calculation method: 'activity_data' for activity-based or 'spend_based' for EXIOBASE.",
        json_schema_extra={"example": "activity_data"}
    )

    dataset: EmissionDatasetPreference = Field(
        default=EmissionDatasetPreference.auto,
        description="Preferred emission factor dataset. AUTO selects based on country (GB→DEFRA, US→EPA).",
        json_schema_extra={"example": "AUTO"}
    )

    scope: Union[str, int] = Field(
        ...,
        description="GHG Protocol scope: 1, 2, or 3 (or 'SCOPE_1', 'SCOPE_2', 'SCOPE_3').",
        json_schema_extra={"example": 2}
    )

    country_code: constr(strip_whitespace=True, min_length=2, max_length=10) = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code (e.g., 'DE', 'US', 'GB'). Use 'GLOBAL' for generic factors.",
        json_schema_extra={"example": "DE"}
    )

    amount: condecimal(gt=Decimal("0")) = Field(
        ...,
        description="Activity amount (kWh, liters, etc.) for activity-based, or spend amount in EUR for spend-based.",
        json_schema_extra={"example": "10000"}
    )

    unit: constr(strip_whitespace=True, min_length=1) = Field(
        ...,
        description="Unit of measurement. For activity-based: 'kWh', 'liters', 'km', etc. For spend-based: 'EUR'.",
        json_schema_extra={"example": "kWh"}
    )

    # Activity-based fields
    category: Optional[str] = Field(
        default=None,
        description="Emission category for activity-based calculation (e.g., 'electricity', 'stationary_combustion').",
        json_schema_extra={"example": "electricity"}
    )

    activity_type: Optional[str] = Field(
        default=None,
        description="Specific activity type within category (e.g., 'Electricity - Grid Average', 'Natural Gas').",
        json_schema_extra={"example": "Electricity - Grid Average"}
    )

    # Spend-based fields
    sector_label: Optional[str] = Field(
        default=None,
        description="User-friendly sector label for spend-based (e.g., 'IT Services', 'Car Manufacturing').",
        json_schema_extra={"example": "IT Services"}
    )

    exiobase_activity_type: Optional[str] = Field(
        default=None,
        description="Exact EXIOBASE sector name. Takes priority over sector_label if both provided.",
        json_schema_extra={"example": "Computer and related services (72)"}
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "examples": [
                {
                    "summary": "Activity-based: Electricity in Germany",
                    "value": {
                        "method": "activity_data",
                        "dataset": "AUTO",
                        "scope": 2,
                        "country_code": "DE",
                        "amount": "10000",
                        "unit": "kWh",
                        "category": "electricity",
                        "activity_type": "Electricity - Grid Average"
                    }
                },
                {
                    "summary": "Spend-based: IT Services in Germany",
                    "value": {
                        "method": "spend_based",
                        "dataset": "EXIOBASE_2020",
                        "scope": 3,
                        "country_code": "DE",
                        "amount": "50000",
                        "unit": "EUR",
                        "sector_label": "IT Services"
                    }
                }
            ]
        }
    )


class FactorNotFoundError(BaseModel):
    """
    Structured error response when no emission factor is found.
    """
    error: str = Field(
        default="FACTOR_NOT_FOUND",
        description="Error code"
    )
    lookup_key: Dict = Field(
        ...,
        description="The lookup parameters that failed to find a factor"
    )


class EmissionCalculationResponse(BaseModel):
    """
    Response schema for unified emission calculations.

    Contains calculated emissions in kgCO2e plus all metadata about the
    factor used, method applied, and any warnings.
    """

    emissions_kg_co2e: float = Field(
        ...,
        description="Calculated emissions in kilograms of CO2 equivalent (kgCO2e).",
        json_schema_extra={"example": 3500.0}
    )

    factor_value: float = Field(
        ...,
        description="Emission factor value used for calculation.",
        json_schema_extra={"example": 0.35}
    )

    factor_unit: str = Field(
        ...,
        description="Unit of the emission factor (e.g., 'kgCO2e/kWh', 'kgCO2e/EUR').",
        json_schema_extra={"example": "kgCO2e/kWh"}
    )

    dataset_used: str = Field(
        ...,
        description="Emission factor dataset that was actually used.",
        json_schema_extra={"example": "DEFRA_2024"}
    )

    method_used: str = Field(
        ...,
        description="Calculation method that was applied ('activity_data' or 'spend_based').",
        json_schema_extra={"example": "activity_data"}
    )

    scope: Union[str, int] = Field(
        ...,
        description="GHG Protocol scope as provided in the request.",
        json_schema_extra={"example": 2}
    )

    country_code: str = Field(
        ...,
        description="Country code used for factor lookup (may differ from request if fallback applied).",
        json_schema_extra={"example": "DE"}
    )

    activity_type_used: Optional[str] = Field(
        default=None,
        description="Activity type used in the lookup (for activity-based calculations).",
        json_schema_extra={"example": "Electricity - Grid Average"}
    )

    sector_used: Optional[str] = Field(
        default=None,
        description="EXIOBASE sector used (for spend-based calculations).",
        json_schema_extra={"example": "Computer and related services (72)"}
    )

    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or warnings about the calculation.",
        json_schema_extra={"example": "Factor outlier warning: value exceeds 100 kgCO2e/EUR threshold"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "emissions_kg_co2e": 3500.0,
                "factor_value": 0.35,
                "factor_unit": "kgCO2e/kWh",
                "dataset_used": "DEFRA_2024",
                "method_used": "activity_data",
                "scope": 2,
                "country_code": "DE",
                "activity_type_used": "Electricity - Grid Average",
                "sector_used": None,
                "notes": None
            }
        }
    )
