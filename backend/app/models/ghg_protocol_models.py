"""
Domain Models for GHG Protocol Scope 3 Emissions Calculator
Core entities representing the business domain following DDD principles
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# Enumerations
class Scope3Category(str, Enum):
    """15 Scope 3 Categories per GHG Protocol"""
    PURCHASED_GOODS_AND_SERVICES = "category_1"
    CAPITAL_GOODS = "category_2"
    FUEL_AND_ENERGY_RELATED = "category_3"
    UPSTREAM_TRANSPORTATION = "category_4"
    WASTE_GENERATED = "category_5"
    BUSINESS_TRAVEL = "category_6"
    EMPLOYEE_COMMUTING = "category_7"
    UPSTREAM_LEASED_ASSETS = "category_8"
    DOWNSTREAM_TRANSPORTATION = "category_9"
    PROCESSING_OF_SOLD_PRODUCTS = "category_10"
    USE_OF_SOLD_PRODUCTS = "category_11"
    END_OF_LIFE_TREATMENT = "category_12"
    DOWNSTREAM_LEASED_ASSETS = "category_13"
    FRANCHISES = "category_14"
    INVESTMENTS = "category_15"


class MethodologyType(str, Enum):
    """Calculation methodology approaches"""
    ACTIVITY_BASED = "activity_based"
    SPEND_BASED = "spend_based"
    HYBRID = "hybrid"
    AVERAGE_DATA = "average_data"
    SUPPLIER_SPECIFIC = "supplier_specific"


class DataQualityScore(int, Enum):
    """Data quality scoring per GHG Protocol"""
    VERIFIED_SPECIFIC = 1  # Highest quality
    UNVERIFIED_SPECIFIC = 2
    INDUSTRY_AVERAGE = 3
    PROXY_DATA = 4
    ESTIMATED = 5  # Lowest quality


class EmissionFactorSource(str, Enum):
    """Emission factor data sources"""
    EPA = "epa"
    DEFRA = "defra"
    IPCC = "ipcc"
    ECOINVENT = "ecoinvent"
    IEA = "iea"
    CUSTOM = "custom"
    SUPPLIER_SPECIFIC = "supplier_specific"


class UncertaintyDistribution(str, Enum):
    """Statistical distributions for uncertainty"""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"


class TransportMode(str, Enum):
    """Transportation modes for categories 4, 6, 7, 9"""
    ROAD = "road"
    RAIL = "rail"
    AIR = "air"
    SEA = "sea"
    INLAND_WATERWAY = "inland_waterway"
    PIPELINE = "pipeline"


class WasteTreatment(str, Enum):
    """Waste treatment methods"""
    LANDFILL = "landfill"
    INCINERATION = "incineration"
    RECYCLING = "recycling"
    COMPOSTING = "composting"
    ANAEROBIC_DIGESTION = "anaerobic_digestion"
    WASTEWATER = "wastewater"


class TemporalResolution(str, Enum):
    """Time granularity for calculations"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    DAILY = "daily"


# Value Objects
class Quantity(BaseModel):
    """Value object for quantities with units"""
    value: Decimal = Field(..., ge=0)
    unit: str
    
    @field_validator('value', mode="before")
    def coerce_decimal(cls, v):
        return Decimal(str(v))


class EmissionResult(BaseModel):
    """Value object for emission calculation results"""
    value: Decimal = Field(..., description="CO2e emissions in kg")
    uncertainty_lower: Optional[Decimal] = Field(None, description="P5 confidence interval")
    uncertainty_upper: Optional[Decimal] = Field(None, description="P95 confidence interval")
    unit: str = "kgCO2e"
    
    @field_validator('value', 'uncertainty_lower', 'uncertainty_upper', mode="before")
    def coerce_decimal(cls, v):
        return Decimal(str(v)) if v is not None else None


