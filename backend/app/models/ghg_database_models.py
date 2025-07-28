"""
Database Models for GHG Protocol Scope 3 Calculator
SQLAlchemy models with PostgreSQL and TimescaleDB support
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, List, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Text, JSON, ARRAY, Numeric, Enum as SQLEnum,
    func, text
, desc)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import expression

Base = declarative_base()


def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid4())


class TimestampMixin:
    """Mixin for created/updated timestamps"""
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )


class OrganizationDB(Base, TimestampMixin):
    """Organization entity"""
    __tablename__ = "organizations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False)
    industry_code = Column(String(20))  # NAICS/ISIC code
    reporting_year = Column(Integer, nullable=False)
    baseline_year = Column(Integer)
    target_year = Column(Integer)
    
    # Location and contact
    headquarters_country = Column(String(2))  # ISO country code
    locations = Column(ARRAY(String))
    contact_email = Column(String(255))
    
    # Compliance flags
    sbti_committed = Column(Boolean, default=False)
    sbti_validated = Column(Boolean, default=False)
    tcfd_aligned = Column(Boolean, default=False)
    
    # Metadata
    emission_metadata = Column(JSONB, default={})
    
    # Relationships
    emission_factors = relationship("EmissionFactorDB", back_populates="organization")
    activity_data = relationship("ActivityDataDB", back_populates="organization")
    calculation_results = relationship("CalculationResultDB", back_populates="organization")
    inventories = relationship("Scope3InventoryDB", back_populates="organization")
    audit_logs = relationship("AuditLogDB", back_populates="organization")
    
    __table_args__ = (
        Index("idx_org_reporting_year", "reporting_year"),
        Index("idx_org_industry", "industry"),
    )


class EmissionFactorDB(Base, TimestampMixin):
    """Emission factors with source tracking"""
    __tablename__ = "emission_factors"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Basic attributes
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # Scope3Category enum value
    value = Column(Numeric(precision=20, scale=10), nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Source information
    source = Column(String(50), nullable=False)  # EmissionFactorSource enum
    source_reference = Column(Text, nullable=False)
    source_url = Column(String(500))
    
    # Applicability
    region = Column(String(100))  # Country/region code
    year = Column(Integer, nullable=False)
    valid_from = Column(Date)
    valid_to = Column(Date)
    
    # Data quality
    uncertainty_range = Column(ARRAY(Float))  # [lower, upper] as percentages
    quality_indicator = Column(JSONB)  # Pedigree matrix scores
    tier_level = Column(Integer, CheckConstraint("tier_level BETWEEN 1 AND 3"))
    
    # Additional metadata
    emission_metadata = Column(JSONB, default={})
    tags = Column(ARRAY(String))
    
    # Audit
    is_custom = Column(Boolean, default=False)
    approved_by = Column(String(255))
    approval_date = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("OrganizationDB", back_populates="emission_factors")
    
    __table_args__ = (
        Index("idx_ef_category_region_year", "category", "region", "year"),
        Index("idx_ef_source", "source"),
        Index("idx_ef_tags", "tags", postgresql_using="gin"),
        UniqueConstraint(
            "name", "category", "source", "region", "year",
            name="uq_emission_factor"
        ),
    )
    
    @validates("value")
    def validate_value(self, key, value):
        """Ensure emission factor is positive"""
        if value <= 0:
            raise ValueError("Emission factor value must be positive")
        return value


class ActivityDataDB(Base, TimestampMixin):
    """Activity data for calculations"""
    __tablename__ = "activity_data"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Core attributes
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    
    # Quantity with unit
    quantity_value = Column(Numeric(precision=20, scale=6), nullable=False)
    quantity_unit = Column(String(50), nullable=False)
    
    # Context
    location = Column(String(100))
    time_period = Column(Date, nullable=False)
    data_source = Column(String(255), nullable=False)
    
    # Data quality
    quality_indicator = Column(JSONB, nullable=False)  # Pedigree matrix
    verification_status = Column(String(50))
    
    # Category-specific data stored in JSONB
    emission_metadata = Column(JSONB, default={})
    
    # File attachments
    supporting_documents = Column(ARRAY(String))  # URLs/paths
    
    # Relationships
    organization = relationship("OrganizationDB", back_populates="activity_data")
    
    __table_args__ = (
        Index("idx_ad_org_category", "organization_id", "category"),
        Index("idx_ad_time_period", "time_period"),
        Index("idx_ad_metadata", "emission_metadata", postgresql_using="gin"),
    )


class CalculationResultDB(Base, TimestampMixin):
    """Calculation results with full audit trail"""
    __tablename__ = "calculation_results"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Calculation metadata
    category = Column(String(50), nullable=False)
    calculation_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    reporting_period = Column(Date, nullable=False)
    methodology = Column(String(50), nullable=False)
    
    # Results
    emissions_value = Column(Numeric(precision=20, scale=6), nullable=False)
    emissions_lower = Column(Numeric(precision=20, scale=6))  # Uncertainty bound
    emissions_upper = Column(Numeric(precision=20, scale=6))  # Uncertainty bound
    emissions_unit = Column(String(20), default="kgCO2e")
    
    # Quality metrics
    activity_data_count = Column(Integer, nullable=False)
    data_quality_score = Column(Float, nullable=False)
    completeness_score = Column(Float)
    
    # Detailed breakdowns
    emissions_by_source = Column(JSONB)
    emissions_by_region = Column(JSONB)
    emissions_by_time = Column(JSONB)
    
    # Calculation details
    calculation_parameters = Column(JSONB, nullable=False)
    emission_factors_used = Column(ARRAY(String))  # UUIDs
    activity_data_used = Column(ARRAY(String))  # UUIDs
    
    # Documentation
    assumptions = Column(ARRAY(Text))
    exclusions = Column(ARRAY(Text))
    notes = Column(Text)
    
    # Validation
    validated = Column(Boolean, default=False)
    validation_errors = Column(ARRAY(Text))
    reviewer = Column(String(255))
    review_date = Column(DateTime(timezone=True))
    
    # Version control
    version = Column(Integer, default=1)
    supersedes_id = Column(PGUUID(as_uuid=True), ForeignKey("calculation_results.id"))
    
    # Relationships
    organization = relationship("OrganizationDB", back_populates="calculation_results")
    supersedes = relationship("CalculationResultDB", remote_side=[id])
    
    __table_args__ = (
        Index("idx_cr_org_category_period", "organization_id", "category", "reporting_period"),
        Index("idx_cr_calculation_date", "calculation_date"),
        CheckConstraint("emissions_value >= 0", name="ck_emissions_positive"),
        CheckConstraint(
            "emissions_lower IS NULL OR emissions_lower <= emissions_value",
            name="ck_lower_bound"
        ),
        CheckConstraint(
            "emissions_upper IS NULL OR emissions_upper >= emissions_value",
            name="ck_upper_bound"
        ),
    )


class Scope3InventoryDB(Base, TimestampMixin):
    """Complete Scope 3 inventory"""
    __tablename__ = "scope3_inventories"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Inventory metadata
    reporting_year = Column(Integer, nullable=False)
    calculation_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    status = Column(String(50), default="draft")  # draft, submitted, verified
    
    # Aggregate results
    total_emissions = Column(Numeric(precision=20, scale=6), nullable=False)
    total_emissions_lower = Column(Numeric(precision=20, scale=6))
    total_emissions_upper = Column(Numeric(precision=20, scale=6))
    
    # Category totals (JSONB for flexibility)
    emissions_by_category = Column(JSONB, nullable=False)
    
    # Completeness and quality
    categories_calculated = Column(ARRAY(String))
    completeness_percentage = Column(Float)
    average_data_quality = Column(Float)
    
    # Documentation
    executive_summary = Column(Text)
    key_findings = Column(ARRAY(Text))
    improvement_opportunities = Column(ARRAY(Text))
    
    # Compliance
    ghg_protocol_compliant = Column(Boolean, default=True)
    iso_14064_compliant = Column(Boolean, default=True)
    third_party_verified = Column(Boolean, default=False)
    verification_statement_url = Column(String(500))
    verifier_name = Column(String(255))
    verification_date = Column(Date)
    
    # Links to calculations
    calculation_result_ids = Column(ARRAY(String))  # UUIDs of CategoryCalculationResults
    
    # Relationships
    organization = relationship("OrganizationDB", back_populates="inventories")
    
    __table_args__ = (
        Index("idx_inventory_org_year", "organization_id", "reporting_year"),
        Index("idx_inventory_status", "status"),
        UniqueConstraint(
            "organization_id", "reporting_year", "status",
            name="uq_org_year_status"
        ),
    )


class AuditLogDB(Base):
    """Immutable audit log for all changes"""
    __tablename__ = "audit_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )
    
    # Context
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user = Column(String(255), nullable=False)
    user_email = Column(String(255))
    
    # Action details
    action = Column(String(100), nullable=False)  # create, update, delete, calculate, approve
    entity_type = Column(String(50))  # activity_data, emission_factor, calculation
    entity_id = Column(PGUUID(as_uuid=True))
    category = Column(String(50))  # Scope3Category if applicable
    
    # Change tracking
    previous_value = Column(JSONB)
    new_value = Column(JSONB)
    changed_fields = Column(ARRAY(String))
    
    # Additional context
    reason = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(255))
    
    # Calculation specific
    calculation_id = Column(PGUUID(as_uuid=True))
    
    # Relationships
    organization = relationship("OrganizationDB", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_org_timestamp", "organization_id", "timestamp"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_calculation", "calculation_id"),
    )


# TimescaleDB Hypertables for time-series data
class EmissionTimeSeriesDB(Base):
    """Time-series emissions data for tracking and forecasting"""
    __tablename__ = "emission_timeseries"
    
    time = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, primary_key=True)
    category = Column(String(50), nullable=False, primary_key=True)
    
    # Measurements
    emissions_value = Column(Numeric(precision=20, scale=6), nullable=False)
    activity_level = Column(Numeric(precision=20, scale=6))
    emission_intensity = Column(Numeric(precision=20, scale=6))
    
    # Metadata
    source = Column(String(50))  # actual, estimated, target
    emission_metadata = Column(JSONB)
    
    __table_args__ = (
        Index("idx_ts_org_cat", "organization_id", "category", desc("time")),
        # This table would be converted to a TimescaleDB hypertable
        # SELECT create_hypertable('emission_timeseries', 'time');
    )


# Materialized views for performance (created via migrations)
"""
CREATE MATERIALIZED VIEW mv_category_summaries AS
SELECT 
    organization_id,
    category,
    reporting_period,
    COUNT(*) as calculation_count,
    AVG(emissions_value) as avg_emissions,
    MIN(emissions_value) as min_emissions,
    MAX(emissions_value) as max_emissions,
    AVG(data_quality_score) as avg_quality_score
FROM calculation_results
GROUP BY organization_id, category, reporting_period
WITH DATA;

CREATE INDEX idx_mv_cat_sum_org ON mv_category_summaries(organization_id);
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_category_summaries;
"""


# Database functions for complex calculations
"""
CREATE OR REPLACE FUNCTION calculate_inventory_total(org_id UUID, year INTEGER)
RETURNS TABLE(
    total_emissions NUMERIC,
    categories_included TEXT[],
    calculation_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        SUM(emissions_value) as total_emissions,
        ARRAY_AGG(DISTINCT category) as categories_included,
        MAX(calculation_date) as calculation_date
    FROM calculation_results
    WHERE organization_id = org_id
        AND EXTRACT(YEAR FROM reporting_period) = year
        AND validated = true;
END;
$$ LANGUAGE plpgsql;
"""