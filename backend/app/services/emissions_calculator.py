# backend/app/services/emissions_calculator.py
"""
Emissions Calculator for Scope 1-3 GHG emissions with regulatory compliance.
Implements GHG Protocol, CBAM, and ESRS calculation methodologies with
uncertainty quantification and cryptographic audit trails.

Version: 2.0.0
Compliance: GHG Protocol Rev. 2024, CBAM Regulation (EU) 2023/1773, ESRS E1-6
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator
from scipy import stats
from sqlalchemy.orm import Session

# ==============================================================================
# CONSTANTS
# ==============================================================================

# GWP factors per IPCC AR6 (100-year time horizon)
GWP_FACTORS_AR6_100 = {
    "CO2": Decimal("1.0"),
    "CH4": Decimal("29.8"),  # Fossil CH4
    "N2O": Decimal("273.0"),
    "SF6": Decimal("25200.0"),
    "NF3": Decimal("17400.0"),
}

# GWP factors per IPCC AR5 (100-year time horizon)
GWP_FACTORS_AR5_100 = {
    "CO2": Decimal("1.0"),
    "CH4": Decimal("28.0"),
    "N2O": Decimal("265.0"),
    "SF6": Decimal("23500.0"),
    "NF3": Decimal("16100.0"),
}

# Default uncertainty ranges by tier level (%)
DEFAULT_UNCERTAINTY_BY_TIER = {
    "TIER_1": Decimal("30.0"),  # Default factors
    "TIER_2": Decimal("10.0"),  # Facility-specific
    "TIER_3": Decimal("5.0"),   # Direct measurement
}

# CBAM default emission factors (tCO2e/unit)
CBAM_DEFAULT_FACTORS = {
    "72": {  # Iron and steel
        "direct": Decimal("2.13"),
        "indirect": Decimal("0.47"),
        "unit": "tonne",
    },
    "76": {  # Aluminium
        "direct": Decimal("1.51"),
        "indirect": Decimal("11.17"),
        "unit": "tonne",
    },
    "25": {  # Cement
        "direct": Decimal("0.64"),
        "indirect": Decimal("0.08"),
        "unit": "tonne",
    },
    "31": {  # Fertilizers
        "direct": Decimal("1.89"),
        "indirect": Decimal("0.21"),
        "unit": "tonne",
    },
    "27": {  # Electricity
        "direct": Decimal("0.0"),
        "indirect": Decimal("0.465"),
        "unit": "MWh",
    },
}

# Scope 3 Categories per GHG Protocol
SCOPE3_CATEGORIES = {
    "purchased_goods_services": {
        "id": "cat1",
        "display_name": "Purchased Goods and Services",
        "ghg_protocol_id": "3.1",
        "esrs_requirements": ["E1-6.50", "E1-6.51"],
        "cdp_questions": ["C6.5", "C6.5a"],
        "material_sectors": ["Manufacturing", "Retail", "Technology", "Healthcare"],
    },
    "capital_goods": {
        "id": "cat2",
        "display_name": "Capital Goods",
        "ghg_protocol_id": "3.2",
        "esrs_requirements": ["E1-6.52"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Manufacturing", "Real Estate", "Technology", "Energy"],
    },
    "fuel_energy_activities": {
        "id": "cat3",
        "display_name": "Fuel- and Energy-Related Activities",
        "ghg_protocol_id": "3.3",
        "esrs_requirements": ["E1-6.53"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["All sectors"],
    },
    "upstream_transportation": {
        "id": "cat4",
        "display_name": "Upstream Transportation and Distribution",
        "ghg_protocol_id": "3.4",
        "esrs_requirements": ["E1-6.54"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Retail", "Manufacturing", "E-commerce"],
    },
    "waste_operations": {
        "id": "cat5",
        "display_name": "Waste Generated in Operations",
        "ghg_protocol_id": "3.5",
        "esrs_requirements": ["E1-6.55"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Manufacturing", "Retail", "Healthcare", "Hospitality"],
    },
    "business_travel": {
        "id": "cat6",
        "display_name": "Business Travel",
        "ghg_protocol_id": "3.6",
        "esrs_requirements": ["E1-6.56"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Professional Services", "Technology", "Finance"],
    },
    "employee_commuting": {
        "id": "cat7",
        "display_name": "Employee Commuting",
        "ghg_protocol_id": "3.7",
        "esrs_requirements": ["E1-6.57"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["All sectors with significant workforce"],
    },
    "upstream_leased_assets": {
        "id": "cat8",
        "display_name": "Upstream Leased Assets",
        "ghg_protocol_id": "3.8",
        "esrs_requirements": ["E1-6.58"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Real Estate", "Retail", "Logistics"],
    },
    "downstream_transportation": {
        "id": "cat9",
        "display_name": "Downstream Transportation and Distribution",
        "ghg_protocol_id": "3.9",
        "esrs_requirements": ["E1-6.59"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Retail", "E-commerce", "Manufacturing"],
    },
    "processing_sold_products": {
        "id": "cat10",
        "display_name": "Processing of Sold Products",
        "ghg_protocol_id": "3.10",
        "esrs_requirements": ["E1-6.60"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Chemicals", "Materials", "Components"],
    },
    "use_of_sold_products": {
        "id": "cat11",
        "display_name": "Use of Sold Products",
        "ghg_protocol_id": "3.11",
        "esrs_requirements": ["E1-6.61"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Automotive", "Electronics", "Appliances", "Energy"],
    },
    "end_of_life_treatment": {
        "id": "cat12",
        "display_name": "End-of-Life Treatment of Sold Products",
        "ghg_protocol_id": "3.12",
        "esrs_requirements": ["E1-6.62"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Consumer Goods", "Electronics", "Automotive"],
    },
    "downstream_leased_assets": {
        "id": "cat13",
        "display_name": "Downstream Leased Assets",
        "ghg_protocol_id": "3.13",
        "esrs_requirements": ["E1-6.63"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Real Estate", "Equipment Rental", "Fleet Management"],
    },
    "franchises": {
        "id": "cat14",
        "display_name": "Franchises",
        "ghg_protocol_id": "3.14",
        "esrs_requirements": ["E1-6.64"],
        "cdp_questions": ["C6.5"],
        "material_sectors": ["Retail", "Food Service", "Hospitality"],
    },
    "investments": {
        "id": "cat15",
        "display_name": "Investments",
        "ghg_protocol_id": "3.15",
        "esrs_requirements": ["E1-6.65", "E1-6.66"],
        "cdp_questions": ["C6.5", "C-FS14.1"],
        "material_sectors": ["Finance", "Insurance", "Asset Management"],
    },
}

# Materiality thresholds by sector
MATERIALITY_THRESHOLDS = {
    "Manufacturing": 0.05,
    "Retail": 0.10,
    "Technology": 0.03,
    "Finance": 0.15,
    "Energy": 0.08,
    "Healthcare": 0.06,
    "Transportation": 0.07,
    "Default": 0.05,
}

# Hardcoded emission factor lookup database
# Key: (scope, category, country) -> emission factor value (kgCO2e/unit)
FACTOR_DB: Dict[Tuple[int, str, str], float] = {
    # Scope 1 - Mobile Combustion
    (1, 'Mobile Combustion', 'DE'): 2.31,
    (1, 'Mobile Combustion', 'US'): 2.50,
    (1, 'Mobile Combustion', 'FR'): 2.28,
    (1, 'Mobile Combustion', 'UK'): 2.34,
    (1, 'Mobile Combustion', 'Global'): 2.40,
    # Scope 1 - Stationary Combustion
    (1, 'Stationary Combustion', 'DE'): 2.02,
    (1, 'Stationary Combustion', 'US'): 2.10,
    (1, 'Stationary Combustion', 'Global'): 2.05,
    # Scope 1 - Fugitive Emissions
    (1, 'Fugitive Emissions', 'Global'): 0.025,
    # Scope 2 - Purchased Electricity (kgCO2e/kWh)
    (2, 'Purchased Electricity', 'DE'): 0.35,
    (2, 'Purchased Electricity', 'FR'): 0.08,
    (2, 'Purchased Electricity', 'PL'): 0.70,
    (2, 'Purchased Electricity', 'US'): 0.42,
    (2, 'Purchased Electricity', 'UK'): 0.23,
    (2, 'Purchased Electricity', 'Global'): 0.45,
    # Scope 2 - Purchased Heat/Steam
    (2, 'Purchased Heat', 'DE'): 0.22,
    (2, 'Purchased Heat', 'Global'): 0.25,
    # Scope 3 - Business Travel (kgCO2e/km)
    (3, 'Business Travel', 'DE'): 0.15,
    (3, 'Business Travel', 'Global'): 0.255,
    # Scope 3 - Water Supply (kgCO2e/m3)
    (3, 'Water Supply', 'DE'): 0.30,
    (3, 'Water Supply', 'Global'): 0.34,
    # Scope 3 - Other Categories
    (3, 'Employee Commuting', 'Global'): 0.21,
    (3, 'Purchased Goods', 'Global'): 0.5,
    (3, 'Upstream Transportation', 'Global'): 0.1,
    (3, 'Waste', 'Global'): 0.7,
}

# Default emission factor when no match is found
DEFAULT_EMISSION_FACTOR = 1.0

logger = logging.getLogger(__name__)


# ==============================================================================
# ENUMERATIONS
# ==============================================================================


class CalculationMethodEnum(str, Enum):
    """Calculation methods per ESRS E1-6 S54"""
    DIRECT_MEASUREMENT = "direct_measurement"
    MASS_BALANCE = "mass_balance"
    EMISSION_FACTOR = "emission_factor"
    ENGINEERING_ESTIMATE = "engineering_estimate"
    DEFAULT_FACTOR = "default_factor"
    HYBRID = "hybrid"
    SPEND_BASED = "spend_based"
    ACTIVITY_BASED = "activity_based"


class AllocationMethodEnum(str, Enum):
    """Allocation methods for multi-output processes"""
    PHYSICAL = "physical"
    ECONOMIC = "economic"
    ENERGY = "energy"
    MASS = "mass"
    SYSTEM_EXPANSION = "system_expansion"


class GasTypeEnum(str, Enum):
    """Greenhouse gas types"""
    CO2 = "CO2"
    CH4 = "CH4"
    N2O = "N2O"
    SF6 = "SF6"
    NF3 = "NF3"


class GWPVersionEnum(str, Enum):
    """GWP version standards"""
    AR6_100 = "AR6_100"
    AR5_100 = "AR5_100"
    AR4_100 = "AR4_100"


class TierLevelEnum(str, Enum):
    """Calculation tier levels"""
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"


class UncertaintyDistributionEnum(str, Enum):
    """Uncertainty distribution types"""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"


class DataQualityDimension(str, Enum):
    """Data quality dimensions"""
    TEMPORAL = "temporal"
    GEOGRAPHICAL = "geographical"  
    TECHNOLOGICAL = "technological"
    COMPLETENESS = "completeness"
    RELIABILITY = "reliability"


# ==============================================================================
# DATA MODELS
# ==============================================================================


class DataQualityIndicators(BaseModel):
    """Data quality assessment per GHG Protocol"""
    temporal: int = Field(..., ge=0, le=100, description="Temporal correlation score")
    geographical: int = Field(..., ge=0, le=100, description="Geographical correlation score")
    technological: int = Field(..., ge=0, le=100, description="Technological correlation score")
    completeness: int = Field(..., ge=0, le=100, description="Data completeness score")
    reliability: int = Field(..., ge=0, le=100, description="Source reliability score")
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall score"""
        weights = {
            "temporal": 0.25,
            "geographical": 0.20,
            "technological": 0.20,
            "completeness": 0.20,
            "reliability": 0.15
        }
        
        weighted_sum = sum(
            getattr(self, dim) * weight 
            for dim, weight in weights.items()
        )
        
        return round(weighted_sum, 1)
    
    @property
    def uncertainty_factor(self) -> Decimal:
        """Convert quality score to uncertainty factor"""
        # Higher quality = lower uncertainty
        # Score 100 = 5% uncertainty, Score 0 = 50% uncertainty
        return Decimal(str(50 - (self.overall_score * 0.45)))


