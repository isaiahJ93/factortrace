# app/models/emissions_voucher.py
"""
ESRS E1/CBAM/GHG Protocol compliant emission voucher model
Designed for regulatory compliance and institutional audit requirements

Standards Compliance:
- ESRS E1-E6 (2025 taxonomy)
- CBAM Regulation (EU) 2023/1773
- GHG Protocol Corporate Standard (2024 revision)
- ISO 14064-1:2018
"""
from __future__ import annotations

import hashlib
import uuid
import re
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Dict, List, Union

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, constr

# ============================================================================
# ENUMERATIONS - Compliance with ESRS/GHG Protocol standards
# ============================================================================

class ScopeLevelEnum(str, Enum):
    """GHG Protocol Scope definitions"""
    SCOPE_1 = "scope_1"  # Direct emissions
    SCOPE_2_LOCATION = "scope_2_location"  # Location-based electricity
    SCOPE_2_MARKET = "scope_2_market"  # Market-based electricity
    SCOPE_3 = "scope_3"  # Value chain emissions

    @classmethod
    def _missing_(cls, value):
        """Flexible parsing for various input formats"""
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
            for member in cls:
                if member.value == normalized or member.name.lower() == normalized:
                    return member
        return None


class Scope3CategoryEnum(str, Enum):
    """GHG Protocol Scope 3 Categories"""
    CAT_1 = "category_1_purchased_goods_services"
    CAT_2 = "category_2_capital_goods"
    CAT_3 = "category_3_fuel_energy_activities"
    CAT_4 = "category_4_upstream_transportation"
    CAT_5 = "category_5_waste_generated_operations"
    CAT_6 = "category_6_business_travel"
    CAT_7 = "category_7_employee_commuting"
    CAT_8 = "category_8_upstream_leased_assets"
    CAT_9 = "category_9_downstream_transportation"
    CAT_10 = "category_10_processing_sold_products"
    CAT_11 = "category_11_use_sold_products"
    CAT_12 = "category_12_end_of_life_sold_products"
    CAT_13 = "category_13_downstream_leased_assets"
    CAT_14 = "category_14_franchises"
    CAT_15 = "category_15_investments"


class ValueChainStageEnum(str, Enum):
    """Value chain position for emissions"""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    DIRECT_OPERATIONS = "direct_operations"


class GWPVersionEnum(str, Enum):
    """IPCC Global Warming Potential versions"""
    AR4_100 = "AR4_100"  # Fourth Assessment Report
    AR5_100 = "AR5_100"  # Fifth Assessment Report
    AR6_100 = "AR6_100"  # Sixth Assessment Report (latest)


class TierLevelEnum(str, Enum):
    """IPCC Tier methodology levels"""
    TIER_1 = "tier_1"  # Default emission factors
    TIER_2 = "tier_2"  # Country/technology specific
    TIER_3 = "tier_3"  # Facility specific measurements


class UncertaintyDistributionEnum(str, Enum):
    """Statistical distribution types for uncertainty"""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"
    BETA = "beta"


class ConsolidationMethodEnum(str, Enum):
    """GHG Protocol consolidation approaches"""
    EQUITY_SHARE = "equity_share"
    FINANCIAL_CONTROL = "financial_control"
    OPERATIONAL_CONTROL = "operational_control"


class VerificationLevelEnum(str, Enum):
    """Third-party verification levels"""
    NONE = "none"
    LIMITED = "limited_assurance"
    REASONABLE = "reasonable_assurance"


class AuditActionEnum(str, Enum):
    """Audit trail action types"""
    CREATE = "create"
    UPDATE = "update"
    VERIFY = "verify"
    APPROVE = "approve"
    REJECT = "reject"
    AMEND = "amend"
    ARCHIVE = "archive"


class MaterialityTypeEnum(str, Enum):
    """ESRS double materiality assessment types"""
    IMPACT = "impact_materiality"  # Inside-out
    FINANCIAL = "financial_materiality"  # Outside-in
    DOUBLE = "double_materiality"  # Both
    NOT_MATERIAL = "not_material"


