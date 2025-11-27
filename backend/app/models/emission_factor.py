"""
EmissionFactor Model - Production Database Architecture

Robust schema supporting:
- Multi-country factors with GLOBAL fallback
- Activity-based lookups (scope, category, activity_type, country_code)
- Year versioning for regulatory updates
- Method differentiation (location_based, market_based, average_data)
- Regulation tracking (GHG_PROTOCOL, ESRS, CDP, etc.)
- Validity periods for temporal accuracy
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    Index, ForeignKey, Numeric, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class EmissionFactor(Base):
    """
    Emission Factor Model - Production Database Architecture

    Stores emission factors with support for:
    - Multi-country factors with GLOBAL fallback
    - Activity-based lookups (scope, category, activity_type, country_code)
    - Year versioning for regulatory updates
    - Method differentiation (location_based, market_based, average_data)
    - Regulation compliance tracking
    """
    __tablename__ = "emission_factors"
    __table_args__ = (
        # Unique constraint for factor lookups (includes method for differentiation)
        UniqueConstraint(
            'scope', 'category', 'activity_type', 'country_code', 'year', 'method',
            name='uq_emission_factor_lookup'
        ),
        # Indexes for common queries
        Index('idx_factor_scope', 'scope'),
        Index('idx_factor_category', 'category'),
        Index('idx_factor_activity_type', 'activity_type'),
        Index('idx_factor_country_code', 'country_code'),
        Index('idx_factor_lookup', 'scope', 'category', 'activity_type', 'country_code'),
        {'extend_existing': True}
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Core lookup fields
    scope = Column(String(20), nullable=False, index=True)  # SCOPE_1, SCOPE_2, SCOPE_3
    category = Column(String(100), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    country_code = Column(String(10), nullable=False, index=True, default='GLOBAL')
    year = Column(Integer, nullable=False, default=2024)

    # Factor value and unit
    factor = Column(Float, nullable=False)  # kgCO2e per unit
    unit = Column(String(50), nullable=False)

    # Source metadata
    source = Column(String(255), nullable=True)

    # NEW: Regulatory fields
    method = Column(String(50), nullable=True, default='average_data')  # location_based, market_based, average_data
    regulation = Column(String(50), nullable=True, default='GHG_PROTOCOL')  # GHG_PROTOCOL, ESRS, CDP, SBTi
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<EmissionFactor("
            f"scope='{self.scope}', "
            f"category='{self.category}', "
            f"activity_type='{self.activity_type}', "
            f"country_code='{self.country_code}', "
            f"factor={self.factor})>"
        )

    @property
    def is_valid(self) -> bool:
        """Check if the factor is currently valid based on validity period."""
        now = datetime.utcnow()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True