class DataQualityIndicator(BaseModel):
    """Pedigree matrix for data quality assessment"""
    reliability: DataQualityScore
    completeness: DataQualityScore
    temporal_correlation: DataQualityScore
    geographical_correlation: DataQualityScore
    technological_correlation: DataQualityScore
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted average score"""
        scores = [
            self.reliability.value,
            self.completeness.value,
            self.temporal_correlation.value,
            self.geographical_correlation.value,
            self.technological_correlation.value
        ]
        return sum(scores) / len(scores)


# Core Domain Entities
class EmissionFactor(BaseModel):
    """Core entity representing an emission factor"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    category: Scope3Category
    value: Decimal
    unit: str  # e.g., "kgCO2e/kg", "kgCO2e/kWh"
    source: EmissionFactorSource
    source_reference: str
    region: Optional[str] = None
    year: int
    uncertainty_range: Optional[tuple[float, float]] = None
    quality_indicator: Optional[DataQualityIndicator] = None
    metadata: Dict[str, Union[str, float, int]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('value', mode="before")
    def coerce_decimal(cls, v):
        return Decimal(str(v))


class ActivityData(BaseModel):
    """Core entity representing activity data input"""
    id: UUID = Field(default_factory=uuid4)
    category: Scope3Category
    description: str
    quantity: Quantity
    location: Optional[str] = None
    time_period: date
    data_source: str
    quality_indicator: DataQualityIndicator
    metadata: Dict[str, Union[str, float, int]] = Field(default_factory=dict)


class Organization(BaseModel):
    """Entity representing the reporting organization"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    industry: str
    reporting_year: int
    locations: List[str]
    baseline_year: Optional[int] = None
    target_year: Optional[int] = None
    sbti_committed: bool = False
    metadata: Dict[str, Union[str, float, int]] = Field(default_factory=dict)


class CalculationParameters(BaseModel):
    """Parameters for emission calculations"""
    methodology: MethodologyType
    include_uncertainty: bool = True
    confidence_level: float = 0.95
    monte_carlo_iterations: int = 10_000
    gwp_version: str = "AR6"  # IPCC Assessment Report version
    temporal_resolution: TemporalResolution = TemporalResolution.ANNUAL


# Category-Specific Models
class PurchasedGoodsActivity(ActivityData):
    """Category 1: Purchased Goods and Services"""
    product_description: str
    supplier_country: str
    unit_price: Optional[Decimal] = None
    material_composition: Optional[Dict[str, float]] = None
    recycled_content: Optional[float] = Field(None, ge=0, le=1)
    transport_distance: Optional[float] = None
    
    @field_validator('unit_price', mode="before")
    def coerce_decimal(cls, v):
        return Decimal(str(v)) if v is not None else None


class BusinessTravelActivity(ActivityData):
    """Category 6: Business Travel"""
    origin: str
    destination: str
    mode: TransportMode
    distance: float
    travelers: int = 1
    cabin_class: Optional[str] = None  # For air travel
    hotel_nights: Optional[int] = None
    hotel_country: Optional[str] = None


class UpstreamTransportActivity(ActivityData):
    """Category 4: Upstream Transportation"""
    origin: str
    destination: str
    mode: TransportMode
    distance: float
    weight: Quantity
    load_factor: Optional[float] = Field(None, ge=0, le=1)
    empty_return: bool = False
    refrigerated: bool = False


class WasteActivity(ActivityData):
    """Category 5: Waste Generated in Operations"""
    waste_type: str
    treatment_method: WasteTreatment
    moisture_content: Optional[float] = Field(None, ge=0, le=1)
    landfill_gas_capture: Optional[float] = Field(None, ge=0, le=1)
    recycling_rate: Optional[float] = Field(None, ge=0, le=1)


class UsePhaseActivity(ActivityData):
    """Category 11: Use of Sold Products"""
    product_model: str
    units_sold: int
    energy_consumption: Quantity  # Per use or per time
    product_lifetime: float  # Years
    usage_profile: Dict[str, float] = Field(default_factory=dict)  # Usage pattern
    geographic_distribution: Dict[str, float] = Field(default_factory=dict)  # Sales by region


# Calculation Results
class CategoryCalculationResult(BaseModel):
    """Result of a category-specific calculation"""
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    category: Scope3Category
    calculation_date: datetime = Field(default_factory=datetime.utcnow)
    reporting_period: date
    methodology: MethodologyType
    
    # Results
    emissions: EmissionResult
    activity_data_count: int
    data_quality_score: float
    
    # Breakdown
    emissions_by_source: Optional[Dict[str, EmissionResult]] = None
    emissions_by_region: Optional[Dict[str, EmissionResult]] = None
    emissions_by_time: Optional[Dict[str, EmissionResult]] = None
    
    # Audit trail
    calculation_parameters: CalculationParameters
    emission_factors_used: List[UUID]
    activity_data_used: List[UUID]
    assumptions: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    
    # Validation
    validated: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    reviewer: Optional[str] = None
    review_date: Optional[datetime] = None


class Scope3Inventory(BaseModel):
    """Complete Scope 3 inventory for an organization"""
    id: UUID = Field(default_factory=uuid4)
    organization: Organization
    reporting_year: int
    calculation_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Results by category
    category_results: Dict[Scope3Category, CategoryCalculationResult]
    
    # Aggregated results
    total_emissions: EmissionResult
    emissions_by_category: Dict[Scope3Category, EmissionResult]
    
    # Metadata
    completeness: float = Field(..., ge=0, le=1)  # % of categories calculated
    average_data_quality: float
    key_assumptions: List[str] = Field(default_factory=list)
    
    # Compliance
    ghg_protocol_compliant: bool = True
    iso_14064_compliant: bool = True
    third_party_verified: bool = False
    verification_statement: Optional[str] = None
    
    @model_validator(mode="after")
    def calculate_totals(cls, values):
        """Calculate total emissions from category results"""
        if 'category_results' in values:
            total = Decimal('0')
            for result in values['category_results'].values():
                total += result.emissions.value
            
            values['total_emissions'] = EmissionResult(value=total)
        return values


# Audit and Compliance
class AuditLogEntry(BaseModel):
    """Immutable audit log entry for calculations"""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    organization_id: UUID
    user: str
    action: str
    category: Optional[Scope3Category] = None
    calculation_id: Optional[UUID] = None
    
    # Change tracking
    previous_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    reason: Optional[str] = None
    
    # Compliance
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        frozen = True  # Immutable