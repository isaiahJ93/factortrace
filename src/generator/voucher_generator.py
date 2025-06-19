"""
CSRD/ESRS E1 and CBAM-compliant Scope 3 emission voucher generator.

Implements voucher generation and XML serialization aligned with:
- ESRS E1-6 (Climate change) data points with AR6 GWP
- CBAM Implementing Regulation (EU) 2023/1773
- GHG Protocol Scope 1-3 with full category breakdown
- IPCC Tier 1-3 methodology with uncertainty quantification

Version: 2.0.0
Requires: lxml, Python 3.11+
"""

from __future__ import annotations

import hashlib
import logging
from enum import Enum
import uuid
from factortrace.models.common_enums import TierLevelEnum
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from factortrace.models.uncertainty_model import (
    TierLevelEnum,
    ConsolidationMethodEnum,
    UncertaintyDistributionEnum,
)
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import lru_cache
import redis

from lxml import etree
from lxml.etree import Element, QName, SubElement, XMLSchema, XMLSyntaxError

# Configure audit logging per ESRS 1 §76
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# REGULATORY CONSTANTS - Aligned with ESRS E1 & CBAM                          #
# --------------------------------------------------------------------------- #

# ISO 20022 compliant namespaces
NAMESPACE = "urn:iso:std:20022:tech:xsd:esrs.e1.002.01"  # v2 for AR6
CBAM_NAMESPACE = "urn:eu:cbam:xsd:declaration:001.01"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP = {
    None: NAMESPACE,
    "cbam": CBAM_NAMESPACE,
    "xsi": XSI_NAMESPACE
}

# Schema version management
SCHEMA_VERSION = "2.0.0"
ESRS_TAXONOMY_VERSION = "2025.1"

# --------------------------------------------------------------------------- #
# ENUMERATIONS - Full Regulatory Taxonomy                                     #
# --------------------------------------------------------------------------- #

class EmissionScope(str, Enum):
    """GHG Protocol Scopes"""
    SCOPE_1 = "scope_1"
    SCOPE_2_LOCATION = "scope_2_location"
    SCOPE_2_MARKET = "scope_2_market"
    SCOPE_3 = "scope_3"


class Scope3Category(str, Enum):
    """ESRS E1-48 Scope 3 Categories"""
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
    """IPCC Assessment Report versions"""
    AR4 = "AR4"
    AR5 = "AR5"
    AR6 = "AR6"  # Mandatory from 2025


class DataQualityTier(str, Enum):
    """IPCC 2019 Refinement Tiers"""
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"


class CBAMProductCode(str, Enum):
    """CBAM Annex I Products"""
    CEMENT = "2523"
    ELECTRICITY = "2716"
    FERTILIZERS_31 = "3102"
    FERTILIZERS_31_105 = "3105"
    IRON_STEEL = "72"
    ALUMINIUM = "76"
    HYDROGEN = "2804"


# --------------------------------------------------------------------------- #
# GWP FACTORS - AR6 Values                                                    #
# --------------------------------------------------------------------------- #

# IPCC AR6 GWP100 values (CSRD mandatory from 2025)
AR6_GWP_FACTORS = {
    "CO2": Decimal("1"),
    "CH4": Decimal("29.8"),    # Fossil CH4
    "CH4_BIO": Decimal("27.2"), # Biogenic CH4
    "N2O": Decimal("273"),
    "SF6": Decimal("25200"),
    "NF3": Decimal("17400"),
    "HFC-23": Decimal("14600"),
    "HFC-32": Decimal("771"),
    "HFC-125": Decimal("3740"),
    "HFC-134a": Decimal("1530"),
    "HFC-143a": Decimal("5810"),
    "HFC-152a": Decimal("164"),
    "HFC-227ea": Decimal("3860"),
    "HFC-236fa": Decimal("8690"),
    "HFC-245fa": Decimal("962"),
    "HFC-365mfc": Decimal("914"),
    "HFC-43-10mee": Decimal("1650"),
    "PFC-14": Decimal("7380"),
    "PFC-116": Decimal("12400"),
    "PFC-218": Decimal("9290"),
    "PFC-318": Decimal("10300"),
    "PFC-3-1-10": Decimal("10300"),
    "PFC-4-1-12": Decimal("9430"),
    "PFC-5-1-14": Decimal("9710"),
    "PFC-6-1-16": Decimal("9920"),
}

# Legacy factors for comparison
AR5_GWP_FACTORS = {
    "CO2": Decimal("1"),
    "CH4": Decimal("28"),
    "N2O": Decimal("265"),
    "SF6": Decimal("23500"),
}

# --------------------------------------------------------------------------- #
# CBAM FALLBACK FACTORS                                                       #
# --------------------------------------------------------------------------- #