class GasTypeEnum(str, Enum):
    """Greenhouse gas types per IPCC"""
    CO2 = "CO2"
    CH4 = "CH4"
    N2O = "N2O"
    HFCS = "HFCs"
    PFCS = "PFCs"
    SF6 = "SF6"
    NF3 = "NF3"


# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

# Legal Entity Identifier pattern (20 characters)
LEI_PATTERN = re.compile(r"^[A-Z0-9]{4}[A-Z0-9]{2}[A-Z0-9]{12}[0-9]{2}$")

# EORI (Economic Operators Registration and Identification) pattern
EORI_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{1,15}$")

# Country code (ISO 3166-1 alpha-2)
COUNTRY_CODE_PATTERN = re.compile(r"^[A-Z]{2}$")

# Combined Nomenclature code (EU customs)
CN_CODE_PATTERN = re.compile(r"^\d{8,10}$")

# ============================================================================
# AUDIT TRAIL MODELS
# ============================================================================

class AuditEntry(BaseModel):
    """Individual audit trail entry"""
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str = Field(..., description="Authenticated user identifier")
    action: AuditActionEnum
    field_changed: Optional[str] = Field(None, description="JSON path to modified field")
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    ip_address: Optional[str] = Field(None, pattern=r"^\d{1,3}(?:\.\d{1,3}){3}$")
    justification: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(use_enum_values=True)


class AuditTrail(BaseModel):
    """Complete audit trail with cryptographic sealing"""
    entries: List[AuditEntry] = Field(default_factory=list)
    sealed: bool = Field(False, description="Whether trail has been cryptographically sealed")
    seal_hash: Optional[str] = Field(None, description="SHA-256 hash of sealed entries")

    def add_entry(self, user_id: str, action: AuditActionEnum, **kwargs) -> None:
        """Add a new audit entry"""
        if self.sealed:
            raise ValueError("Cannot modify sealed audit trail")
        
        entry = AuditEntry(user_id=user_id, action=action, **kwargs)
        self.entries.append(entry)

    def generate_hash(self) -> str:
        """Generate cryptographic hash of all entries"""
        entries_data = [
            f"{e.entry_id}|{e.timestamp.isoformat()}|{e.user_id}|{e.action}|"
            f"{e.field_changed or ''}|{e.old_value or ''}|{e.new_value or ''}"
            for e in self.entries
        ]
        combined = "|".join(entries_data)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def seal(self) -> None:
        """Cryptographically seal the audit trail"""
        if not self.entries:
            raise ValueError("Cannot seal empty audit trail")
        self.seal_hash = self.generate_hash()
        self.sealed = True


# ============================================================================
# EMISSION DATA MODELS
# ============================================================================

class GHGBreakdown(BaseModel):
    """Individual greenhouse gas contribution"""
    gas_type: GasTypeEnum
    amount: Decimal = Field(..., ge=0, decimal_places=6)
    unit: str = Field("tCO2e", description="Emission unit")
    gwp_factor: Decimal = Field(..., gt=0, description="GWP factor applied")
    gwp_version: GWPVersionEnum = Field(GWPVersionEnum.AR6_100)


class DataQuality(BaseModel):
    """Data quality assessment per ESRS E1 requirements"""
    tier: TierLevelEnum
    score: Decimal = Field(..., ge=0, le=100, description="Quality score 0-100")
    
    # Representativeness scores
    temporal_representativeness: Decimal = Field(..., ge=0, le=100)
    geographical_representativeness: Decimal = Field(..., ge=0, le=100)
    technological_representativeness: Decimal = Field(..., ge=0, le=100)
    completeness: Decimal = Field(..., ge=0, le=100, description="Data completeness %")
    
    # Statistical quality
    uncertainty_percent: Decimal = Field(..., ge=0, le=100)
    confidence_level: Decimal = Field(95, ge=50, le=99.9)
    distribution: UncertaintyDistributionEnum = Field(UncertaintyDistributionEnum.LOGNORMAL)
    
    # Metadata
    data_gaps: List[str] = Field(default_factory=list)
    estimation_method: Optional[str] = Field(None, max_length=200)
    last_quality_review: Optional[datetime] = None


