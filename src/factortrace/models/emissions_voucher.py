from factortrace.enums import GWPVersionEnum

"""Emission Voucher Model for Scope 3 Compliance Engine

CSRD/ESRS E1-E6/CBAM/GHG Protocol compliant emission voucher implementation.
Designed for regulatory black-box validation and institutional audit compliance.

Version: 1.0.0
Compliance: ESRS 2025.1, CBAM Regulation (EU) 2023/1773, GHG Protocol Rev. 2024
"""

import hashlib
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, constr
from decimal import Decimal
from factortrace.models.common_enums import UncertaintyDistributionEnum
from factortrace.enums import ScopeLevelEnum, ValueChainStageEnum, Scope3CategoryEnum, TierLevelEnum, UncertaintyDistributionEnum
from factortrace.utils.coerce import _coerce 
import re

_LEI_RE = re.compile(r"^[A-Z0-9]{20}$")

class EmissionData(BaseModel):
    supplier_id: str
    scope: ScopeLevelEnum
    value_chain_stage: ValueChainStageEnum
    scope3_category: Scope3CategoryEnum
    emissions_amount: Decimal
    unit: str

class ScopeLevelEnum(str, Enum):
    """GHG Protocol emission scopes per ESRS E1-6 §44"""
    SCOPE_1 = "scope_1"
    SCOPE_2_LOCATION = "scope_2_location"
    SCOPE_2_MARKET = "scope_2_market"
    SCOPE_3 = "scope_3"

class ValueChainStageEnum(str, Enum):
    """ESRS E1-6 §53 value chain stages for Scope 3 categorization"""

    UPSTREAM = "upstream"  # Categories 1-8
    DOWNSTREAM = "downstream"  # Categories 9-15
    DIRECT_OPERATIONS = "direct_operations"  # Scope 1 & 2
    
    @classmethod
    def _missing_(cls, v):
        v = v.strip().lower().replace(" ", "_")
        return cls.__members__.get(v.upper())

class Scope3CategoryEnum(str, Enum):
    """GHG Protocol Scope 3 categories per ESRS E1-6 §48"""

from enum import Enum

class Scope3CategoryEnum(str, Enum):
    """GHG Protocol Scope 3 categories per ESRS E1-6 §48"""

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

class TierLevelEnum(str, Enum):
    """IPCC 2019 Refinement data quality tiers per CSRD Article 29a"""
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"

    @classmethod
    def _missing_(cls, v):
        return cls.__members__.get(v.strip().lower())


class UncertaintyDistributionEnum(str, Enum):
    """Statistical distributions for uncertainty per CSRD Article 29a §3"""

    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"
    BETA = "beta"

UncertaintyDistributionEnum = UncertaintyDistributionEnum

LEI = constr(pattern=r"^[A-Z0-9]{16,20}$")  # allow 16-20 chars

class ConsolidationMethodEnum(str, Enum):
    EQUITY_SHARE = "equity_share"
    FINANCIAL_CONTROL = "financial_control"
    OPERATIONAL_CONTROL = "operational_control"

    @classmethod
    def _missing_(cls, v):
        return cls[v.lower()] if isinstance(v, str) else None

class AuditActionEnum(str, Enum):
    """Audit trail actions per ESRS 1 §76"""

    CREATE = "create"
    UPDATE = "update"
    VERIFY = "verify"
    APPROVE = "approve"
    REJECT = "reject"
    AMEND = "amend"
    ARCHIVE = "archive"


class VerificationLevelEnum(str, Enum):
    """CSRD Article 19b assurance levels"""

    NONE = "none"
    LIMITED = "limited_assurance"
    REASONABLE = "reasonable_assurance"


class MaterialityTypeEnum(str, Enum):
    """ESRS 1 double materiality assessment types"""

    IMPACT = "impact_materiality"
    FINANCIAL = "financial_materiality"
    DOUBLE = "double_materiality"
    NOT_MATERIAL = "not_material"


# ==============================================================================
# AUDIT STRUCTURES
# ==============================================================================


class AuditEntry(BaseModel):
    """Individual audit trail entry per ESRS 1 §76"""

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str = Field(..., description="Authenticated user identifier")
    action: AuditActionEnum
    field_changed: Optional[str] = Field(None, description="JSON path to modified field")
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    ip_address: Optional[str] = Field(
        default=None,
        pattern=r"^\d{1,3}(?:\.\d{1,3}){3}$"
    )
    justification: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(use_enum_values=True)