class EmissionFactor(BaseModel):
    """Enhanced emission factor model matching database schema"""
    factor_id: str
    value: Decimal = Field(..., description="Emission factor value")
    unit: str = Field(..., description="Unit of emission factor")
    source: str
    source_year: int
    tier: TierLevelEnum = TierLevelEnum.TIER_2
    
    # Enhanced fields matching database
    uncertainty_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    data_quality_score: Optional[int] = Field(None, ge=1, le=5)  # 1=best, 5=worst
    tier_level: Optional[str] = None
    scope3_category: Optional[str] = None
    calculation_method: Optional[CalculationMethodEnum] = None
    temporal_representativeness: Optional[str] = None
    geographical_representativeness: Optional[str] = None
    methodology: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    region: Optional[str] = None
    last_verified: Optional[datetime] = None
    
    # Computed data quality
    data_quality: Optional[DataQualityIndicators] = None
    
    @field_validator("value")
    def validate_positive_value(cls, v):
        if v <= 0:
            raise ValueError("Emission factor must be positive")
        return v
    
    def model_post_init(self, __context):
        """Initialize data quality from score if not provided"""
        if not self.data_quality and self.data_quality_score:
            self.data_quality = create_data_quality_from_factor(self)


class GHGBreakdown(BaseModel):
    """Breakdown by gas type"""
    gas_type: GasTypeEnum
    amount: Decimal
    unit: str = "tCO2e"
    gwp_factor: Decimal
    gwp_version: GWPVersionEnum