class EmissionFactor(BaseModel):
    """Emission factor with source tracking"""
    factor_id: str = Field(..., description="Unique factor identifier")
    value: Decimal = Field(..., gt=0, decimal_places=9)
    unit: str = Field(..., description="e.g. kgCO2e/kWh, tCO2e/t")
    source: str = Field(..., description="e.g. IPCC_2024, DEFRA_2024, CBAM_DEFAULT")
    source_year: int = Field(..., ge=2020, le=2030)
    
    # Quality attributes
    tier: TierLevelEnum
    country_code: Optional[str] = Field(None, pattern="^[A-Z]{2}$")
    region_code: Optional[str] = Field(None, description="NUTS code for EU regions")
    technology: Optional[str] = Field(None, max_length=100)
    
    # CBAM specific
    is_cbam_default: bool = Field(False)
    cbam_product_code: Optional[str] = Field(None, pattern=r"^\d{4,8}$")


class EmissionsRecord(BaseModel):
    """Individual emission activity record"""
    # Classification
    scope: ScopeLevelEnum
    value_chain_stage: ValueChainStageEnum
    scope3_category: Optional[Scope3CategoryEnum] = None
    
    # Activity data
    activity_description: str = Field(..., max_length=500)
    activity_value: Decimal = Field(..., ge=0)
    activity_unit: str = Field(..., description="Unit of activity data")
    
    # Emissions calculation
    emission_factor: EmissionFactor
    ghg_breakdown: List[GHGBreakdown]
    total_emissions_tco2e: Decimal = Field(..., ge=0, decimal_places=6)
    
    # Quality assessment
    data_quality: DataQuality
    calculation_method: str = Field(..., description="Per ESRS E1-6 S54")
    
    # Temporal boundaries
    emission_date_start: datetime
    emission_date_end: datetime
    
    # Location (optional)
    location_country: Optional[str] = Field(None, pattern="^[A-Z]{2}$")
    location_region: Optional[str] = None
    facility_id: Optional[str] = None
    
    # Evidence/documentation
    evidence_urls: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("scope3_category")
    def validate_scope3_category(cls, v, values):
        """Ensure Scope 3 category is only set for Scope 3 emissions"""
        if values.get("scope") == ScopeLevelEnum.SCOPE_3 and not v:
            raise ValueError("Scope 3 emissions must specify a category")
        if values.get("scope") != ScopeLevelEnum.SCOPE_3 and v:
            raise ValueError("Scope 3 category can only be set for Scope 3 emissions")
        return v


class CBAMDeclaration(BaseModel):
    """Carbon Border Adjustment Mechanism declaration"""
    declarant_eori: str = Field(..., pattern=EORI_PATTERN.pattern)
    importer_eori: Optional[str] = Field(None, pattern=EORI_PATTERN.pattern)
    
    # Product data
    cn_code: str = Field(..., pattern=CN_CODE_PATTERN.pattern)
    product_description: str = Field(..., max_length=500)
    quantity_imported: Decimal = Field(..., gt=0)
    quantity_unit: str = Field(..., description="tonnes, MWh, etc.")
    customs_value_eur: Decimal = Field(..., ge=0)
    
    # Embedded emissions
    embedded_emissions_direct: Decimal = Field(..., ge=0, description="tCO2e")
    embedded_emissions_indirect: Decimal = Field(..., ge=0, description="tCO2e")
    emissions_intensity: Decimal = Field(..., ge=0, description="tCO2e/unit")
    
    # Carbon pricing
    carbon_price_paid: Optional[Decimal] = Field(None, ge=0, description="EUR/tCO2e")
    carbon_price_currency: str = Field("EUR", pattern="^[A-Z]{3}$")
    carbon_price_jurisdiction: Optional[str] = None
    ets_allowances_surrendered: Optional[Decimal] = Field(None, ge=0)
    
    # Verification
    cbam_verifier_id: Optional[str] = None
    cbam_verification_date: Optional[datetime] = None
    default_values_used: bool = Field(False)
    default_values_justification: Optional[str] = Field(None, max_length=1000)


