from __future__ import annotations

"""Core emissions utilities & data models.

This module handles:
1. Emission-factor lookup against the SQLite factor database.
2. Utility helpers for CO2-e calculations & quality scoring.
3. Pydantic models that describe emission-related payloads
   used across the FactorTrace code-base.

Note: Duplicated definitions were removed; we now rely on the
canonical models imported from ``factortrace.models`` to avoid
schema drift between modules.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
import sqlite3
from typing import Any, Optional, List

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────
# FactorTrace model imports (canonical definitions)
# ──────────────────────────────────────────────────────────────
from factortrace.models.types import EmissionFactor
from factortrace.models.climate import TargetTypeEnum
from factortrace.models.uncertainty_model import UncertaintyAssessment  # single source of truth
from factortrace.enums import (
    ScopeLevelEnum,  # ✅ correct
    Scope3CategoryEnum,
    ValueChainStageEnum,
    GWPVersionEnum,
    ConsolidationMethodEnum,
)

# ──────────────────────────────────────────────────────────────
# Constants / simple enums
# ──────────────────────────────────────────────────────────────

class ProductCategory(str, Enum):
    """High-level product categories for emission-factor lookup."""

    METALS = "metals"
    TEXTILES = "textiles"
    CHEMICALS = "chemicals"
    # Extend as required.


DB_PATH: str = "data/emissions_factors.db"  # single source of truth

# ──────────────────────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────────────────────

def lookup_factor(
    country: str,
    material_type: str,
    category: ProductCategory,
) -> EmissionFactor:
    """Return an :class:`EmissionFactor` for the given key tuple.

    Falls back to a default factor + quality score if no specific
    record exists in the SQLite database.
    """

    query = (
        "SELECT factor, quality_score \n"
        "  FROM emission_factors \n"
        " WHERE country = ? AND material_type = ? AND category = ?"
    )

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(query, (country, material_type, category.value))
        row: Optional[tuple[Any, ...]] = cursor.fetchone()

    if row is not None:
        factor, quality_score = row
    else:
        # ⤵︎ sensible defaults if DB record missing
        factor, quality_score = 2.5, "F"

    return EmissionFactor(
        country=country,
        material_type=material_type,
        category=category,
        factor=factor,
        quality_score=quality_score,
    )


# ──────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────

def calculate_co2e(cost: float, factor: float) -> float:
    """Simple CO₂-e = *cost × factor* helper."""

    return cost * factor


def score_quality(factor: EmissionFactor) -> str:
    """Return letter quality score (A–F); default "F" if missing."""

    return factor.quality_score or "F"

# ──────────────────────────────────────────────────────────────
# Domain models
# ──────────────────────────────────────────────────────────────

class EmissionAmount(BaseModel):
    """Generic CO₂-e amount wrapper."""

    value: Decimal
    unit: str = Field(default="tCO2e", pattern="^tCO2e$")


class Scope2Emissions(BaseModel):
    location_based: EmissionAmount
    market_based: EmissionAmount
    residual_mix_factor: Optional[str] = None


class EmissionData(BaseModel):
    # context
    scope: ScopeEnum
    scope3_category: Optional[Scope3CategoryEnum] = None
    value_chain_stage: Optional[ValueChainStageEnum] = None

    # emissions data
    scope1_emissions: Optional[EmissionAmount] = None
    scope2_emissions: Optional[Scope2Emissions] = None
    scope3_emissions: Optional[EmissionAmount] = None
    biogenic_emissions: Optional[EmissionAmount] = None
    carbon_removals: Optional[EmissionAmount] = None

    embedded_emissions_intensity: Optional[Decimal] = Field(
        default=None, description="Unit: tCO2e/t"
    )

    # methodology
    ghg_breakdown: Optional[dict[str, Decimal]] = None
    emission_factor: Optional[dict[str, Any]] = None
    calculation_method: Optional[dict[str, Any]] = None

    # meta
    gwp_version: GWPVersionEnum = GWPVersionEnum.AR6_100
    consolidation_method: ConsolidationMethodEnum
    carbon_price_paid: Optional[Decimal] = None


class BaseYearReference(BaseModel):
    base_year: int
    base_year_emissions: EmissionAmount
    recalculation_policy: Optional[str] = None


class TargetReference(BaseModel):
    target_id: str
    target_type: TargetTypeEnum
    target_year: int
    reduction_percentage: Decimal
    validation_body: Optional[str] = None


class ClimateTargets(BaseModel):
    target_reference: List[TargetReference]