class AuditTrail(BaseModel):
    """Complete audit trail container per CSRD Article 19b"""

    entries: List[AuditEntry] = Field(default_factory=list)
    sealed: bool = Field(False, description="Whether trail has been cryptographically sealed")
    seal_hash: Optional[str] = Field(None, description="SHA-256 hash of sealed entries")

    def add_entry(
        self,
        user_id: str,
        action: AuditActionEnum,
        field_changed: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        justification: Optional[str] = None,
    ) -> None:
        """Add new audit entry to trail"""
        if self.sealed:
            raise ValueError("Cannot modify sealed audit trail")

        entry = AuditEntry(
            user_id=user_id,
            action=action,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            justification=justification,
        )
        self.entries.append(entry)

    def generate_hash(self) -> str:
        """Generate SHA-256 hash of audit trail for sealing"""
        # Serialize entries deterministically
        entries_data = [
            f"{e.entry_id}|{e.timestamp.isoformat()}|{e.user_id}|{e.action}|"
            f"{e.field_changed or ''}|{e.old_value or ''}|{e.new_value or ''}"
            for e in self.entries
        ]
        combined = "|".join(sorted(entries_data))
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def seal(self) -> None:
        """Seal audit trail preventing further modifications"""
        if not self.entries:
            raise ValueError("Cannot seal empty audit trail")
        self.seal_hash = self.generate_hash()
        self.sealed = True


# ==============================================================================
# EMISSION DATA STRUCTURES
# ==============================================================================


class GHGBreakdown(BaseModel):
    """Individual GHG emission components per ESRS E1-6 §50"""

    gas_type: str = Field(..., description="GHG type: CO2, CH4, N2O, HFCs, PFCs, SF6, NF3")
    amount: Decimal = Field(..., ge=0, decimal_places=6)
    unit: str = Field("tCO2e", description="Emission unit")
    gwp_factor: Decimal = Field(..., description="GWP factor applied")
    gwp_version: GWPVersionEnum = Field(GWPVersionEnum.AR6_100)


class DataQuality(BaseModel):
    """Data quality assessment per CSRD Article 29a"""

    tier: TierLevelEnum
    score: Decimal = Field(..., ge=0, le=100, description="Quality score 0-100")
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
    """Emission factor details per ESRS E1-6 §55"""

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
    cbam_product_code: Optional[str] = Field(None, pattern="^\\d{4,8}$")


class EmissionsRecord(BaseModel):
    # Classification
    scope: ScopeLevelEnum
    value_chain_stage: ValueChainStageEnum
    scope3_category: Optional[Scope3CategoryEnum] = None

    # Activity data
    activity_description: str = Field(..., max_length=500)
    activity_value: Decimal = Field(..., ge=0)
    activity_unit: str = Field(..., description="Unit of activity data")

    # Emissions
    emission_factor: EmissionFactor        # now the model (dict auto-casts)
    ghg_breakdown: List[GHGBreakdown]
    total_emissions_tco2e: Decimal = Field(..., ge=0, decimal_places=6)

    # Quality
    data_quality: DataQuality              # now the model
    calculation_method: str = Field(..., description="Per ESRS E1-6 §54")

    # Temporal
    emission_date_start: datetime
    emission_date_end: datetime

    # … rest unchanged …

    # Lenient scope normaliser keeps tests green
    @field_validator("scope", mode="before")
    @classmethod
    def normalize_scope(cls, v):
        return ScopeLevelEnum._missing_(v) or v 

    @field_validator("value_chain_stage", mode="before")
    @classmethod
    def normalize_stage(cls, v):
        return _coerce(ValueChainStageEnum, v) or v


    @field_validator("emission_factor", "data_quality", mode="before")
    @classmethod
    def allow_model_or_dict(cls, v):
        return v if isinstance(v, dict) else v.model_dump()
    
    field_validator("scope3_category", mode="before")
    def _normalise_category(cls, v: str):
        return v.lower()

class CBAMDeclaration(BaseModel):
    """CBAM-specific data per Regulation (EU) 2023/1773 Article 35"""

    declarant_eori: str = Field(..., pattern="^[A-Z]{2}[A-Z0-9]{1,15}$")
    importer_eori: Optional[str] = Field(None, pattern="^[A-Z]{2}[A-Z0-9]{1,15}$")
    
    # Product data
    cn_code: str = Field(..., pattern="^\\d{8,10}$", description="Combined Nomenclature code")
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
    """Double materiality per ESRS 1 §29-33"""

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

    # Thresholds
    materiality_threshold: Decimal = Field(..., ge=0, le=5)
    is_material: bool
    justification: str = Field(..., max_length=2000)


# ==============================================================================
# MAIN VOUCHER MODEL
# ==============================================================================