# CBAM Annex VI default emission factors (tCO2e/tonne)
CBAM_FALLBACK_FACTORS = {
    CBAMProductCode.CEMENT: {
        "tier_1": Decimal("0.918"),  # Global average
        "tier_2_eu": Decimal("0.766"),  # EU average
        "tier_2_china": Decimal("0.944"),
        "tier_2_india": Decimal("0.931"),
        "tier_2_us": Decimal("0.818"),
    },
    CBAMProductCode.IRON_STEEL: {
        "tier_1": Decimal("2.134"),  # Global average
        "tier_2_eu": Decimal("1.328"),
        "tier_2_china": Decimal("2.247"),
        "tier_2_india": Decimal("2.556"),
        "tier_2_brazil": Decimal("1.468"),
    },
    CBAMProductCode.ALUMINIUM: {
        "tier_1": Decimal("16.518"),  # Global average
        "tier_2_eu": Decimal("6.743"),
        "tier_2_china": Decimal("13.398"),
        "tier_2_canada": Decimal("1.904"),  # Hydro-based
        "tier_2_middle_east": Decimal("15.234"),
    },
    CBAMProductCode.ELECTRICITY: {
        "tier_1": Decimal("0.493"),  # Global grid average (tCO2e/MWh)
        "tier_2_eu": Decimal("0.269"),
        "tier_2_china": Decimal("0.581"),
        "tier_2_india": Decimal("0.722"),
        "tier_2_france": Decimal("0.052"),  # Nuclear
        "tier_2_poland": Decimal("0.773"),  # Coal
    },
    CBAMProductCode.HYDROGEN: {
        "tier_1": Decimal("10.125"),  # SMR global average
        "tier_2_grey": Decimal("9.052"),  # Natural gas SMR
        "tier_2_blue": Decimal("3.621"),  # With CCS
        "tier_2_green": Decimal("0.336"),  # Renewable electricity
    }
}

# --------------------------------------------------------------------------- #
# DATA STRUCTURES                                                             #
# --------------------------------------------------------------------------- #

@dataclass
class EmissionFactorData:
    """Enhanced emission factor with uncertainty"""
    factor_id: str
    value: Decimal
    unit: str
    source: str
    source_year: int
    quality_tier: DataQualityTier
    
    # Uncertainty (CSRD Article 29a)
    uncertainty_percent: Decimal = Decimal("10")  # Default ±10%
    confidence_level: Decimal = Decimal("95")
    distribution: str = "lognormal"
    
    # Specificity
    country_code: Optional[str] = None
    technology: Optional[str] = None
    
    def get_uncertainty_range(self) -> Tuple[Decimal, Decimal]:
        """Calculate uncertainty bounds"""
        lower = self.value * (1 - self.uncertainty_percent / 100)
        upper = self.value * (1 + self.uncertainty_percent / 100)
        return (lower, upper)

from pydantic import BaseModel, Field

class VoucherInput(BaseModel):
    # === Required fields ===
    reporting_undertaking_id: str
    supplier_id: str
    supplier_name: str
    tier: TierLevelEnum = Field(default=TierLevelEnum.tier_1)
    emission_scope: EmissionScope
    product_cn_code: str
    product_category: str
    activity_description: str
    quantity: Decimal
    quantity_unit: str
    installation_country: str
    reporting_period_start: date
    reporting_period_end: date

    # === Optional / defaults ===
    emission_factor_id: Optional[str] = None
    legal_entity_identifier: Optional[str] = None
    scope3_category: Optional[Scope3Category] = None
    use_fallback_factor: bool = False
    monetary_value: Optional[Decimal] = None
    currency: str = "EUR"
    installation_id: Optional[str] = None
    embedded_emissions_direct: Optional[Decimal] = None
    embedded_emissions_indirect: Optional[Decimal] = None
    carbon_price_paid: Optional[Decimal] = None
    verifier_accreditation_id: Optional[str] = None
    material_type: Optional[str] = None
    quantity: Optional[Decimal] = None
    cost: Optional[Decimal] = Field(default=None, alias="quantity")  # accept “cost” as alias

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }
# --------------------------------------------------------------------------- #
# EMISSION CALCULATION ENGINE                                                 #
# --------------------------------------------------------------------------- #

class EmissionCalculator:
    """CSRD-compliant emission calculation with AR6 GWP"""
    
    def __init__(self, gwp_version: GWPVersion = GWPVersion.AR6):
        self.gwp_version = gwp_version
        self.gwp_factors = AR6_GWP_FACTORS if gwp_version == GWPVersion.AR6 else AR5_GWP_FACTORS
        
    def calculate_emissions(
        self,
        activity_data: Decimal,
        emission_factor: EmissionFactorData,
        gas_composition: Optional[Dict[str, Decimal]] = None
    ) -> Tuple[Decimal, Dict[str, Any]]:
        """
        Calculate total CO2e emissions with uncertainty propagation.
        
        Returns:
            Tuple of (total_co2e, calculation_details)
        """
        if gas_composition is None:
            # Default: 100% CO2
            gas_composition = {"CO2": Decimal("1.0")}
        
        # Calculate emissions by gas
        emissions_by_gas = {}
        total_co2e = Decimal("0")
        
        for gas, fraction in gas_composition.items():
            if gas in self.gwp_factors:
                gas_emissions = activity_data * emission_factor.value * fraction
                co2e_emissions = gas_emissions * self.gwp_factors[gas]
                
                emissions_by_gas[gas] = {
                    "amount": gas_emissions,
                    "co2e": co2e_emissions,
                    "gwp_factor": self.gwp_factors[gas]
                }
                
                total_co2e += co2e_emissions
        
        # Calculate uncertainty
        uncertainty_range = emission_factor.get_uncertainty_range()
        lower_bound = total_co2e * (uncertainty_range[0] / emission_factor.value)
        upper_bound = total_co2e * (uncertainty_range[1] / emission_factor.value)
        
        calculation_details = {
            "emissions_by_gas": emissions_by_gas,
            "total_co2e": total_co2e,
            "uncertainty_range": (lower_bound, upper_bound),
            "confidence_level": emission_factor.confidence_level,
            "gwp_version": self.gwp_version.value,
            "calculation_method": self._determine_calculation_method(emission_factor)
        }
        
        return total_co2e, calculation_details
    
    def _determine_calculation_method(self, factor: EmissionFactorData) -> str:
        """Determine calculation methodology per ESRS E1-6 §54"""
        if factor.quality_tier == DataQualityTier.tier_3:
            return "Direct measurement"
        elif factor.quality_tier == DataQualityTier.tier_2:
            return "Mass balance / Fuel analysis"
        else:
            return "Default emission factors"