class AuditTrail(BaseModel):
    """Audit trail for calculation"""
    entries: List[Dict[str, Any]] = Field(default_factory=list)
    sealed: bool = False
    seal_hash: Optional[str] = None
    
    def add_entry(self, user_id: str, action: str, field_changed: str, new_value: str):
        """Add audit entry"""
        if self.sealed:
            raise ValueError("Cannot modify sealed audit trail")
            
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "field_changed": field_changed,
            "new_value": new_value
        }
        self.entries.append(entry)
    
    def seal(self):
        """Seal the audit trail"""
        if self.sealed:
            return
            
        # Generate hash of all entries
        entries_json = json.dumps(self.entries, sort_keys=True)
        self.seal_hash = hashlib.sha256(entries_json.encode()).hexdigest()
        self.sealed = True


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def create_data_quality_from_factor(factor: EmissionFactor) -> DataQualityIndicators:
    """Convert emission factor quality fields to DataQualityIndicators"""
    
    # Map 1-5 score to percentage
    quality_map = {
        1: 95,  # Excellent
        2: 85,  # Good
        3: 70,  # Fair
        4: 50,  # Poor
        5: 30   # Very Poor
    }
    
    base_score = quality_map.get(factor.data_quality_score or 3, 50)
    
    # Adjust scores based on available metadata
    temporal_score = base_score + 5 if factor.temporal_representativeness and "2024" in factor.temporal_representativeness else base_score
    geographical_score = base_score + 5 if factor.geographical_representativeness else base_score
    technological_score = base_score + 5 if factor.methodology else base_score
    completeness_score = 90 if factor.tier_level == "TIER_3" else (80 if factor.tier_level == "TIER_2" else 70)
    reliability_score = base_score + 5 if factor.last_verified else base_score
    
    return DataQualityIndicators(
        temporal=temporal_score,
        geographical=geographical_score,
        technological=technological_score,
        completeness=completeness_score,
        reliability=reliability_score
    )


# ==============================================================================
# CALCULATION MODELS
# ==============================================================================


class CalculationContext(BaseModel):
    """Context for emissions calculation"""
    calculation_id: str = Field(default_factory=lambda: hashlib.sha256(
        datetime.now(timezone.utc).isoformat().encode()
    ).hexdigest()[:16])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Calculation parameters
    gwp_version: GWPVersionEnum = Field(GWPVersionEnum.AR6_100)
    include_biogenic: bool = Field(False)
    include_indirect: bool = Field(True)
    uncertainty_method: str = Field("monte_carlo", pattern="^(monte_carlo|analytical|hybrid)$")
    confidence_level: Decimal = Field(Decimal("95"), ge=50, le=99.9)
    
    # CBAM specific
    apply_cbam_defaults: bool = Field(False)
    cbam_cn_code: Optional[str] = Field(None, pattern="^\\d{2,10}$")
    
    # Audit
    user_id: str = Field(..., description="User performing calculation")
    organization_id: str = Field(..., description="Organization context")
    notes: Optional[str] = Field(None, max_length=1000)


class CalculationInput(BaseModel):
    """Input data for emissions calculation"""
    activity_data: Decimal = Field(..., gt=0, description="Activity amount")
    activity_unit: str = Field(..., description="Unit of activity")
    emission_factor: EmissionFactor
    
    # Optional overrides
    custom_gwp: Optional[Dict[GasTypeEnum, Decimal]] = None
    allocation_factor: Decimal = Field(Decimal("1.0"), ge=0, le=1)
    temporal_correlation: Decimal = Field(Decimal("1.0"), ge=0, le=1)
    
    # Data quality
    data_quality_override: Optional[DataQualityIndicators] = None
    uncertainty_override: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Scope 3 specific
    scope3_category: Optional[str] = None
    region: Optional[str] = None


class CalculationResult(BaseModel):
    """Result of emissions calculation"""
    calculation_id: str
    timestamp: datetime
    
    # Core results
    emissions_tco2e: Decimal = Field(..., description="Central estimate")
    ghg_breakdown: List[GHGBreakdown]
    
    # Uncertainty
    uncertainty_percent: Decimal = Field(..., ge=0, le=100)
    confidence_interval_lower: Decimal
    confidence_interval_upper: Decimal
    distribution_type: UncertaintyDistributionEnum
    
    # Metadata
    calculation_method: CalculationMethodEnum
    data_quality: DataQualityIndicators
    tier_level: TierLevelEnum
    
    # Scope 3 specific
    scope3_category: Optional[str] = None
    scope3_category_name: Optional[str] = None
    
    # Traceability
    calculation_hash: str = Field(..., description="SHA-256 of inputs")
    input_data_hash: str
    audit_trail: AuditTrail = Field(default_factory=AuditTrail)
    
    # Compliance
    esrs_mapping: Optional[List[str]] = None
    cdp_mapping: Optional[List[str]] = None
    
    # Warnings
    warnings: List[str] = Field(default_factory=list)
    applied_defaults: bool = Field(False)


class MaterialityAssessment(BaseModel):
    """Scope 3 category materiality assessment"""
    category: str
    category_name: str
    is_material: bool
    threshold_percentage: Decimal
    actual_percentage: Optional[Decimal] = None
    reasons: List[str]
    recommendations: List[str]
    data_availability: str  # high, medium, low
    sector: str


class ComplianceReport(BaseModel):
    """Multi-standard compliance report"""
    reporting_period: str
    standard: str  # ESRS, CDP, TCFD, SBTi
    total_emissions: Decimal
    scope_breakdown: Dict[str, Decimal]
    
    # Category details
    category_emissions: Dict[str, Dict[str, Any]]
    
    # Compliance status
    compliance_status: str
    completeness_percentage: Decimal
    data_quality_score: Decimal
    
    # Requirements
    requirements_met: List[str]
    requirements_pending: List[str]
    
    # Recommendations
    priority_actions: List[str]
    improvement_areas: List[str]


# ==============================================================================
# CALCULATOR CLASSES
# ==============================================================================


