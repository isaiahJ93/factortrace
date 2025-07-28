from __future__ import annotations


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

    "
"
ESG Compliance Backend - Emission Voucher Types
Compliant with: CSRD, CBAM, ESRS E1-E6, GHG Protocol, EFRAG 2025
Version: 2.0.0
"
"

    from dataclasses import dataclass, field
    from typing import Optional, List, Dict, Union, Literal
    from enum import Enum, auto
    from decimal import Decimal
    from datetime import datetime, date
    from uuid import UUID

    from pydantic import BaseModel, Field, ConfigDict

    class FUNCTION():
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
    product_cn_code: str=Field(alias="product_cn_code")"

    model_config=ConfigDict(populate_by_name=True, validate_assignment=True)

    class FUNCTION():
    tier_1="tier_1"
    tier_2="tier_2"
    tier_3="tier_3"

    # ============================================================================
    # CORE ENUMERATIONS - Aligned with ESRS/CBAM Taxonomies
    # ============================================================================


    class FUNCTION():
    "
"
    SCOPE_1="scope_1"
    SCOPE_2_LOCATION="scope_2_location"
    SCOPE_2_MARKET="scope_2_market"
    SCOPE_3="scope_3"

    class FUNCTION():
    "
"
    CAT_1_PURCHASED_GOODS="1_purchased_goods_services"
    CAT_2_CAPITAL_GOODS="2_capital_goods"
    CAT_3_FUEL_ENERGY="3_fuel_energy_activities"
    CAT_4_UPSTREAM_TRANSPORT="4_upstream_transportation"
    CAT_5_WASTE_OPERATIONS="5_waste_generated_operations"
    CAT_6_BUSINESS_TRAVEL="6_business_travel"
    CAT_7_EMPLOYEE_COMMUTING="7_employee_commuting"
    CAT_8_UPSTREAM_LEASED="8_upstream_leased_assets"
    CAT_9_DOWNSTREAM_TRANSPORT="9_downstream_transportation"
    CAT_10_PROCESSING_SOLD="10_processing_sold_products"
    CAT_11_USE_SOLD="11_use_sold_products"
    CAT_12_EOL_SOLD="12_end_of_life_sold_products"
    CAT_13_DOWNSTREAM_LEASED="13_downstream_leased_assets"
    CAT_14_FRANCHISES="14_franchises"
    CAT_15_INVESTMENTS="15_investments"


    class FUNCTION():
    "
"
    AR4="AR4"
    AR5="AR5"
    AR6="AR6"


    class FUNCTION():
    "
"
    tier_1="tier_1"
    tier_2="tier_2"
    tier_3="tier_3"

    class FUNCTION():
    "
"
    NONE="none"
    LIMITED="limited_assurance"
    REASONABLE="reasonable_assurance"


    class FUNCTION():
    "
"
    IMPACT="impact_materiality"
    FINANCIAL="financial_materiality"
    DOUBLE="double_materiality"


    class FUNCTION():
    "
"
    MATERIALS="materials"
    LOGISTICS="logistics"
    ENERGY="energy"
    MANUFACTURING="manufacturing"
    SERVICES="services"
    AGRICULTURE="agriculture"
    CONSTRUCTION="construction"
    WASTE="waste"


    class FUNCTION():
    "
"
    CEMENT="2523"
    ELECTRICITY="2716"
    FERTILIZERS="3102-3105"
    IRON_STEEL="7201-7229"
    ALUMINIUM="7601-7616"
    HYDROGEN="2804"

    @ dataclass
    class EmissionFactor:
    factor_id: str
    value: Decimal
    unit: str
    source: str
    source_year: int
    tier: DataQualityTier

    @ dataclass
    class GHGBreakdown:
    gas_type: str
    amount: Decimal
    gwp_factor: Decimal
    gwp_version: GWPVersion


    @ dataclass
    class DataQuality:
    tier: DataQualityTier
    score: Decimal
    temporal_representativeness: Decimal
    geographical_representativeness: Decimal
    technological_representativeness: Decimal
    completeness: Decimal
    uncertainty_percent: Decimal

    class FUNCTION():
    "
"
    UPSTREAM="upstream"
    OPERATIONS="operations"
    DOWNSTREAM="downstream"



# Remaining classes (GHGEmission, EmissionFactor, etc.) truncated for brevity
# Add complete class definitions as needed following this format.)