# --------------------------------------------------------------------------- #
# EMISSION FACTOR REPOSITORY                                                  #
# --------------------------------------------------------------------------- #

class EmissionFactorRepository:
    def __init__(self):
        self.factors: dict[str, EmissionFactorData] = {
            "EF-001": EmissionFactorData(
            factor_id="EF-001",
                value=Decimal("2.5"),
                unit="tCO2e/t",
                quality_tier=DataQualityTier.tie_1,
                source="TEST",
                source_year=2024,
            )
        }
        
    
    def _load_default_factors(self):
        """Add static emission factors for testing"""
        self.factors["EF_CEMENT_DE_2024"] = EmissionFactorData(
                factor_id="EF_CEMENT_DE_2024",
                value=Decimal("0.766"),
                unit="tCO2e/tonne",
                source="CBAM Germany",
                source_year=2024,
                quality_tier=DataQualityTier.tier_2,
                uncertainty_percent=Decimal("7.5"),
                confidence_level=Decimal("95"),
                distribution="lognormal",
                country_code="DE",
                technology="dry kiln"
        )


    def get_factor(
        self,
        factor_id: Optional[str],
        product_code: Optional[str],
        country: Optional[str],
        use_fallback: bool = False
    ) -> EmissionFactorData:
        """
        Retrieve the appropriate emission factor with support for:
        1. Direct lookup by specific factor_id (Tier 3)
        2. Country-specific fallback (Tier 2, CBAM-aligned)
        3. Global default fallback (Tier 1, CBAM-aligned)
        """
        if factor_id:
            factor = self.factors.get(factor_id)
            if factor:
                return factor
            else:
                raise ValueError(f"Factor ID '{factor_id}' not found in repository.")

        if use_fallback:
            if not product_code:
                raise ValueError("Fallback requested, but no product_code provided.")
            return self._get_cbam_fallback(product_code, country)

        raise ValueError(
            f"No emission factor found. "
            f"Inputs — factor_id: {factor_id}, product_code: {product_code}, country: {country}, use_fallback: {use_fallback}"
        )

    def _get_cbam_fallback(self, product_code: str, country: Optional[str]) -> EmissionFactorData:
        """Mocked fallback logic for CBAM alignment (replace with real logic)"""
        fallback_key = f"CBAM_{product_code}_{country or 'GLOBAL'}"
        factor = self.factors.get(fallback_key)
        if factor:
            return factor

        # Final global fallback
        global_fallback_key = f"CBAM_{product_code}_GLOBAL"
        factor = self.factors.get(global_fallback_key)
        if factor:
            return factor

        raise ValueError(f"No CBAM fallback factor found for product_code: {product_code}")
    
        
def _load_default_factors(self):
    """Load IPCC/CBAM default factors"""
    self.factors["EF_GRID_EU_2024"] = EmissionFactorData(
        factor_id="EF_GRID_EU_2024",
        value=Decimal("0.269"),
        unit="tCO2e/MWh",
        source="EEA",
        source_year=2024,
        quality_tier=DataQualityTier.tier_2,
        uncertainty_percent=Decimal("5"),
        country_code="EU"
    )

    self.factors["EF_CEMENT_DE_2024"] = EmissionFactorData(
        factor_id="EF_CEMENT_DE_2024",
        value=Decimal("0.726"),
        unit="tCO2e/tonne",
        source="CBAM Germany",
        source_year=2024,
        quality_tier=DataQualityTier.tier_2,
        uncertainty_percent=Decimal("7.5"),
        country_code="DE"
    )

    
def get_factor(
    self,
    factor_id: Optional[str],
    product_code: Optional[str],
    country: Optional[str],
    use_fallback: bool = False
) -> EmissionFactorData:
    """
    Retrieve the appropriate emission factor with support for:
    1. Direct lookup by specific factor_id (Tier 3)
    2. Country-specific fallback (Tier 2, CBAM-aligned)
    3. Global default fallback (Tier 1, CBAM-aligned)
    """

    # Step 1: Direct factor ID match (most specific)
    if factor_id:
        factor = self.factors.get(factor_id)
        if factor:
            return factor
        else:
            raise ValueError(f"Factor ID '{factor_id}' not found in repository.")

    # Step 2: Use fallback logic if allowed and product_code is available
    if use_fallback:
        if not product_code:
            raise ValueError("Fallback requested, but no product_code provided.")
        return self._get_cbam_fallback(product_code, country)

    # Step 3: No valid path to retrieve a factor
    raise ValueError(
        f"No emission factor found. "
        f"Inputs — factor_id: {factor_id}, product_code: {product_code}, country: {country}, use_fallback: {use_fallback}"
    )

    def _get_cbam_fallback(self, product_code: str, country: Optional[str]) -> EmissionFactorData:
        """Apply CBAM fallback hierarchy"""
        cbam_code = CBAMProductCode(product_code) if isinstance(product_code, str) else product_code
        
        if cbam_code not in CBAM_FALLBACK_FACTORS:
            raise ValueError(f"No CBAM fallback for product: {cbam_code}")
        
        fallbacks = CBAM_FALLBACK_FACTORS[cbam_code]
        
        # Try country-specific Tier 2
        if country:
            country_key = f"tier_2_{country.lower()}"
            if country_key in fallbacks:
                return EmissionFactorData(
                    factor_id=f"CBAM_{cbam_code.value}_{country}_FALLBACK",
                    value=fallbacks[country_key],
                    unit="tCO2e/t" if cbam_code != CBAMProductCode.ELECTRICITY else "tCO2e/MWh",
                    source="CBAM_ANNEX_VI",
                    source_year=2024,
                    quality_tier=DataQualityTier.tier_2,
                    uncertainty_percent=Decimal("10"),
                    country_code=country
                )
        
        # Default to Tier 1 global average
        return EmissionFactorData(
            factor_id=f"CBAM_{cbam_code.value}_GLOBAL_FALLBACK",
            value=fallbacks["tier_1"],
            unit="tCO2e/t" if cbam_code != CBAMProductCode.ELECTRICITY else "tCO2e/MWh",
            source="CBAM_ANNEX_VI",
            source_year=2024,
            quality_tier=DataQualityTier.tier_1,
            uncertainty_percent=Decimal("15")
        )


