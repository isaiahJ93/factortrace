# backend/app/models/emission.py
"""
SQLAlchemy model for emissions
Clean implementation that works with the API endpoints
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Integer, String, DateTime, Float, Text, ForeignKey, Enum, JSON
from sqlalchemy import String, DateTime, Float, Text, ForeignKey, Enum, JSON
from app.core.database import Base
import enum
from typing import Optional
from datetime import datetime

class EmissionScope(enum.IntEnum):
    """GHG Protocol emission scopes"""
    SCOPE_1 = 1  # Direct emissions
    SCOPE_2 = 2  # Indirect emissions from energy
    SCOPE_3 = 3  # Value chain emissions

class DataSourceType(str, enum.Enum):
    """Data source types for quality tracking"""
    MEASURED = "measured"      # Primary data from direct measurement
    CALCULATED = "calculated"  # Calculated from activity data
    ESTIMATED = "estimated"    # Estimated using proxies
    DEFAULT = "default"        # Default emission factors

class Scope3Category(str, enum.Enum):
    """Scope 3 categories as per GHG Protocol"""
    PURCHASED_GOODS = "purchased_goods_services"
    CAPITAL_GOODS = "capital_goods"
    FUEL_ENERGY = "fuel_energy_activities"
    UPSTREAM_TRANSPORTATION = "upstream_transportation"
    WASTE_GENERATED = "waste_generated"
    BUSINESS_TRAVEL = "business_travel"
    EMPLOYEE_COMMUTING = "employee_commuting"
    UPSTREAM_LEASED = "upstream_leased_assets"
    DOWNSTREAM_TRANSPORTATION = "downstream_transportation"
    PROCESSING_SOLD_PRODUCTS = "processing_sold_products"
    USE_OF_SOLD_PRODUCTS = "use_sold_products"
    END_OF_LIFE = "end_of_life_treatment"
    DOWNSTREAM_LEASED = "downstream_leased_assets"
    FRANCHISES = "franchises"
    INVESTMENTS = "investments"

class Emission(Base):
    """
    Emission model for tracking GHG emissions
    
    This model stores individual emission entries with support for
    all three scopes as defined by the GHG Protocol.
    """
    __tablename__ = "emissions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional for now
    # organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Core emission data
    scope = Column(SQLEnum(EmissionScope), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)  # For more detailed categorization
    
    # Activity data
    activity_data = Column(Float, nullable=False, comment="Quantity of activity (e.g., kWh, km, kg)")
    unit = Column(String(50), nullable=False, comment="Unit of measurement for activity")
    
    # Emission calculation
    emission_factor = Column(Float, nullable=True, comment="Emission factor used (kgCO2e per unit)")
    emission_factor_source = Column(String(200), nullable=True, comment="Source of emission factor")
    amount = Column(Float, nullable=False, comment="Calculated emission amount in tCO2e")
    
    # Data quality
    data_source = Column(SQLEnum(DataSourceType), nullable=True, default=DataSourceType.CALCULATED)
    data_quality_score = Column(Integer, nullable=True, comment="Data quality score 1-100")
    uncertainty_percentage = Column(Float, nullable=True, comment="Uncertainty percentage")
    
    # Location and time
    location = Column(String(200), nullable=True, comment="Location/facility name")
    country_code = Column(String(2), nullable=True, comment="ISO country code")
    reporting_period_start = Column(DateTime(timezone=True), nullable=True)
    reporting_period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True, comment="Comma-separated tags")
    external_reference = Column(String(200), nullable=True, comment="External system reference")
    
    # Verification
    is_verified = Column(Integer, default=0, comment="0=unverified, 1=verified")
    verified_by = Column(String(200), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    data_quality_scores = relationship("DataQualityScore", back_populates="emission")
    evidence_documents = relationship("EvidenceDocument", back_populates="emission", cascade="all, delete-orphan")
    user = relationship("User", back_populates="emissions", foreign_keys=[user_id])
    # organization = relationship("Organization", back_populates="emissions")  # Keep commented until Organization model exists
    
    # Indexes for performance - FIXED: Commented out the organization index
    __table_args__ = (
        Index('idx_emissions_user_scope', 'user_id', 'scope'),
        # Index('idx_emissions_org_scope', 'organization_id', 'scope'),  # Commented out since organization_id doesn't exist
        Index('idx_emissions_created_at', 'created_at'),
        Index('idx_emissions_reporting_period', 'reporting_period_start', 'reporting_period_end'),
    )
    
    def __repr__(self):
        return f"<Emission(id={self.id}, scope={self.scope.value}, category={self.category}, amount={self.amount})>"
    
    @property
    def scope_name(self) -> str:
        """Get human-readable scope name"""
        return f"Scope {self.scope.value}"
    
    @property
    def is_scope3(self) -> bool:
        """Check if this is a Scope 3 emission"""
        return self.scope == EmissionScope.SCOPE_3
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'scope': self.scope.value,
            'category': self.category,
            'subcategory': self.subcategory,
            'activity_data': self.activity_data,
            'unit': self.unit,
            'emission_factor': self.emission_factor,
            'amount': self.amount,
            'data_source': self.data_source.value if self.data_source else None,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

# Optional: Additional models for emission factors

# class EmissionFactor(Base):
#     """
#     Emission factors database
#     
#     Stores emission factors for different activities, regions, and time periods
#     """
#     __tablename__ = "emission_factors"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     
#     # Factor identification
#     activity_type = Column(String(100), nullable=False, index=True)
#     category = Column(String(100), nullable=False)
#     subcategory = Column(String(100), nullable=True)
#     
#     # Factor value
#     factor_value = Column(Float, nullable=False, comment="Emission factor value")
#     factor_unit = Column(String(50), nullable=False, comment="e.g., kgCO2e/kWh")
#     
#     # Geographic scope
#     region = Column(String(100), nullable=True, default="Global")
#     country_code = Column(String(2), nullable=True)
#     
#     # Temporal validity
#     valid_from = Column(DateTime, nullable=True)
#     valid_to = Column(DateTime, nullable=True)
#     
#     # Source and quality
#     source = Column(String(200), nullable=False, comment="Source of the factor")
#     source_year = Column(Integer, nullable=True)
#     quality_tier = Column(Integer, nullable=True, comment="1=Best, 5=Worst")
#     
#     # GWP version
#     gwp_version = Column(String(20), nullable=True, default="AR6")
#     
#     # Metadata
#     description = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
#     
#     __table_args__ = (
#         Index('idx_factor_activity_region', 'activity_type', 'region'),
#         Index('idx_factor_category', 'category'),
#     )