# app/schemas/report.py
"""
CSRD/ESRS Report Schemas
========================
Pydantic models for CSRD-style XHTML/iXBRL reporting.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal


class ScopeBreakdown(BaseModel):
    """Breakdown of emissions by scope."""
    scope_1_kg_co2e: float = Field(
        default=0.0,
        description="Scope 1 direct emissions in kg CO2e"
    )
    scope_2_kg_co2e: float = Field(
        default=0.0,
        description="Scope 2 indirect energy emissions in kg CO2e"
    )
    scope_3_kg_co2e: float = Field(
        default=0.0,
        description="Scope 3 value chain emissions in kg CO2e"
    )


class CSRDSummaryRequest(BaseModel):
    """
    Request for CSRD-style summary report.

    Filters emissions data by organization and reporting period.
    """
    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Legal name of the reporting organization"
    )
    reporting_year: int = Field(
        ...,
        ge=2020,
        le=2100,
        description="Reporting year (e.g., 2024)"
    )
    reporting_period_start: Optional[date] = Field(
        default=None,
        description="Start date of reporting period (defaults to Jan 1 of reporting_year)"
    )
    reporting_period_end: Optional[date] = Field(
        default=None,
        description="End date of reporting period (defaults to Dec 31 of reporting_year)"
    )
    lei: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Legal Entity Identifier (LEI) if available"
    )
    include_methodology_notes: bool = Field(
        default=True,
        description="Include methodology notes in the report"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_name": "Acme Corporation GmbH",
                "reporting_year": 2024,
                "lei": "5493001KJTIIGC8Y1R12",
                "include_methodology_notes": True
            }
        }


class CSRDSummaryResponse(BaseModel):
    """
    Response containing CSRD-style summary data.

    Includes both structured data and XHTML content.
    """
    organization_name: str = Field(
        ...,
        description="Legal name of the reporting organization"
    )
    reporting_year: int = Field(
        ...,
        description="Reporting year"
    )
    reporting_period_start: date = Field(
        ...,
        description="Start date of reporting period"
    )
    reporting_period_end: date = Field(
        ...,
        description="End date of reporting period"
    )
    lei: Optional[str] = Field(
        default=None,
        description="Legal Entity Identifier"
    )

    # Emissions totals
    total_emissions_kg_co2e: float = Field(
        ...,
        description="Total emissions across all scopes in kg CO2e"
    )
    total_emissions_tonnes_co2e: float = Field(
        ...,
        description="Total emissions across all scopes in tonnes CO2e"
    )

    # Scope breakdown
    scope_breakdown: ScopeBreakdown = Field(
        ...,
        description="Emissions breakdown by scope"
    )

    # Data quality
    calculation_count: int = Field(
        default=0,
        description="Number of emission calculations included"
    )
    datasets_used: List[str] = Field(
        default_factory=list,
        description="List of emission factor datasets used"
    )

    # XHTML output
    xhtml_content: str = Field(
        ...,
        description="XHTML document with embedded iXBRL tags for ESRS E1 disclosure"
    )

    # Metadata
    generated_at: str = Field(
        ...,
        description="ISO 8601 timestamp when report was generated"
    )
    factortrace_version: str = Field(
        default="1.0.0",
        description="FactorTrace API version used"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_name": "Acme Corporation GmbH",
                "reporting_year": 2024,
                "reporting_period_start": "2024-01-01",
                "reporting_period_end": "2024-12-31",
                "lei": "5493001KJTIIGC8Y1R12",
                "total_emissions_kg_co2e": 125000.0,
                "total_emissions_tonnes_co2e": 125.0,
                "scope_breakdown": {
                    "scope_1_kg_co2e": 15000.0,
                    "scope_2_kg_co2e": 35000.0,
                    "scope_3_kg_co2e": 75000.0
                },
                "calculation_count": 42,
                "datasets_used": ["DEFRA_2024", "EXIOBASE_2020"],
                "xhtml_content": "<!DOCTYPE html>...",
                "generated_at": "2024-12-15T14:30:00Z",
                "factortrace_version": "1.0.0"
            }
        }


class ReportError(BaseModel):
    """Error response for report generation failures."""
    error: str = Field(
        ...,
        description="Error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[dict] = Field(
        default=None,
        description="Additional error details"
    )