# --------------------------------------------------------------------------- #
# DATA QUALITY SCORING                                                        #
# --------------------------------------------------------------------------- #

class DataQualityScorer:
    """CSRD Article 29a compliant quality scoring"""
    
    @staticmethod
    def calculate_score(
        emission_factor: EmissionFactorData,
        temporal_correlation: int,  # Years between data and reporting
        geographical_match: bool,
        technology_match: bool,
        verification_level: Optional[str] = None
    ) -> Tuple[int, DataQualityTier]:
        """
        Calculate data quality score (1-5) and determine tier.
        
        1 = Highest quality (verified, recent, specific)
        5 = Lowest quality (unverified, old, generic)
        """
        score = 1  # Start with best
        
        # Temporal representativeness
        if temporal_correlation > 5:
            score += 2
        elif temporal_correlation > 2:
            score += 1
        
        # Geographical representativeness
        if not geographical_match:
            score += 1
        
        # Technological representativeness
        if not technology_match:
            score += 1
        
        # Verification bonus
        if verification_level == "reasonable_assurance":
            score = max(1, score - 1)
        
        # Map to tier
        if emission_factor.quality_tier == DataQualityTier.tier_3:
            tier = DataQualityTier.tier_3
        elif score <= 2:
            tier = DataQualityTier.tier_2
        else:
            tier = DataQualityTier.tier_1
        
        return min(5, score), tier


# --------------------------------------------------------------------------- #
# VOUCHER GENERATION LOGIC                                                    #
# --------------------------------------------------------------------------- #

def generate_voucher(
    input_data: VoucherInput,
    factor_repository: Optional[EmissionFactorRepository] = None,
    calculator: Optional[EmissionCalculator] = None
) -> Dict[str, Any]:
    """
    Generate CSRD/CBAM compliant emission voucher.
    
    This is the main entry point for voucher creation with full
    regulatory compliance.
    """
    logger.info(f"Generating voucher for supplier: {input_data.supplier_id}")
    
    # Initialize components
    if factor_repository is None:
        factor_repository = EmissionFactorRepository()
    
    if calculator is None:
        calculator = EmissionCalculator(GWPVersion.AR6)
    
    # Generate voucher ID (UUID v7 for time-ordering at scale)
    voucher_id = str(uuid.uuid4())  # In production, use UUID v7
    
    # Get emission factor with fallback logic
    emission_factor = factor_repository.get_factor(
        factor_id=input_data.emission_factor_id,
        product_code=input_data.product_cn_code,
        country=input_data.installation_country,
        use_fallback=input_data.use_fallback_factor
    )
    
    # Calculate emissions
    total_co2e, calculation_details = calculator.calculate_emissions(
        activity_data=input_data.quantity,
        emission_factor=emission_factor
    )
    
    # Calculate data quality score
    temporal_gap = datetime.now().year - emission_factor.source_year
    quality_score, quality_tier = DataQualityScorer.calculate_score(
        emission_factor=emission_factor,
        temporal_correlation=temporal_gap,
        geographical_match=(emission_factor.country_code == input_data.installation_country),
        technology_match=bool(emission_factor.technology),
        verification_level=input_data.verifier_accreditation_id
    )
    
    # Build voucher data structure
    voucher_data = {
        # Identifiers
        "voucher_id": voucher_id,
        "schema_version": SCHEMA_VERSION,
        "submission_timestamp": datetime.now(timezone.utc).isoformat(),
        "tier": input_data.tier.value,
        
        # Entity data
        "reporting_undertaking_id": input_data.reporting_undertaking_id,
        "supplier_id": input_data.supplier_id,
        "supplier_name": input_data.supplier_name,
        "legal_entity_identifier": input_data.legal_entity_identifier,
        
        # Emission scope
        "emission_scope": input_data.emission_scope.value,
        "scope3_category": input_data.scope3_category.value if input_data.scope3_category else None,
        
        # Product data
        "product_cn_code": input_data.product_cn_code,
        "product_category": input_data.product_category,
        "activity_description": input_data.activity_description,
        "material_type": input_data.material_type,
        
        # Quantities
        "quantity": float(input_data.quantity),
        "quantity_unit": input_data.quantity_unit,
        "monetary_value": float(input_data.monetary_value) if input_data.monetary_value else None,
        "currency": input_data.currency,
        
        # Location
        "installation_country": input_data.installation_country,
        "installation_id": input_data.installation_id,
        
        # Emission factor
        "emission_factor_id": emission_factor.factor_id,
        "emission_factor_value": float(emission_factor.value),
        "emission_factor_source": emission_factor.source,
        "emission_factor_unit": emission_factor.unit,
        
        # Calculation results
        "total_emissions_tco2e": float(total_co2e),
        "gwp_version": calculator.gwp_version.value,
        "calculation_methodology": calculation_details["calculation_method"],
        "emissions_breakdown": calculation_details["emissions_by_gas"],
        
        # Data quality
        "data_quality_rating": quality_score,
        "data_quality_tier": quality_tier.value,
        "uncertainty_lower": float(calculation_details["uncertainty_range"][0]),
        "uncertainty_upper": float(calculation_details["uncertainty_range"][1]),
        "confidence_level": float(emission_factor.confidence_level),
        
        # CBAM specific
        "fallback_factor_used": input_data.use_fallback_factor,
        "embedded_emissions_direct": float(input_data.embedded_emissions_direct) if input_data.embedded_emissions_direct else None,
        "embedded_emissions_indirect": float(input_data.embedded_emissions_indirect) if input_data.embedded_emissions_indirect else None,
        "carbon_price_paid": float(input_data.carbon_price_paid) if input_data.carbon_price_paid else None,
        
        # Time period
        "reporting_period_start": input_data.reporting_period_start.isoformat(),
        "reporting_period_end": input_data.reporting_period_end.isoformat(),
        
        # Verification
        "verifier_accreditation_id": input_data.verifier_accreditation_id,
        
        # Calculate integrity hash
        "calculation_hash": calculate_integrity_hash({
            "supplier_id": input_data.supplier_id,
            "product_cn_code": input_data.product_cn_code,
            "quantity": str(input_data.quantity),
            "emission_factor_value": str(emission_factor.value),
            "reporting_period_start": input_data.reporting_period_start.isoformat(),
            "reporting_period_end": input_data.reporting_period_end.isoformat()
        })
    }
    
    logger.info(f"Generated voucher {voucher_id}: {total_co2e} tCO2e")
    logger.info(f"Data quality: Tier {quality_tier.value}, Score {quality_score}/5")
    
    return voucher_data


