from __future__ import annotations
from factortrace.shared_enums import (
    GWPVersionEnum,
    TierLevelEnum,
    Scope3CategoryEnum,
    ScopeLevelEnum,
    VerificationLevelEnum,
    ConsolidationMethodEnum,
    DataQualityTierEnum,
    ValueChainStageEnum,
    UncertaintyDistributionEnum,
    TemporalGranularityEnum,
    GasTypeEnum,

"""
ESG Compliance Backend - Emission Voucher Types
Compliant with: CSRD, CBAM, ESRS E1-E6, GHG Protocol, EFRAG 2025
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union, Literal
from enum import Enum, auto
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class VoucherInput(BaseModel):
    supplier_id: str
    supplier_name: str
    legal_entity_identifier: str
    product_category: str
    cost: float
    material_type: str
    origin_country: str
    emission_factor: float
    emission_factor_id: str
    fallback_factor_used: bool
    product_cn_code: str = Field(alias="product_cn_code")

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

class TierLevelEnum(str, Enum):
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"

# ============================================================================
# CORE ENUMERATIONS - Aligned with ESRS/CBAM Taxonomies
# ============================================================================


class EmissionScope(str, Enum):
    """GHG Protocol Scopes"""
    SCOPE_1 = "scope_1"  # Direct emissions
    SCOPE_2_LOCATION = "scope_2_location"  # Location-based electricity
    SCOPE_2_MARKET = "scope_2_market"  # Market-based electricity
    SCOPE_3 = "scope_3"  # Value chain emissions

class Scope3Category(str, Enum):
    """ESRS E1-48 Scope 3 Categories (15 categories per GHG Protocol)"""
    CAT_1_PURCHASED_GOODS = "1_purchased_goods_services"
    CAT_2_CAPITAL_GOODS = "2_capital_goods"
    CAT_3_FUEL_ENERGY = "3_fuel_energy_activities"
    CAT_4_UPSTREAM_TRANSPORT = "4_upstream_transportation"
    CAT_5_WASTE_OPERATIONS = "5_waste_generated_operations"
    CAT_6_BUSINESS_TRAVEL = "6_business_travel"
    CAT_7_EMPLOYEE_COMMUTING = "7_employee_commuting"
    CAT_8_UPSTREAM_LEASED = "8_upstream_leased_assets"
    CAT_9_DOWNSTREAM_TRANSPORT = "9_downstream_transportation"
    CAT_10_PROCESSING_SOLD = "10_processing_sold_products"
    CAT_11_USE_SOLD = "11_use_sold_products"
    CAT_12_EOL_SOLD = "12_end_of_life_sold_products"
    CAT_13_DOWNSTREAM_LEASED = "13_downstream_leased_assets"
    CAT_14_FRANCHISES = "14_franchises"
    CAT_15_INVESTMENTS = "15_investments"


class GWPVersion(str, Enum):
    """IPCC Assessment Report GWP versions"""
    AR4 = "AR4"  # Legacy
    AR5 = "AR5"  # Current standard
    AR6 = "AR6"  # CSRD mandatory from 2025


class DataQualityTier(str, Enum):
    """IPCC 2019 Refinement Tier Classification"""
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"

class VerificationLevel(str, Enum):
    """CSRD Article 19b Assurance Levels"""
    NONE = "none"
    LIMITED = "limited_assurance"
    REASONABLE = "reasonable_assurance"


class MaterialityType(str, Enum):
    """ESRS Double Materiality"""
    IMPACT = "impact_materiality"
    FINANCIAL = "financial_materiality"
    DOUBLE = "double_materiality"


class ProductCategory(str, Enum):
    """Extended NACE Rev.2 aligned categories"""
    MATERIALS = "materials"
    LOGISTICS = "logistics"
    ENERGY = "energy"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    AGRICULTURE = "agriculture"
    CONSTRUCTION = "construction"
    WASTE = "waste"


class CBAMProductCode(str, Enum):
    """CBAM Regulation Annex I Product Codes"""
    CEMENT = "2523"
    ELECTRICITY = "2716"
    FERTILIZERS = "3102-3105"
    IRON_STEEL = "7201-7229"
    ALUMINIUM = "7601-7616"
    HYDROGEN = "2804"

@dataclass
class EmissionFactor:
    factor_id: str
    value: Decimal
    unit: str
    source: str
    source_year: int
    tier: DataQualityTier

@dataclass
class GHGBreakdown:
    gas_type: str
    amount: Decimal
    gwp_factor: Decimal
    gwp_version: GWPVersion


@dataclass
class DataQuality:
    tier: DataQualityTier
    score: Decimal
    temporal_representativeness: Decimal
    geographical_representativeness: Decimal
    technological_representativeness: Decimal
    completeness: Decimal
    uncertainty_percent: Decimal

class ValueChainStageEnum(str, Enum):
    """Stages of the value chain for Scope 3 classification"""
    UPSTREAM = "upstream"
    OPERATIONS = "operations"
    DOWNSTREAM = "downstream"


)
# Remaining classes (GHGEmission, EmissionFactor, etc.) truncated for brevity
# Add complete class definitions as needed following this format.)