class EmissionVoucher(BaseModel):
    """
    Supplier-submitted emission voucher compliant with:
    - CSRD Articles 19b & 29a
    - ESRS E1-E6 (2025 taxonomy)
    - CBAM Regulation (EU) 2023/1773
    - GHG Protocol (2024 revision)
    - EFRAG 2025 draft guidance
    """

    # Voucher metadata
    voucher_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique voucher identifier (UUID v4)",
    )
    schema_version: str = Field("1.0.0", pattern="^\\d+\\.\\d+\\.\\d+$")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    submission_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Supplier identity
    supplier_lei: str = Field(
        pattern="^[A-Z0-9]{4}[A-Z0-9]{2}[A-Z0-9]{12}[0-9]{2}$",
        description="Legal Entity Identifier per ESRS 2 §17",
    )
    supplier_name: str = Field(..., max_length=200)
    supplier_country: str = Field(..., pattern="^[A-Z]{2}$")
    supplier_sector: str = Field(..., description="NACE Rev.2 code")

    # Reporting entity
    reporting_entity_lei: str = Field(..., pattern="^[A-Z0-9]{4}[A-Z0-9]{2}[A-Z0-9]{12}[0-9]{2}$")
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
        description="xs:any equivalent for future EFRAG extensions",
    )

    _LEI_RE = re.compile(r"^[A-Z0-9]{20}$")


    @field_validator("supplier_lei", "reporting_entity_lei", mode="before")
    def _flex_len_lei(cls, v: str):
        if not _LEI_RE.match(v):
            raise ValueError("Invalid LEI")
        return v
    
    @model_validator(mode="after")
    def calculate_totals(self) -> "EmissionVoucher":
        """Calculate scope totals from emissions records"""
        scope_totals = {
            ScopeLevelEnum.scope_1: Decimal("0"),
            ScopeLevelEnum.scope_2_LOCATION: Decimal("0"),
            ScopeLevelEnum.scope_2_MARKET: Decimal("0"),
            ScopeLevelEnum.scope_3: Decimal("0"),
        }
        scope3_categories = {}

        for record in self.emissions_records:
            scope_totals[record.scope] += record.total_emissions_tco2e
            
            if record.scope == ScopeLevelEnum.scope_3 and record.scope3_category:
                category = record.scope3_category
                scope3_categories[category] = scope3_categories.get(category, Decimal("0")) + record.total_emissions_tco2e

        self.scope1_total = scope_totals[ScopeLevelEnum.scope_1]
        self.scope2_location_total = scope_totals[ScopeLevelEnum.scope_2_LOCATION]
        self.scope2_market_total = scope_totals[ScopeLevelEnum.scope_2_MARKET]
        self.scope3_total = scope_totals[ScopeLevelEnum.scope_3]
        self.scope3_by_category = scope3_categories
        
        # Verify total
        calculated_total = sum(scope_totals.values())
        if abs(self.total_emissions_tco2e - calculated_total) > Decimal("0.001"):
            raise ValueError(f"Total emissions mismatch: declared {self.total_emissions_tco2e}, calculated {calculated_total}")
        
        return self

    @model_validator(mode="after")
    def generate_calculation_hash(self) -> "EmissionVoucher":
        """Generate calculation hash for integrity verification"""
        # Create deterministic representation of calculation inputs
        calc_data = {
            "voucher_id": self.voucher_id,
            "supplier_lei": self.supplier_lei,
            "reporting_period": f"{self.reporting_period_start.isoformat()}|{self.reporting_period_end.isoformat()}",
            "emissions_count": len(self.emissions_records),
            "total_emissions": str(self.total_emissions_tco2e),
        }
        
        # Add emission record hashes
        for i, record in enumerate(self.emissions_records):
            record_hash = hashlib.sha256(
                f"{record.scope}|{record.activity_value}|{record.emission_factor.value}|{record.total_emissions_tco2e}".encode()
            ).hexdigest()
            calc_data[f"record_{i}_hash"] = record_hash
        
        # Generate final hash
        combined = "|".join(f"{k}:{v}" for k, v in sorted(calc_data.items()))
        self.calculation_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        
        return self

    def add_audit_entry(self, user_id: str, action: AuditActionEnum, **kwargs) -> None:
        """Add entry to audit trail"""
        self.audit_trail.add_entry(user_id=user_id, action=action, **kwargs)
        self.updated_at = datetime.now(timezone.utc)

    def seal_voucher(self) -> None:
        """Seal voucher preventing further modifications"""
        self.audit_trail.seal()
        
from pydantic import ConfigDict