def calculate_integrity_hash(data: Dict[str, Any]) -> str:
    """
    Calculate SHA-256 hash of core calculation inputs.
    Enhanced for regulatory compliance.
    """
    # Include version in hash for auditability
    hash_data = {"schema_version": SCHEMA_VERSION}
    hash_data.update(data)
    
    # Sort fields for deterministic hashing
    hash_input = "|".join(f"{k}:{v}" for k, v in sorted(hash_data.items()))
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


# --------------------------------------------------------------------------- #
# ENHANCED XML SERIALIZATION                                                  #
# --------------------------------------------------------------------------- #

def serialize_voucher(
    voucher: Union[Dict[str, Any], Any],
    validate_mandatory: bool = True,
    include_cbam_namespace: bool = True
) -> str:
    """
    Serialize emission voucher to ESRS/CBAM-compliant XML.
    Enhanced with AR6 GWP and full regulatory compliance.
    """
    logger.info(f"Serializing voucher ID: {voucher.get('voucher_id', 'UNKNOWN')}")
    
    # Normalize input
    if is_dataclass(voucher):
        data = asdict(voucher)
    elif isinstance(voucher, dict):
        data = dict(voucher)
    else:
        raise TypeError(f"Voucher must be dict or dataclass, got {type(voucher)}")
    
    # Build XML structure
    root = Element(
        QName(NAMESPACE, "EmissionVoucher"),
        nsmap=NSMAP if include_cbam_namespace else {None: NAMESPACE}
    )
    
    # Set schema location and version
    root.set(QName(XSI_NAMESPACE, "schemaLocation"), f"{NAMESPACE} emission-voucher-v2.xsd")
    root.set("schemaVersion", data.get("schema_version", SCHEMA_VERSION))
    
    # Header section
    header = SubElement(root, QName(NAMESPACE, "Header"))
    SubElement(header, QName(NAMESPACE, "MessageId")).text = data["voucher_id"]
    SubElement(header, QName(NAMESPACE, "CreationDateTime")).text = data["submission_timestamp"]
    SubElement(header, QName(NAMESPACE, "SchemaVersion")).text = SCHEMA_VERSION
    
    # Reporting entity
    entity = SubElement(root, QName(NAMESPACE, "ReportingEntity"))
    SubElement(entity, QName(NAMESPACE, "LEI")).text = data["reporting_undertaking_id"]
    
    # Supplier section
    supplier = SubElement(root, QName(NAMESPACE, "Supplier"))
    SubElement(supplier, QName(NAMESPACE, "Id")).text = data["supplier_id"]
    SubElement(supplier, QName(NAMESPACE, "Name")).text = data["supplier_name"]
    if data.get("legal_entity_identifier"):
        SubElement(supplier, QName(NAMESPACE, "LEI")).text = data["legal_entity_identifier"]
    
    # Emission scope section (NEW)
    scope_elem = SubElement(root, QName(NAMESPACE, "EmissionScope"))
    SubElement(scope_elem, QName(NAMESPACE, "Scope")).text = data["emission_scope"]
    if data.get("scope3_category"):
        SubElement(scope_elem, QName(NAMESPACE, "Scope3Category")).text = data["scope3_category"]
    
    # Product section
    product = SubElement(root, QName(NAMESPACE, "Product"))
    SubElement(product, QName(NAMESPACE, "CNCcode")).text = data["product_cn_code"]
    SubElement(product, QName(NAMESPACE, "Category")).text = data["product_category"]
    SubElement(product, QName(NAMESPACE, "Description")).text = data["activity_description"]
    if data.get("material_type"):
        SubElement(product, QName(NAMESPACE, "MaterialType")).text = data["material_type"]
    
    # Quantity
    quantity = SubElement(product, QName(NAMESPACE, "Quantity"))
    quantity.set("unit", data["quantity_unit"])
    quantity.text = str(data["quantity"])
    
    # Monetary value
    if data.get("monetary_value"):
        value = SubElement(product, QName(NAMESPACE, "MonetaryValue"))
        value.set("currency", data.get("currency", "EUR"))
        value.text = str(data["monetary_value"])
    
    # Installation (CBAM)
    if include_cbam_namespace:
        installation = SubElement(root, QName(CBAM_NAMESPACE, "Installation"))
        SubElement(installation, QName(CBAM_NAMESPACE, "Country")).text = data["installation_country"]
        if data.get("installation_id"):
            SubElement(installation, QName(CBAM_NAMESPACE, "Id")).text = data["installation_id"]
        
        # CBAM specific emissions
        if data.get("embedded_emissions_direct"):
            cbam_emissions = SubElement(installation, QName(CBAM_NAMESPACE, "EmbeddedEmissions"))
            SubElement(cbam_emissions, QName(CBAM_NAMESPACE, "Direct")).text = str(data["embedded_emissions_direct"])
            if data.get("embedded_emissions_indirect"):
                SubElement(cbam_emissions, QName(CBAM_NAMESPACE, "Indirect")).text = str(data["embedded_emissions_indirect"])
        
        if data.get("carbon_price_paid"):
            carbon_price = SubElement(installation, QName(CBAM_NAMESPACE, "CarbonPrice"))
            carbon_price.set("currency", "EUR")
            carbon_price.text = str(data["carbon_price_paid"])
    
    # Emission calculation section (ENHANCED)
    emissions = SubElement(root, QName(NAMESPACE, "EmissionCalculation"))
    
    # GWP version (NEW)
    SubElement(emissions, QName(NAMESPACE, "GWPVersion")).text = data.get("gwp_version", "AR6")
    
    # Emission factor
    factor = SubElement(emissions, QName(NAMESPACE, "EmissionFactor"))
    factor.set("id", data["emission_factor_id"])
    factor.set("source", data["emission_factor_source"])
    SubElement(factor, QName(NAMESPACE, "Value")).text = str(data["emission_factor_value"])
    SubElement(factor, QName(NAMESPACE, "Unit")).text = data.get("emission_factor_unit", "tCO2e/unit")
    
    if data.get("fallback_factor_used"):
        factor.set("fallbackUsed", "true")
    
    # Data quality (ENHANCED)
    quality = SubElement(emissions, QName(NAMESPACE, "DataQuality"))
    quality.set("rating", str(data["data_quality_rating"]))
    quality.set("tier", data.get("data_quality_tier", "tier_1"))
    
    # Uncertainty (NEW)
    if data.get("uncertainty_lower") and data.get("uncertainty_upper"):
        uncertainty = SubElement(quality, QName(NAMESPACE, "Uncertainty"))
        uncertainty.set("confidenceLevel", str(data.get("confidence_level", "95")))
        SubElement(uncertainty, QName(NAMESPACE, "LowerBound")).text = str(data["uncertainty_lower"])
        SubElement(uncertainty, QName(NAMESPACE, "UpperBound")).text = str(data["uncertainty_upper"])
    
    # Methodology
    SubElement(emissions, QName(NAMESPACE, "Methodology")).text = data["calculation_methodology"]
    
    # Total emissions
    total = SubElement(emissions, QName(NAMESPACE, "TotalEmissions"))
    total.set("unit", "tCO2e")
    total.text = str(data["total_emissions_tco2e"])
    
    # Emissions breakdown (NEW)
    if data.get("emissions_breakdown"):
        breakdown = SubElement(emissions, QName(NAMESPACE, "EmissionsBreakdown"))
        for gas, details in data["emissions_breakdown"].items():
            gas_elem = SubElement(breakdown, QName(NAMESPACE, "GasEmission"))
            gas_elem.set("gas", gas)
            gas_elem.set("gwpFactor", str(details["gwp_factor"]))
            SubElement(gas_elem, QName(NAMESPACE, "Amount")).text = str(details["amount"])
            SubElement(gas_elem, QName(NAMESPACE, "CO2e")).text = str(details["co2e"])
    
    # Reporting period
    period = SubElement(root, QName(NAMESPACE, "ReportingPeriod"))
    SubElement(period, QName(NAMESPACE, "StartDate")).text = data["reporting_period_start"]
    SubElement(period, QName(NAMESPACE, "EndDate")).text = data["reporting_period_end"]
    
    # Verification section
    verification = SubElement(root, QName(NAMESPACE, "Verification"))
    SubElement(verification, QName(NAMESPACE, "CalculationHash")).text = data["calculation_hash"]
    
    if data.get("verifier_accreditation_id"):
        verifier = SubElement(verification, QName(NAMESPACE, "Verifier"))
        SubElement(verifier, QName(NAMESPACE, "AccreditationId")).text = data["verifier_accreditation_id"]
    
    # Serialize
    xml_bytes = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=False
    )
    
    logger.info(f"Successfully serialized voucher {data['voucher_id']}")
    
    return xml_bytes.decode('utf-8')