class UncertaintyCalculator:
    """Calculate emissions uncertainty using various methods"""
    
    def __init__(self, method: str = "monte_carlo", iterations: int = 10000):
        self.method = method
        self.iterations = iterations
        self.rng = np.random.default_rng()
    
    def calculate_uncertainty(
        self,
        central_value: Decimal,
        uncertainty_percent: Decimal,
        distribution: UncertaintyDistributionEnum,
        confidence_level: Decimal = Decimal("95"),
        data_quality: Optional[DataQualityIndicators] = None
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate uncertainty bounds for emissions.
        
        Returns:
            Tuple of (lower_bound, central_value, upper_bound)
        """
        # Adjust uncertainty based on data quality
        if data_quality:
            quality_adjustment = data_quality.uncertainty_factor / Decimal("100")
            adjusted_uncertainty = uncertainty_percent * (Decimal("1") + quality_adjustment)
        else:
            adjusted_uncertainty = uncertainty_percent
        
        if self.method == "analytical":
            return self._analytical_uncertainty(
                central_value, adjusted_uncertainty, distribution, confidence_level
            )
        elif self.method == "monte_carlo":
            return self._monte_carlo_uncertainty(
                central_value, adjusted_uncertainty, distribution, confidence_level
            )
        else:
            raise ValueError(f"Unknown uncertainty method: {self.method}")
    
    def _analytical_uncertainty(
        self,
        central: Decimal,
        uncertainty: Decimal,
        distribution: UncertaintyDistributionEnum,
        confidence: Decimal,
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate analytical uncertainty bounds"""
        z_score = float(stats.norm.ppf((float(confidence) + 100) / 200))
        
        if distribution == UncertaintyDistributionEnum.NORMAL:
            std_dev = float(central) * float(uncertainty) / 100
            lower = Decimal(str(float(central) - z_score * std_dev))
            upper = Decimal(str(float(central) + z_score * std_dev))
        
        elif distribution == UncertaintyDistributionEnum.LOGNORMAL:
            # For lognormal, work in log space
            log_mean = np.log(float(central))
            log_std = np.log(1 + float(uncertainty) / 100)
            lower = Decimal(str(np.exp(log_mean - z_score * log_std)))
            upper = Decimal(str(np.exp(log_mean + z_score * log_std)))
        
        elif distribution == UncertaintyDistributionEnum.UNIFORM:
            # For uniform, use the range directly
            half_range = float(central) * float(uncertainty) / 100
            lower = central - Decimal(str(half_range))
            upper = central + Decimal(str(half_range))
        
        else:
            # Default to normal for other distributions
            return self._analytical_uncertainty(
                central, uncertainty, UncertaintyDistributionEnum.NORMAL, confidence
            )
        
        return (max(lower, Decimal("0")), central, upper)
    
    def _monte_carlo_uncertainty(
        self,
        central: Decimal,
        uncertainty: Decimal,
        distribution: UncertaintyDistributionEnum,
        confidence: Decimal,
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Run Monte Carlo simulation for uncertainty"""
        samples = self._generate_samples(
            float(central), float(uncertainty), distribution
        )
        
        # Calculate percentiles
        lower_percentile = (100 - float(confidence)) / 2
        upper_percentile = 100 - lower_percentile
        
        lower = Decimal(str(np.percentile(samples, lower_percentile)))
        upper = Decimal(str(np.percentile(samples, upper_percentile)))
        mean = Decimal(str(np.mean(samples)))
        
        return (max(lower, Decimal("0")), mean, upper)
    
    def _generate_samples(
        self, central: float, uncertainty: float, distribution: UncertaintyDistributionEnum
    ) -> np.ndarray:
        """Generate random samples based on distribution type"""
        if distribution == UncertaintyDistributionEnum.NORMAL:
            std_dev = central * uncertainty / 100
            samples = self.rng.normal(central, std_dev, self.iterations)
        
        elif distribution == UncertaintyDistributionEnum.LOGNORMAL:
            # Convert to lognormal parameters
            var = (central * uncertainty / 100) ** 2
            mu = np.log(central / np.sqrt(1 + var / central**2))
            sigma = np.sqrt(np.log(1 + var / central**2))
            samples = self.rng.lognormal(mu, sigma, self.iterations)
        
        elif distribution == UncertaintyDistributionEnum.TRIANGULAR:
            # Triangular with mode at central value
            min_val = central * (1 - uncertainty / 100)
            max_val = central * (1 + uncertainty / 100)
            samples = self.rng.triangular(min_val, central, max_val, self.iterations)
        
        elif distribution == UncertaintyDistributionEnum.UNIFORM:
            min_val = central * (1 - uncertainty / 100)
            max_val = central * (1 + uncertainty / 100)
            samples = self.rng.uniform(min_val, max_val, self.iterations)
        
        else:
            # Default to normal
            return self._generate_samples(
                central, uncertainty, UncertaintyDistributionEnum.NORMAL
            )
        
        return np.maximum(samples, 0)  # Ensure non-negative
    
    def combine_uncertainties(
        self, uncertainties: List[Dict[str, Any]], correlation: float = 0.0
    ) -> Decimal:
        """Combine multiple uncertainties"""
        if not uncertainties:
            return Decimal("0")
        
        if correlation > 0:
            # Correlated uncertainties
            total_uncertainty = sum(
                u["weight"] * float(u["uncertainty"]) / 100
                for u in uncertainties
            )
            return Decimal(str(total_uncertainty * 100))
        else:
            # Independent uncertainties - root sum of squares
            weighted_variance = sum(
                (u["weight"] * float(u["uncertainty"]) / 100) ** 2
                for u in uncertainties
            )
            
            combined_uncertainty = Decimal(str(np.sqrt(weighted_variance) * 100))
            return combined_uncertainty.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CBAMCalculator:
    """Calculator for CBAM-specific emissions"""
    
    @staticmethod
    def get_default_factors(cn_code: str) -> Optional[Dict[str, Any]]:
        """Get CBAM default emission factors for CN code"""
        prefix = cn_code[:2]
        return CBAM_DEFAULT_FACTORS.get(prefix)
    
    @staticmethod
    def calculate_embedded_emissions(
        quantity: Decimal,
        cn_code: str,
        custom_factors: Optional[Dict[str, Decimal]] = None,
    ) -> Tuple[Decimal, Decimal, str]:
        """
        Calculate CBAM embedded emissions.
        
        Returns:
            Tuple of (direct_emissions, indirect_emissions, unit)
        """
        if custom_factors:
            direct = quantity * custom_factors.get("direct", Decimal("0"))
            indirect = quantity * custom_factors.get("indirect", Decimal("0"))
            unit = custom_factors.get("unit", "unit")
        else:
            defaults = CBAMCalculator.get_default_factors(cn_code)
            if not defaults:
                raise ValueError(f"No CBAM default factors for CN code: {cn_code}")
            
            direct = quantity * defaults["direct"]
            indirect = quantity * defaults["indirect"]
            unit = defaults["unit"]
        
        return (direct, indirect, unit)


class EliteEmissionsCalculator:
    """
    Main emissions calculator implementing GHG Protocol, CBAM, and ESRS methodologies.
    Enhanced with comprehensive Scope 3 support and database integration.
    """
    
    def __init__(
        self,
        context: CalculationContext,
        uncertainty_calculator: Optional[UncertaintyCalculator] = None,
        db_session: Optional[Session] = None
    ):
        self.context = context
        self.uncertainty_calc = uncertainty_calculator or UncertaintyCalculator()
        self.cbam_calc = CBAMCalculator()
        self.audit_trail = AuditTrail()
        self.db_session = db_session
        
        # Initialize GWP factors based on version
        self.gwp_factors = self._get_gwp_factors(context.gwp_version)
    
    def calculate_emissions(
        self,
        inputs: List[CalculationInput],
        allocation_method: Optional[AllocationMethodEnum] = None,
    ) -> CalculationResult:
        """
        Calculate total emissions from multiple inputs with uncertainty.
        
        Args:
            inputs: List of calculation inputs
            allocation_method: Method for allocating emissions
        
        Returns:
            CalculationResult with emissions and uncertainty bounds
        """
        # Start calculation
        calc_start = datetime.now(timezone.utc)
        self._add_audit_entry("calculation_started", {
            "inputs_count": len(inputs),
            "gwp_version": self.context.gwp_version.value,
        })
        
        # Calculate emissions for each input
        total_emissions = Decimal("0")
        combined_ghg = {}
        combined_uncertainty = []
        warnings = []
        data_quality_scores = []
        
        # Track Scope 3 categories
        scope3_categories = set()
        
        for input_data in inputs:
            try:
                result = self._calculate_single_emission(input_data)
                total_emissions += result["emissions"]
                
                # Aggregate GHG breakdown
                for ghg in result["ghg_breakdown"]:
                    if ghg.gas_type not in combined_ghg:
                        combined_ghg[ghg.gas_type] = Decimal("0")
                    combined_ghg[ghg.gas_type] += ghg.amount
                
                # Track uncertainty
                combined_uncertainty.append({
                    "value": result["emissions"],
                    "uncertainty": result["uncertainty"],
                    "weight": float(result["emissions"]) / float(total_emissions) if total_emissions > 0 else 0
                })
                
                # Track data quality
                if result.get("data_quality"):
                    data_quality_scores.append(result["data_quality"])
                
                # Track Scope 3 category
                if input_data.scope3_category:
                    scope3_categories.add(input_data.scope3_category)
                
            except Exception as e:
                warning = f"Failed to calculate for {input_data.activity_unit}: {str(e)}"
                warnings.append(warning)
                logger.warning(warning)
        
        # Calculate combined uncertainty
        total_uncertainty = self.uncertainty_calc.combine_uncertainties(combined_uncertainty)
        
        # Aggregate data quality
        aggregated_quality = self._aggregate_data_quality(data_quality_scores)
        
        # Apply uncertainty calculation
        lower, central, upper = self.uncertainty_calc.calculate_uncertainty(
            total_emissions,
            total_uncertainty,
            UncertaintyDistributionEnum.LOGNORMAL,
            self.context.confidence_level,
            aggregated_quality
        )
        
        # Create GHG breakdown
        ghg_breakdown = [
            GHGBreakdown(
                gas_type=gas_type,
                amount=amount,
                unit="tCO2e",
                gwp_factor=self.gwp_factors.get(gas_type.value, Decimal("1")),
                gwp_version=self.context.gwp_version,
            )
            for gas_type, amount in combined_ghg.items()
        ]
        
        # Determine Scope 3 category (if single category)
        scope3_category = None
        scope3_category_name = None
        esrs_mapping = None
        cdp_mapping = None
        
        if len(scope3_categories) == 1:
            scope3_category = list(scope3_categories)[0]
            category_info = SCOPE3_CATEGORIES.get(scope3_category, {})
            scope3_category_name = category_info.get("display_name")
            esrs_mapping = category_info.get("esrs_requirements")
            cdp_mapping = category_info.get("cdp_questions")
        
        # Generate calculation hash
        calc_hash = self._generate_calculation_hash(inputs, total_emissions)
        
        # Create result
        result = CalculationResult(
            calculation_id=self.context.calculation_id,
            timestamp=calc_start,
            emissions_tco2e=central,
            ghg_breakdown=ghg_breakdown,
            uncertainty_percent=total_uncertainty,
            confidence_interval_lower=lower,
            confidence_interval_upper=upper,
            distribution_type=UncertaintyDistributionEnum.LOGNORMAL,
            calculation_method=self._determine_calculation_method(inputs),
            data_quality=aggregated_quality,
            tier_level=self._determine_tier_level(inputs),
            scope3_category=scope3_category,
            scope3_category_name=scope3_category_name,
            esrs_mapping=esrs_mapping,
            cdp_mapping=cdp_mapping,
            calculation_hash=calc_hash,
            input_data_hash=self._hash_inputs(inputs),
            audit_trail=self.audit_trail,
            warnings=warnings,
            applied_defaults=self.context.apply_cbam_defaults,
        )
        
        # Seal audit trail
        self._add_audit_entry("calculation_completed", {
            "total_emissions": str(central),
            "uncertainty": str(total_uncertainty),
            "duration_ms": (datetime.now(timezone.utc) - calc_start).total_seconds() * 1000,
        })
        self.audit_trail.seal()
        
        return result
    
    def _calculate_single_emission(self, input_data: CalculationInput) -> Dict[str, Any]:
        """Calculate emissions for a single input"""
        # Use region-specific factor if available
        emission_value = input_data.emission_factor.value
        if input_data.region and input_data.emission_factor.region == input_data.region:
            # Factor already region-specific
            pass
        elif input_data.region and self.db_session:
            # Try to get region-specific factor from database
            regional_factor = self._get_regional_factor(
                input_data.emission_factor.factor_id,
                input_data.region
            )
            if regional_factor:
                emission_value = regional_factor
        
        # Base calculation
        emissions = input_data.activity_data * emission_value
        
        # Apply allocation factor
        emissions *= input_data.allocation_factor
        
        # Apply temporal correlation
        emissions *= input_data.temporal_correlation
        
        # Determine uncertainty
        if input_data.uncertainty_override:
            uncertainty = input_data.uncertainty_override
        elif input_data.emission_factor.uncertainty_percentage:
            uncertainty = input_data.emission_factor.uncertainty_percentage
        else:
            # Use tier-based default
            tier = input_data.emission_factor.tier
            if input_data.emission_factor.tier_level:
                try:
                    tier = TierLevelEnum(input_data.emission_factor.tier_level)
                except:
                    pass
            uncertainty = DEFAULT_UNCERTAINTY_BY_TIER[tier.value]
        
        # Determine data quality
        if input_data.data_quality_override:
            data_quality = input_data.data_quality_override
        elif input_data.emission_factor.data_quality:
            data_quality = input_data.emission_factor.data_quality
        else:
            # Create from emission factor metadata
            data_quality = create_data_quality_from_factor(input_data.emission_factor)
        
        # Calculate GHG breakdown (simplified - assumes single gas)
        ghg_breakdown = [
            GHGBreakdown(
                gas_type=GasTypeEnum.CO2,  # Default to CO2
                amount=emissions,
                unit="tCO2e",
                gwp_factor=Decimal("1.0"),
                gwp_version=self.context.gwp_version,
            )
        ]
        
        return {
            "emissions": emissions,
            "uncertainty": uncertainty,
            "ghg_breakdown": ghg_breakdown,
            "data_quality": data_quality,
        }
    
    def calculate_scope3_by_category(
        self,
        category: str,
        activity_data: List[Dict[str, Any]],
        db_session: Optional[Session] = None
    ) -> CalculationResult:
        """Calculate Scope 3 emissions for a specific category"""
        if category not in SCOPE3_CATEGORIES:
            raise ValueError(f"Invalid Scope 3 category: {category}")
        
        # Use provided session or instance session
        session = db_session or self.db_session
        
        # Build calculation inputs
        calculation_inputs = []
        
        for item in activity_data:
            # Get emission factor from database if available
            emission_factor = None
            
            if session and item.get("factor_name"):
                # Try to get from database
                emission_factor = self._get_emission_factor_from_db(
                    session,
                    category,
                    item["factor_name"],
                    item.get("calculation_method", "activity_based"),
                    item.get("region")
                )
            
            if not emission_factor:
                # Use provided factor or raise error
                if "emission_factor" in item:
                    emission_factor = item["emission_factor"]
                else:
                    raise ValueError(f"No emission factor found for {item.get('factor_name', 'unknown')}")
            
            calc_input = CalculationInput(
                activity_data=Decimal(str(item["quantity"])),
                activity_unit=item.get("unit", "unit"),
                emission_factor=emission_factor,
                scope3_category=category,
                region=item.get("region"),
                allocation_factor=Decimal(str(item.get("allocation_factor", 1.0))),
                temporal_correlation=Decimal(str(item.get("temporal_correlation", 1.0)))
            )
            
            calculation_inputs.append(calc_input)
        
        # Calculate emissions
        return self.calculate_emissions(calculation_inputs)
    
    def _get_emission_factor_from_db(
        self,
        db_session: Session,
        category: str,
        factor_name: str,
        calculation_method: str,
        region: Optional[str] = None
    ) -> Optional[EmissionFactor]:
        """Retrieve emission factor from database with full compliance data"""
        try:
            from app.models.emission_factor import EmissionFactor as DBEmissionFactor
            
            # Query for matching factor
            query = db_session.query(DBEmissionFactor).filter(
                DBEmissionFactor.scope == 3,
                DBEmissionFactor.scope3_category == category,
                DBEmissionFactor.is_active == True
            )
            
            # Filter by calculation method if available
            if hasattr(DBEmissionFactor, 'calculation_method'):
                query = query.filter(DBEmissionFactor.calculation_method == calculation_method)
            
            # Filter by region if specified
            if region and hasattr(DBEmissionFactor, 'region'):
                query = query.filter(DBEmissionFactor.region == region)
            
            # Match by name
            query = query.filter(DBEmissionFactor.name.ilike(f"%{factor_name}%"))
            
            db_factor = query.first()
            
            if db_factor:
                # Build EmissionFactor with all available fields
                factor_data = {
                    "factor_id": str(db_factor.id),
                    "value": Decimal(str(db_factor.factor)),
                    "unit": db_factor.unit,
                    "source": db_factor.source,
                    "source_year": datetime.now().year,
                    "tier": TierLevelEnum.TIER_2,  # Default
                }
                
                # Add compliance fields if they exist
                if hasattr(db_factor, 'uncertainty_percentage') and db_factor.uncertainty_percentage:
                    factor_data["uncertainty_percentage"] = Decimal(str(db_factor.uncertainty_percentage))
                
                if hasattr(db_factor, 'data_quality_score') and db_factor.data_quality_score:
                    factor_data["data_quality_score"] = db_factor.data_quality_score
                
                if hasattr(db_factor, 'tier_level') and db_factor.tier_level:
                    factor_data["tier_level"] = db_factor.tier_level
                    try:
                        factor_data["tier"] = TierLevelEnum(db_factor.tier_level)
                    except:
                        pass
                
                if hasattr(db_factor, 'scope3_category'):
                    factor_data["scope3_category"] = category
                
                if hasattr(db_factor, 'calculation_method') and db_factor.calculation_method:
                    try:
                        factor_data["calculation_method"] = CalculationMethodEnum(db_factor.calculation_method)
                    except:
                        pass
                
                if hasattr(db_factor, 'temporal_representativeness'):
                    factor_data["temporal_representativeness"] = db_factor.temporal_representativeness
                
                if hasattr(db_factor, 'geographical_representativeness'):
                    factor_data["geographical_representativeness"] = db_factor.geographical_representativeness
                
                if hasattr(db_factor, 'methodology'):
                    factor_data["methodology"] = db_factor.methodology
                
                if hasattr(db_factor, 'lifecycle_stage'):
                    factor_data["lifecycle_stage"] = db_factor.lifecycle_stage
                
                if hasattr(db_factor, 'region'):
                    factor_data["region"] = db_factor.region
                
                if hasattr(db_factor, 'last_verified') and db_factor.last_verified:
                    factor_data["last_verified"] = db_factor.last_verified
                    factor_data["source_year"] = db_factor.last_verified.year
                
                return EmissionFactor(**factor_data)
            
        except Exception as e:
            logger.warning(f"Failed to get emission factor from DB: {e}")
        
        return None
    
    def _get_regional_factor(self, factor_id: str, region: str) -> Optional[Decimal]:
        """Get region-specific emission factor value"""
        if not self.db_session:
            return None
        
        try:
            from app.models.emission_factor import EmissionFactor as DBEmissionFactor
            
            # Try to find regional variant
            regional_factor = self.db_session.query(DBEmissionFactor).filter(
                DBEmissionFactor.id == factor_id,
                DBEmissionFactor.region == region,
                DBEmissionFactor.is_active == True
            ).first()
            
            if regional_factor:
                return Decimal(str(regional_factor.factor))
        
        except Exception as e:
            logger.warning(f"Failed to get regional factor: {e}")
        
        return None
    
    def assess_scope3_materiality(
        self,
        sector: str,
        total_emissions: Optional[Decimal] = None,
        category_emissions: Optional[Dict[str, Decimal]] = None
    ) -> List[MaterialityAssessment]:
        """Assess materiality for all Scope 3 categories"""
        assessments = []
        
        for category, info in SCOPE3_CATEGORIES.items():
            # Get threshold for sector
            threshold = MATERIALITY_THRESHOLDS.get(sector, MATERIALITY_THRESHOLDS["Default"])
            
            # Check if category is material for this sector
            is_material = sector in info.get("material_sectors", [])
            reasons = []
            
            if is_material:
                reasons.append(f"Category typically material for {sector} sector")
            
            # Check emissions threshold if data available
            actual_percentage = None
            if total_emissions and category_emissions and category in category_emissions:
                actual_percentage = (category_emissions[category] / total_emissions) * Decimal("100")
                if actual_percentage >= Decimal(str(threshold * 100)):
                    is_material = True
                    reasons.append(f"Emissions exceed {threshold*100}% materiality threshold")
            
            # Mandatory categories
            if category in ["purchased_goods_services", "use_of_sold_products"]:
                is_material = True
                reasons.append("Mandatory category for SBTi")
            
            # Recommendations
            recommendations = []
            if is_material:
                recommendations.append(f"Prioritize data collection for {info['display_name']}")
                recommendations.append("Engage suppliers for primary data")
            else:
                recommendations.append("Monitor for changes in business model")
                recommendations.append("Re-assess annually")
            
            # Data availability assessment
            if category in ["business_travel", "employee_commuting", "purchased_goods_services"]:
                data_availability = "high"
            elif category in ["upstream_transportation", "waste_operations"]:
                data_availability = "medium"
            else:
                data_availability = "low"
            
            assessment = MaterialityAssessment(
                category=category,
                category_name=info["display_name"],
                is_material=is_material,
                threshold_percentage=Decimal(str(threshold * 100)),
                actual_percentage=actual_percentage,
                reasons=reasons,
                recommendations=recommendations,
                data_availability=data_availability,
                sector=sector
            )
            
            assessments.append(assessment)
        
        # Sort by materiality
        assessments.sort(key=lambda x: (x.is_material, x.actual_percentage or 0), reverse=True)
        
        return assessments
    
    def generate_compliance_report(
        self,
        standard: str,
        emissions_by_category: Dict[str, Decimal],
        reporting_period: str
    ) -> ComplianceReport:
        """Generate compliance report for specified standard"""
        total_emissions = sum(emissions_by_category.values())
        
        # Calculate scope breakdown
        scope_breakdown = {
            "scope_1": Decimal("0"),
            "scope_2": Decimal("0"),
            "scope_3": Decimal("0")
        }
        
        # Categorize emissions
        for category, emissions in emissions_by_category.items():
            if category in SCOPE3_CATEGORIES:
                scope_breakdown["scope_3"] += emissions
            elif category in ["electricity", "heating_cooling"]:
                scope_breakdown["scope_2"] += emissions
            else:
                scope_breakdown["scope_1"] += emissions
        
        # Build category emissions with metadata
        category_emissions = {}
        requirements_met = []
        requirements_pending = []
        
        for category, emissions in emissions_by_category.items():
            if category in SCOPE3_CATEGORIES:
                info = SCOPE3_CATEGORIES[category]
                category_emissions[category] = {
                    "display_name": info["display_name"],
                    "emissions": float(emissions),
                    "percentage": float((emissions / total_emissions * 100)) if total_emissions > 0 else 0,
                    "esrs_requirements": info.get("esrs_requirements", []),
                    "cdp_questions": info.get("cdp_questions", [])
                }
                
                if standard == "ESRS":
                    if emissions > 0:
                        requirements_met.extend(info.get("esrs_requirements", []))
                    else:
                        requirements_pending.extend(info.get("esrs_requirements", []))
                elif standard == "CDP":
                    if emissions > 0:
                        requirements_met.extend(info.get("cdp_questions", []))
                    else:
                        requirements_pending.extend(info.get("cdp_questions", []))
        
        # Calculate completeness
        categories_calculated = len([c for c in SCOPE3_CATEGORIES if c in emissions_by_category and emissions_by_category[c] > 0])
        completeness_percentage = Decimal(str(categories_calculated / 15 * 100))
        
        # Determine compliance status
        if completeness_percentage >= 90:
            compliance_status = "Fully Compliant"
        elif completeness_percentage >= 70:
            compliance_status = "Substantially Compliant"
        else:
            compliance_status = "Partial Compliance"
        
        # Priority actions
        priority_actions = []
        if completeness_percentage < 90:
            priority_actions.append(f"Calculate emissions for {15 - categories_calculated} missing Scope 3 categories")
        priority_actions.append("Implement supplier engagement program")
        priority_actions.append("Establish primary data collection processes")
        
        # Improvement areas
        improvement_areas = []
        if scope_breakdown["scope_3"] / total_emissions < 0.7:
            improvement_areas.append("Scope 3 emissions may be underestimated")
        improvement_areas.append("Improve data quality through primary data collection")
        improvement_areas.append("Implement quarterly emissions tracking")
        
        return ComplianceReport(
            reporting_period=reporting_period,
            standard=standard,
            total_emissions=total_emissions,
            scope_breakdown=scope_breakdown,
            category_emissions=category_emissions,
            compliance_status=compliance_status,
            completeness_percentage=completeness_percentage,
            data_quality_score=Decimal("75"),  # Placeholder - should calculate from actual data
            requirements_met=list(set(requirements_met)),
            requirements_pending=list(set(requirements_pending)),
            priority_actions=priority_actions,
            improvement_areas=improvement_areas
        )
    
    def _aggregate_data_quality(self, quality_scores: List[DataQualityIndicators]) -> DataQualityIndicators:
        """Aggregate multiple data quality scores"""
        if not quality_scores:
            return self._default_data_quality(TierLevelEnum.TIER_2)
        
        # Calculate weighted average for each dimension
        dimensions = ["temporal", "geographical", "technological", "completeness", "reliability"]
        aggregated = {}
        
        for dim in dimensions:
            values = [getattr(q, dim) for q in quality_scores]
            aggregated[dim] = int(sum(values) / len(values))
        
        return DataQualityIndicators(**aggregated)
    
    def _default_data_quality(self, tier: TierLevelEnum) -> DataQualityIndicators:
        """Generate default data quality based on tier"""
        tier_quality = {
            TierLevelEnum.TIER_1: {"temporal": 60, "geographical": 60, "technological": 60, "completeness": 60, "reliability": 60},
            TierLevelEnum.TIER_2: {"temporal": 80, "geographical": 80, "technological": 80, "completeness": 80, "reliability": 80},
            TierLevelEnum.TIER_3: {"temporal": 95, "geographical": 95, "technological": 95, "completeness": 95, "reliability": 95},
        }
        
        return DataQualityIndicators(**tier_quality.get(tier, tier_quality[TierLevelEnum.TIER_2]))
    
    def _determine_calculation_method(self, inputs: List[CalculationInput]) -> CalculationMethodEnum:
        """Determine overall calculation method"""
        methods = set()
        for inp in inputs:
            if inp.emission_factor.calculation_method:
                methods.add(inp.emission_factor.calculation_method)
        
        if len(methods) == 1:
            return list(methods)[0]
        elif len(methods) > 1:
            return CalculationMethodEnum.HYBRID
        else:
            return CalculationMethodEnum.EMISSION_FACTOR
    
    def _determine_tier_level(self, inputs: List[CalculationInput]) -> TierLevelEnum:
        """Determine overall tier level from inputs"""
        if not inputs:
            return TierLevelEnum.TIER_1
        
        # Use lowest (most conservative) tier
        tiers = []
        for input_data in inputs:
            if input_data.emission_factor.tier_level:
                try:
                    tiers.append(TierLevelEnum(input_data.emission_factor.tier_level))
                except:
                    tiers.append(input_data.emission_factor.tier)
            else:
                tiers.append(input_data.emission_factor.tier)
        
        tier_order = [TierLevelEnum.TIER_1, TierLevelEnum.TIER_2, TierLevelEnum.TIER_3]
        
        for tier in tier_order:
            if tier in tiers:
                return tier
        
        return TierLevelEnum.TIER_1
    
    def _get_gwp_factors(self, version: GWPVersionEnum) -> Dict[str, Decimal]:
        """Get GWP factors for specified version"""
        if version == GWPVersionEnum.AR6_100:
            return GWP_FACTORS_AR6_100
        elif version == GWPVersionEnum.AR5_100:
            return GWP_FACTORS_AR5_100
        else:
            # Default to AR6
            return GWP_FACTORS_AR6_100
    
    def _generate_calculation_hash(
        self, inputs: List[CalculationInput], total: Decimal
    ) -> str:
        """Generate cryptographic hash of calculation"""
        calc_data = {
            "calculation_id": self.context.calculation_id,
            "timestamp": self.context.timestamp.isoformat(),
            "gwp_version": self.context.gwp_version.value,
            "inputs_count": len(inputs),
            "total_emissions": str(total),
        }
        
        # Add input hashes
        for i, input_data in enumerate(inputs):
            calc_data[f"input_{i}"] = self._hash_single_input(input_data)
        
        combined = json.dumps(calc_data, sort_keys=True)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
    
    def _hash_inputs(self, inputs: List[CalculationInput]) -> str:
        """Generate hash of all inputs"""
        input_hashes = [self._hash_single_input(inp) for inp in inputs]
        combined = "|".join(input_hashes)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
    
    def _hash_single_input(self, input_data: CalculationInput) -> str:
        """Generate hash for single input"""
        data = f"{input_data.activity_data}|{input_data.activity_unit}|{input_data.emission_factor.factor_id}|{input_data.emission_factor.value}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]
    
    def _add_audit_entry(self, action: str, details: Dict[str, Any]) -> None:
        """Add entry to audit trail"""
        self.audit_trail.add_entry(
            user_id=self.context.user_id,
            action="CREATE",
            field_changed=action,
            new_value=json.dumps(details),
        )
    
    def get_central_estimate(self) -> Decimal:
        """Get the central emissions estimate from last calculation"""
        # This method exists for compatibility
        # In practice, use calculate_emissions() and access result.emissions_tco2e
        return Decimal("0")


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================


def lookup_emission_factor(
    scope: int,
    category: str,
    country: str = 'Global'
) -> float:
    """
    Look up emission factor from FACTOR_DB with fallback logic.

    Args:
        scope: Emission scope (1, 2, or 3)
        category: Emission category (e.g., 'Mobile Combustion', 'Purchased Electricity')
        country: Country code (e.g., 'DE', 'US', 'FR') or 'Global'

    Returns:
        Emission factor value, with fallback to 'Global' then to DEFAULT_EMISSION_FACTOR
    """
    # Try specific country first
    key = (scope, category, country)
    if key in FACTOR_DB:
        logger.debug(f"Found emission factor for {key}: {FACTOR_DB[key]}")
        return FACTOR_DB[key]

    # Fallback to Global
    global_key = (scope, category, 'Global')
    if global_key in FACTOR_DB:
        logger.debug(f"Using Global fallback for {key}: {FACTOR_DB[global_key]}")
        return FACTOR_DB[global_key]

    # Fallback to default
    logger.warning(f"No emission factor found for {key}, using default: {DEFAULT_EMISSION_FACTOR}")
    return DEFAULT_EMISSION_FACTOR


def calculate_emissions(
    activity_value: float,
    emission_factor: Optional[float] = None,
    uncertainty_percent: float = 10.0,
    tier: TierLevelEnum = TierLevelEnum.TIER_2,
    scope: Optional[int] = None,
    category: Optional[str] = None,
    country: str = 'Global',
) -> float:
    """
    Simple convenience function for basic emissions calculation.

    Args:
        activity_value: Amount of activity (e.g., kWh, tonnes)
        emission_factor: Emission factor (e.g., kgCO2e/kWh). If not provided,
                        will be looked up from FACTOR_DB using scope/category/country.
        uncertainty_percent: Uncertainty percentage (default 10%)
        tier: Data quality tier level
        scope: Emission scope (1, 2, or 3) - used for FACTOR_DB lookup
        category: Emission category - used for FACTOR_DB lookup
        country: Country code (default 'Global') - used for FACTOR_DB lookup

    Returns:
        Calculated emissions in same units as emission factor
    """
    # Resolve emission factor
    if emission_factor is None:
        if scope is not None and category is not None:
            # Look up from FACTOR_DB
            emission_factor = lookup_emission_factor(scope, category, country)
        else:
            # Use default factor as fallback
            logger.warning("No emission_factor provided and no scope/category for lookup, using default")
            emission_factor = DEFAULT_EMISSION_FACTOR

    # Create minimal context
    context = CalculationContext(
        user_id="system",
        organization_id="default",
        gwp_version=GWPVersionEnum.AR6_100,
    )

    # Create emission factor object
    ef = EmissionFactor(
        factor_id="SIMPLE_CALC",
        value=Decimal(str(emission_factor)),
        unit="tCO2e/unit",
        source="FACTOR_DB" if scope and category else "User provided",
        source_year=datetime.now().year,
        tier=tier,
    )

    # Create input
    calc_input = CalculationInput(
        activity_data=Decimal(str(activity_value)),
        activity_unit="unit",
        emission_factor=ef,
        uncertainty_override=Decimal(str(uncertainty_percent)),
    )

    # Calculate
    calculator = EliteEmissionsCalculator(context)
    result = calculator.calculate_emissions([calc_input])

    return float(result.emissions_tco2e)


def calculate_scope3_emissions(
    category: str,
    activity_data: List[Dict[str, Any]],
    user_id: str = "system",
    organization_id: str = "default",
    db_session: Optional[Session] = None
) -> CalculationResult:
    """
    Calculate Scope 3 emissions for a specific category.
    
    Args:
        category: Scope 3 category key
        activity_data: List of activity data dictionaries
        user_id: User ID for audit
        organization_id: Organization ID
        db_session: Optional database session
    
    Returns:
        CalculationResult with emissions and uncertainty
    """
    # Create context
    context = CalculationContext(
        user_id=user_id,
        organization_id=organization_id,
        gwp_version=GWPVersionEnum.AR6_100,
    )
    
    # Create calculator
    calculator = EliteEmissionsCalculator(context, db_session=db_session)
    
    # Calculate emissions
    return calculator.calculate_scope3_by_category(category, activity_data, db_session)


# ==============================================================================
# EXPORT LIST
# ==============================================================================

__all__ = [
    # Main classes
    "EliteEmissionsCalculator",
    "UncertaintyCalculator",
    "CBAMCalculator",
    # Models
    "CalculationContext",
    "CalculationInput",
    "CalculationResult",
    "DataQualityIndicators",
    "EmissionFactor",
    "GHGBreakdown",
    "AuditTrail",
    "MaterialityAssessment",
    "ComplianceReport",
    # Enums
    "CalculationMethodEnum",
    "AllocationMethodEnum",
    "GasTypeEnum",
    "GWPVersionEnum",
    "TierLevelEnum",
    "UncertaintyDistributionEnum",
    "DataQualityDimension",
    # Functions
    "calculate_emissions",
    "calculate_scope3_emissions",
    "create_data_quality_from_factor",
    "lookup_emission_factor",
    # Constants
    "GWP_FACTORS_AR6_100",
    "GWP_FACTORS_AR5_100",
    "DEFAULT_UNCERTAINTY_BY_TIER",
    "CBAM_DEFAULT_FACTORS",
    "SCOPE3_CATEGORIES",
    "MATERIALITY_THRESHOLDS",
    "FACTOR_DB",
    "DEFAULT_EMISSION_FACTOR",
]