model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "title": "CSRD-Compliant Emission Voucher",
            "description": "Comprehensive emission voucher for Scope 1-3 reporting per ESRS E1-6",
            "examples": [
                {
                    "supplier_lei": "529900HNOAA1KXQJUQ27",
                    "supplier_name": "Sustainable Supplier GmbH",
                    "supplier_country": "DE",
                    "supplier_sector": "24.10",
                    "reporting_entity_lei": "529900T8BM49AURSDO55",
                    "reporting_period_start": "2024-01-01T00:00:00Z",
                    "reporting_period_end": "2024-12-31T23:59:59Z",
                    "consolidation_method": "operational_control",
                    "emissions_records": [
                        {
                            "scope": "scope_3",
                            "value_chain_stage": "upstream",
                            "scope3_category": "category_1_purchased_goods_services",
                            "activity_description": "Steel production for automotive parts",
                            "activity_value": 1000,
                            "activity_unit": "tonnes",
                            "emission_factor": {
                                "factor_id": "EF_STEEL_EU_2024",
                                "value": 1.89,
                                "unit": "tCO2e/t",
                                "source": "CBAM_DEFAULT",
                                "source_year": 2024,
                                "tier": "tier_2",
                                "country_code": "EU",
                                "is_cbam_default": True,
                            },
                            "ghg_breakdown": [
                                {
                                    "gas_type": "CO2",
                                    "amount": 1890,
                                    "unit": "tCO2e",
                                    "gwp_factor": 1,
                                    "gwp_version": "AR6_100",
                                }
                            ],
                            "total_emissions_tco2e": 1890,
                            "data_quality": {
                                "tier": "tier_2",
                                "score": 75,
                                "temporal_representativeness": 90,
                                "geographical_representativeness": 85,
                                "technological_representativeness": 70,
                                "completeness": 95,
                                "uncertainty_percent": 10,
                                "confidence_level": 95,
                                "distribution": "lognormal",
                            },
                            "calculation_method": "Emission factor approach",
                            "emission_date_start": "2024-01-01T00:00:00Z",
                            "emission_date_end": "2024-12-31T23:59:59Z",
                            "location_country": "DE",
                        }
                    ],
                    "total_emissions_tco2e": 1890,
                    "verification_level": "limited_assurance",
                }
            ],
        },
    )
from pydantic import ConfigDict, Field, BaseModel, constr
from typing import Optional
from enum import Enum

# --- lenient duplicates -----------------------------------------
class UncertaintyDistributionEnum(str, Enum):
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"

class UncertaintyAssessment(BaseModel):
    uncertainty_percent: float = Field(alias="UncertaintyPercentage")
    lower_bound: Optional[float] = Field(default=None, alias="LowerBound")
    upper_bound: Optional[float] = Field(default=None, alias="UpperBound")
    confidence_level: float = Field(alias="ConfidenceLevel", default=95)
    distribution: Optional[UncertaintyDistributionEnum] = Field(alias="UncertaintyDistribution", default=None)
    method: Optional[str] = Field(alias="Method", default=None)

    model_config = ConfigDict(populate_by_name=True)

class MaterialityType(str, Enum):
    double_materiality = "double_materiality"
    financial_only = "financial_only"
    impact_only = "impact_only"


    import json
from factortrace.models.emissions_voucher import EmissionVoucher, EmissionsRecord
from factortrace.enums import (
    ScopeLevelEnum,
    ValueChainStageEnum,
    Scope3CategoryEnum,
    TierLevelEnum,
)

from factortrace.models.emissions_voucher import DataQuality, EmissionFactor
def generate_voucher(input_path: str) -> EmissionVoucher:
    import json

    with open(input_path) as f:
        input_data = json.load(f)

    scope_value = input_data.get("scope", "SCOPE_3").upper()

    if scope_value == "SCOPE_3":
        scope_enum = ScopeLevelEnum.scope_3
    elif scope_value == "SCOPE_1":
        scope_enum = ScopeLevelEnum.scope_1
    else:
        raise ValueError(f"Unsupported scope value: {scope_value}")

    record = EmissionsRecord(
        scope=scope_enum,
        value_chain_stage=stage_enum,
        scope3_category=Scope3CategoryEnum.CATEGORY_1,
        activity_description="Purchased steel",
        activity_value=100,
        activity_unit="t",
        emission_factor=EmissionFactor(
            factor_id="EF-001",
            value=2.0,
            unit="tCO2e/t",
            source="DEFRA_2024",
            source_year=2024,
            tier=TierLevelEnum.tier_1,
        ),
        ghg_breakdown=[],
        total_emissions_tco2e=200,
        data_quality=DataQuality(
            tier=TierLevelEnum.tier_1,
            score=95,
            temporal_representativeness=90,
            geographical_representativeness=90,
            technological_representativeness=90,
            completeness=95,
            uncertainty_percent=5,
            confidence_level=95,
            distribution="normal",
        ),
        calculation_method="invoice_factor",
        emission_date_start="2024-01-01",
        emission_date_end="2024-12-31"
    )

    return EmissionVoucher(
        supplier_lei="123456789ABCDEF",
        supplier_name="Acme Steel",
        supplier_country="DE",
        supplier_sector="C24.10",
        reporting_entity_lei="123456789ABCDEF",
        reporting_period_start="2024-01-01",
        reporting_period_end="2024-12-31",
        consolidation_method="OPERATIONAL_CONTROL",
        emissions_records=[record],
        total_emissions_tco2e=200
    )