# --------------------------------------------------------------------------- #
# VALIDATION FUNCTIONS (unchanged)                                            #
# --------------------------------------------------------------------------- #

def validate_lei(lei: str) -> bool:
    """Validate Legal Entity Identifier format"""
    if not isinstance(lei, str) or len(lei) != 20:
        return False
    return lei[:4].isalpha() and lei[4:18].isalnum()


def validate_iso_date(date_str: str) -> bool:
    """Validate YYYY-MM-DD format"""
    try:
        date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def validate_iso_timestamp(timestamp_str: str) -> bool:
    """Validate ISO 8601 timestamp"""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def validate_xml(
    xml: Union[str, bytes],
    xsd_path: Union[str, Path],
    return_errors: bool = False
) -> Union[bool, Tuple[bool, List[str]]]:
    """Validate XML against XSD schema"""
    logger.info(f"Validating XML against schema: {xsd_path}")
    
    if isinstance(xsd_path, Path):
        xsd_path = str(xsd_path)
    
    if isinstance(xml, str):
        xml = xml.encode('utf-8')
    
    try:
        schema_doc = etree.parse(xsd_path)
        schema = XMLSchema(schema_doc)
        xml_doc = etree.fromstring(xml)
        
        is_valid = schema.validate(xml_doc)
        
        if return_errors and not is_valid:
            errors = [str(error) for error in schema.error_log]
            logger.error(f"Validation failed with {len(errors)} errors")
            return is_valid, errors
        
        logger.info(f"Validation {'passed' if is_valid else 'failed'}")
        return is_valid
        
    except (XMLSyntaxError, Exception) as e:
        logger.error(f"Validation error: {str(e)}")
        if return_errors:
            return False, [str(e)]
        return False


