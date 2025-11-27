# backend/app/schemas/emission.py
"""
Pydantic schemas for emissions data - SaaS-Grade API Documentation

These schemas define the contract between the FactorTrace API and its clients.
Every field is documented for OpenAPI/Swagger generation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Literal
from datetime import datetime
from enum import IntEnum


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

    The API will automatically look up the appropriate emission factor from the
    database based on scope, category, activity_type, and country_code.
    If no matching factor is found, a 422 error is returned.
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
        default=None,
        max_length=50,
        description="Method used for calculation. Values: 'activity_based', 'spend_based', 'average_data'.",
        json_schema_extra={"example": "activity_based"}
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
            "example": {
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