class MaterialityAssessment(BaseModel):
    """ESRS double materiality assessment"""
    assessment_date: datetime
    materiality_type: MaterialityTypeEnum
    
    # Impact materiality (inside-out)
    impact_score: Decimal = Field(..., ge=1, le=5, decimal_places=2)
    impact_likelihood: Decimal = Field(..., ge=1, le=5)
    impact_magnitude: Decimal = Field(..., ge=1, le=5)
    impact_scope: List[str] = Field(..., description="Affected stakeholder groups")
    
    # Financial materiality (outside-in)
    financial_score: Decimal = Field(..., ge=1, le=5, decimal_places=2)
    financial_likelihood: Decimal = Field(..., ge=1, le=5)
    financial_magnitude_eur: Optional[Decimal] = Field(None, ge=0)
    financial_time_horizon: str = Field(..., pattern="^(short|medium|long)$")
    
    # Thresholds and decision
    materiality_threshold: Decimal = Field(..., ge=0, le=5)
    is_material: bool
    justification: str = Field(..., max_length=2000)


# ============================================================================
# MAIN EMISSION VOUCHER MODEL
# ============================================================================

class EmissionVoucher(BaseModel):
    """
    ESRS E1/CBAM/GHG Protocol compliant emission voucher
    
    This model represents a complete emissions declaration including:
    - Organizational boundaries and reporting period
    - Detailed emissions records with quality assessment
    - Compliance and verification information
    - Complete audit trail
    """
    
    # Voucher metadata
    voucher_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique voucher identifier (UUID v4)"
    )
    schema_version: str = Field("1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    submission_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Supplier identity
    supplier_lei: str = Field(..., description="Legal Entity Identifier")
    supplier_name: str = Field(..., max_length=200)
    supplier_country: str = Field(..., pattern=COUNTRY_CODE_PATTERN.pattern)
    supplier_sector: str = Field(..., description="NACE Rev.2 code")
    
    # Reporting entity
    reporting_entity_lei: str = Field(...)
    reporting_period_start: datetime
    reporting_period_end: datetime
    consolidation_method: ConsolidationMethodEnum
    
    # Emissions data
    emissions_records: List[EmissionsRecord] = Field(..., min_length=1)
    total_emissions_tco2e: Decimal = Field(..., ge=0, decimal_places=6)
    
    # Calculated breakdowns
    scope1_total: Decimal = Field(0, ge=0)
    scope2_location_total: Decimal = Field(0, ge=0)
    scope2_market_total: Decimal = Field(0, ge=0)
    scope3_total: Decimal = Field(0, ge=0)
    scope3_by_category: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Compliance data
    cbam_declaration: Optional[CBAMDeclaration] = None
    materiality_assessment: Optional[MaterialityAssessment] = None
    verification_level: VerificationLevelEnum = Field(VerificationLevelEnum.NONE)
    verifier_accreditation_id: Optional[str] = None
    verification_statement_url: Optional[str] = Field(None, pattern="^https://")
    
    # Audit trail
    audit_trail: AuditTrail = Field(default_factory=AuditTrail)
    calculation_hash: Optional[str] = Field(None, description="SHA-256 hash of calculation inputs")
    
    # Forward compatibility
    extension_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extension point for future standards"
    )
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "title": "ESRS E1 Compliant Emission Voucher",
            "description": "Comprehensive emission voucher for regulatory compliance"
        }
    )
    
    @field_validator("supplier_lei", "reporting_entity_lei")
    def validate_lei(cls, v):
        """Validate Legal Entity Identifier format"""
        if not LEI_PATTERN.match(v):
            raise ValueError(f"Invalid LEI format: {v}")
        return v
    
    @field_validator("reporting_period_end")
    def validate_reporting_period(cls, v, values):
        """Ensure reporting period is valid"""
        start = values.get("reporting_period_start")
        if start and v <= start:
            raise ValueError("Reporting period end must be after start")
        return v
    
    @model_validator(mode="after")
    def calculate_totals(self) -> "EmissionVoucher":
        """Calculate scope totals and validate consistency"""
        scope_totals = {
            ScopeLevelEnum.SCOPE_1: Decimal(0),
            ScopeLevelEnum.SCOPE_2_LOCATION: Decimal(0),
            ScopeLevelEnum.SCOPE_2_MARKET: Decimal(0),
            ScopeLevelEnum.SCOPE_3: Decimal(0),
        }
        scope3_categories = {}
        
        for record in self.emissions_records:
            scope_totals[record.scope] += record.total_emissions_tco2e
            
            if record.scope == ScopeLevelEnum.SCOPE_3 and record.scope3_category:
                category = record.scope3_category.value
                scope3_categories[category] = scope3_categories.get(
                    category, Decimal(0)
                ) + record.total_emissions_tco2e
        
        # Update totals
        self.scope1_total = scope_totals[ScopeLevelEnum.SCOPE_1]
        self.scope2_location_total = scope_totals[ScopeLevelEnum.SCOPE_2_LOCATION]
        self.scope2_market_total = scope_totals[ScopeLevelEnum.SCOPE_2_MARKET]
        self.scope3_total = scope_totals[ScopeLevelEnum.SCOPE_3]
        self.scope3_by_category = scope3_categories
        
        # Verify total consistency
        calculated_total = sum(scope_totals.values())
        if abs(self.total_emissions_tco2e - calculated_total) > Decimal("0.01"):
            raise ValueError(
                f"Total emissions mismatch: declared {self.total_emissions_tco2e}, "
                f"calculated {calculated_total}"
            )
        
        return self
    
    @model_validator(mode="after")
    def generate_calculation_hash(self) -> "EmissionVoucher":
        """Generate cryptographic hash of calculation inputs"""
        calc_data = {
            "voucher_id": self.voucher_id,
            "supplier_lei": self.supplier_lei,
            "reporting_period": f"{self.reporting_period_start.isoformat()}|{self.reporting_period_end.isoformat()}",
            "emissions_count": len(self.emissions_records),
            "total_emissions": str(self.total_emissions_tco2e),
        }
        
        # Add emission record hashes
        for i, record in enumerate(self.emissions_records):
            record_data = (
                f"{record.scope.value}|{record.activity_value}|"
                f"{record.emission_factor.value}|{record.total_emissions_tco2e}"
            )
            record_hash = hashlib.sha256(record_data.encode()).hexdigest()
            calc_data[f"record_{i}_hash"] = record_hash
        
        # Generate final hash
        combined = "|".join(f"{k}:{v}" for k, v in sorted(calc_data.items()))
        self.calculation_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        
        return self
    
    def add_audit_entry(self, user_id: str, action: AuditActionEnum, **kwargs) -> None:
        """Add an audit trail entry"""
        self.audit_trail.add_entry(user_id, action, **kwargs)
        self.updated_at = datetime.now(timezone.utc)
    
    def seal_voucher(self) -> None:
        """Cryptographically seal the voucher"""
        self.audit_trail.seal()
        self.updated_at = datetime.now(timezone.utc)
    
    def get_emissions_summary(self) -> Dict[str, Any]:
        """Get a summary of emissions by scope and category"""
        return {
            "total_emissions": float(self.total_emissions_tco2e),
            "by_scope": {
                "scope_1": float(self.scope1_total),
                "scope_2_location": float(self.scope2_location_total),
                "scope_2_market": float(self.scope2_market_total),
                "scope_3": float(self.scope3_total),
            },
            "scope_3_breakdown": {
                category: float(amount) 
                for category, amount in self.scope3_by_category.items()
            },
            "verification_status": self.verification_level.value,
            "data_quality_average": self._calculate_average_quality_score()
        }
    
    def _calculate_average_quality_score(self) -> float:
        """Calculate average data quality score across all records"""
        if not self.emissions_records:
            return 0.0
        
        total_score = sum(record.data_quality.score for record in self.emissions_records)
        return float(total_score / len(self.emissions_records))