# --------------------------------------------------------------------------- #
# CLI INTERFACE                                                               #
# --------------------------------------------------------------------------- #

    import json
    from decimal import Decimal

    def decimal_converter(o):
        if isinstance(o, Decimal):
            return float(o)

    print(json.dumps(voucher_data, indent=2, default=decimal_converter))
    
    # Example usage
    if len(sys.argv) > 1:
        # Load from file
        input_file = Path(sys.argv[1])
        input_data = json.loads(input_file.read_text())
    else:
        # Example input
        input_data = {
            "reporting_undertaking_id": "529900HNOAA1KXQJUQ27",  # Example LEI
            "supplier_id": "SUP-2024-001",
            "supplier_name": "Example Supplier GmbH",
            "legal_entity_identifier": "529900T8BM49AURSDO55",
            "emission_scope": "scope_3",
            "scope3_category": "1_purchased_goods_services",
            "product_cn_code": "2523",  # Cement
            "product_category": "Materials",
            "activity_description": "Portland cement CEM I 52.5",
            "material_type": "cement_portland",
            "quantity": 1000.0,
            "quantity_unit": "t",
            "monetary_value": 85000.0,
            "currency": "EUR",
            "installation_country": "DE",
            "installation_id": "DE-123456",
            "use_fallback_factor": False,
            "emission_factor_id": "EF_CEMENT_DE_2024",
            "reporting_period_start": "2024-01-01",
            "reporting_period_end": "2024-12-31",
            "embedded_emissions_direct": 766.0,
            "carbon_price_paid": 80.5
        }
    
    # Convert dates
    input_data["reporting_period_start"] = date.fromisoformat(input_data["reporting_period_start"])
    input_data["reporting_period_end"] = date.fromisoformat(input_data["reporting_period_end"])
    
    # Create input object
    voucher_input = VoucherInput(
        reporting_undertaking_id=input_data["reporting_undertaking_id"],
        supplier_id=input_data["supplier_id"],
        supplier_name=input_data["supplier_name"],
        tier=TierLevelEnum.tier_1,
        legal_entity_identifier=input_data.get("legal_entity_identifier"),
        emission_scope=EmissionScope(input_data["emission_scope"]),
        scope3_category=Scope3Category(input_data["scope3_category"]) if input_data.get("scope3_category") else None,
        product_cn_code=input_data["product_cn_code"],
        product_category=input_data["product_category"],
        activity_description=input_data["activity_description"],
        material_type=input_data.get("material_type"),
        quantity=Decimal(str(input_data["quantity"])),
        quantity_unit=input_data["quantity_unit"],
        monetary_value=Decimal(str(input_data["monetary_value"])) if input_data.get("monetary_value") else None,
        currency=input_data.get("currency", "EUR"),
        installation_country=input_data["installation_country"],
        installation_id=input_data.get("installation_id"),
        emission_factor_id=input_data.get("emission_factor_id"),
        use_fallback_factor=input_data.get("use_fallback_factor", False),
        reporting_period_start=input_data["reporting_period_start"],
        reporting_period_end=input_data["reporting_period_end"],
        embedded_emissions_direct=Decimal(str(input_data["embedded_emissions_direct"])) if input_data.get("embedded_emissions_direct") else None,
        carbon_price_paid=Decimal(str(input_data["carbon_price_paid"])) if input_data.get("carbon_price_paid") else None
    )
    
    # Generate voucher
    voucher_data = generate_voucher(voucher_input)
    
    # Serialize to XML
    xml_output = serialize_voucher(voucher_data)
    
    print("Generated Voucher Data:")
    print(json.dumps({k: str(v) if isinstance(v, Decimal) else v for k, v in voucher_data.items()}, indent=2))
    print("\n" + "="*80 + "\n")
    print("XML Output:")
    print(xml_output)
    SubElement(supplier, QName(NAMESPACE, "Name")).text = data["supplier_name"]
    SubElement(supplier, QName(NAMESPACE, "TierLevel")).text = data.get("tier", "tier_1")

    import uuid6  # pip install uuid6

def generate_voucher_id() -> str:
    """Generate time-ordered UUID v7 for better database indexing"""
    return str(uuid6.uuid7())

import asyncio
from concurrent.futures import ProcessPoolExecutor

async def generate_voucher_batch(
    inputs: List[VoucherInput],
    max_workers: int = 4
) -> List[Dict[str, Any]]:
    """Process vouchers in parallel for 100k+ daily volume"""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, generate_voucher, input_data)
            for input_data in inputs
        ]
        return await asyncio.gather(*tasks)
    
    from functools import lru_cache
import redis

class CachedEmissionFactorRepository(EmissionFactorRepository):
    def __init__(self, redis_client: redis.Redis):
        super().__init__()
        self.cache = redis_client
        
    @lru_cache(maxsize=1000)
    def get_factor(self, factor_id: str, **kwargs) -> EmissionFactorData:
        # Check Redis first
        cached = self.cache.get(f"ef:{factor_id}")
        if cached:
            return EmissionFactorData(**json.loads(cached))
        
        # Fallback to parent method
        factor = super().get_factor(factor_id, **kwargs)
        
        # Cache for 24 hours
        self.cache.setex(
            f"ef:{factor_id}",
            86400,
            json.dumps(asdict(factor), default=str)
        )
        return factor
    
def assess_materiality(
    total_emissions: Decimal,
    monetary_value: Optional[Decimal],
    company_total_emissions: Decimal
) -> Dict[str, Any]:

    def calculate_materiality_emissions(company_total_emissions: Decimal, total_emissions: Decimal) -> Decimal:
        """ESRS double materiality assessment"""
        emission_percentage = (total_emissions / company_total_emissions) * 100
        return emission_percentage
    
    # Financial materiality
    financial_material = False
    if monetary_value:
        # Example: material if >€100k and >5% emissions
        financial_material = (
            monetary_value > 100000 and 
            emission_percentage > Decimal("5.0")
        )
    
    return {
        "impact_material": impact_material,
        "financial_material": financial_material,
        "emission_percentage": float(emission_percentage),
        "materiality_type": "double" if impact_material and financial_material else
                          "impact" if impact_material else
                          "financial" if financial_material else "none"
    }

sql_schema = """
CREATE TABLE emission_vouchers (
    voucher_id UUID PRIMARY KEY,
    schema_version VARCHAR(10) NOT NULL,

    -- Denormalized for query performance
    reporting_lei VARCHAR(20) NOT NULL,
    supplier_id VARCHAR(50) NOT NULL,
    emission_scope VARCHAR(20) NOT NULL,
    scope3_category VARCHAR(50),

    -- Numeric fields
    total_co2e DECIMAL(15,3) NOT NULL,
    data_quality_tier VARCHAR(10) NOT NULL,
    data_quality_score SMALLINT NOT NULL,

    -- CBAM fields
    cbam_product_code VARCHAR(10),
    fallback_used BOOLEAN DEFAULT FALSE,
    carbon_price_paid DECIMAL(10,2),

    -- Temporal
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- JSONB for flexibility
    calculation_details JSONB NOT NULL,
    verification_data JSONB,

    -- Audit
    calculation_hash VARCHAR(64) NOT NULL
);
"""

sql_indexes_and_partitions = """
-- Indexes for regulatory queries
CREATE INDEX idx_vouchers_period ON emission_vouchers(reporting_period_start, reporting_period_end);
CREATE INDEX idx_vouchers_scope ON emission_vouchers(emission_scope, scope3_category);
CREATE INDEX idx_vouchers_quality ON emission_vouchers(data_quality_tier, data_quality_score);
CREATE INDEX idx_vouchers_cbam ON emission_vouchers(cbam_product_code) WHERE cbam_product_code IS NOT NULL;

-- Partitioning by month for scale
CREATE TABLE emission_vouchers_2024_01 PARTITION OF emission_vouchers
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
"""

if __name__ == "__main__":
    from decimal import Decimal
    from datetime import date
    import json

    voucher_input = VoucherInput(
        reporting_undertaking_id="LEI-XYZ-123456",
        supplier_id="SUP-2024-001",
        supplier_name="CementCo GmbH",
        tier=TierLevelEnum.tier_1,
        emission_scope=EmissionScope.SCOPE_3,
        product_cn_code="2523",  # Cement CN code
        product_category="Materials",
        activity_description="Imported cement for EU infrastructure",
        quantity=Decimal("100"),
        quantity_unit="tonnes",
        installation_country="DE",
        reporting_period_start=date(2024, 1, 1),
        reporting_period_end=date(2024, 12, 31),
        emission_factor_id="EF_CEMENT_DE_2024",
        use_fallback_factor=True
    )

    # Print as JSON (convert Decimal to string for serialization)
    print(json.dumps(voucher_input.__dict__, default=str, indent=2))
    voucher_data = generate_voucher(voucher_input)
    print(json.dumps(voucher_data, indent=2, default=str))  # Serialize Decimals as strings

from factortrace.services.audit import create_audit_entry
from factortrace.enums import AuditActionEnum
from factortrace.models.emissions_voucher import EmissionVoucher, AuditTrail

async def create_voucher(file):  # or however you're receiving input
    # Parse uploaded XML or JSON
    voucher_data = parse_voucher(file)

    # Add audit trail
    audit_entry = create_audit_entry(
        user_id="system",  # or get from JWT/session if auth in place
        action=AuditActionEnum.CREATED,
        ip_address="127.0.0.1"
    )
    voucher_data["audit_trail"] = {"audit_entries": [audit_entry.dict()]}

    voucher = EmissionVoucher(
        supplier_lei="5493001KTIIIGC8YR1212",  # ✅ must match LEI regex
        supplier_name="Acme Metals",
        supplier_country="DE",
        supplier_sector="Steel",
        reporting_entity_lei="12345678ABCD12345678",  # ✅ match pattern
        reporting_period_start="2024-01-01",
        reporting_period_end="2024-12-31",
        consolidation_method="operational_control",
        emissions_records=[{"source": "scope1", "amount": 100.0, "unit": "tCO2e"}],  # ✅ must not be empty
        total_emissions_tco2e=100.0
    )
    return voucher