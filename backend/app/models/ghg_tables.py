"""
GHG Protocol Database Models
SQLAlchemy models for persisting GHG data
"""
from typing import Optional
import os
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Enum, Boolean, Index, Text
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Table, Text, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base
from app.schemas.ghg_schemas import Scope3Category


class GHGReportingPeriod(Base):
    """Reporting periods for GHG data"""
    __tablename__ = "ghg_reporting_periods"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    name = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)
    organization_id = Column(String(36))
class GHGOrganization(Base):
    """Renamed to avoid conflict with existing Organization model"""
    __tablename__ = "ghg_organizations"
    
    __table_args__ = {"extend_existing": True}
    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    name = Column(String(255), nullable=False)
    industry = Column(String(100))
    country = Column(String(2))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationships
    calculations = relationship("GHGCalculationResult", back_populates="organization")
    inventories = relationship("GHGScope3Inventory", back_populates="organization")
class GHGEmissionFactor(Base):
    """Emission factors from various sources"""
    __tablename__ = "ghg_emission_factors"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    category = Column(String(50), nullable=False)  # Changed from Enum for SQLite compatibility
    factor_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    source = Column(String(100))
    year = Column(Integer)
    region = Column(String(100))
    uncertainty_percentage = Column(Float)
    factor_emission_metadata = Column(JSON)  # Renamed from 'metadata' to avoid reserved word
    # Indexes for performance
    __table_args__ = (
        Index('idx_category_region', 'category', 'region'),
    )
class GHGActivityData(Base):
    __tablename__ = "ghg_activity_data"
    __table_args__ = {"extend_existing": True}
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    calculation_id = Column(String(36), ForeignKey("ghg_calculation_results.id"))
    category = Column(String(50), nullable=False)  # Changed from Enum for SQLite
    activity_type = Column(String(100))
    amount = Column(Float, nullable=False)
    data_quality_score = Column(Float)
    calculation = relationship("GHGCalculationResult", back_populates="activity_data")
class GHGCalculationResult(Base):
    __tablename__ = "ghg_calculation_results"
    __table_args__ = {"extend_existing": True}
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    total_emissions = Column(Float)
    calculation_method = Column(String(50))  # Changed from Enum for SQLite
    status = Column(String(50), default="pending")
    uncertainty_min = Column(Float)
    uncertainty_max = Column(Float)
    completed_at = Column(DateTime)
    organization = relationship("GHGOrganization", back_populates="calculations")
    activity_data = relationship("GHGActivityData", back_populates="calculation")
    category_results = relationship("GHGCategoryResult", back_populates="calculation")
class GHGCategoryResult(Base):
    __tablename__ = "ghg_category_results"
    __table_args__ = {"extend_existing": True}
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    calculation_id = Column(String(36), ForeignKey("ghg_calculation_results.id"))
    emissions_co2e = Column(Float, nullable=False)
    calculation_details = Column(JSON)
    calculation = relationship("GHGCalculationResult", back_populates="category_results")


class GHGDataQualityScore(Base):
    """Data quality scores for GHG data"""
    __tablename__ = "ghg_data_quality_scores"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    calculation_id = Column(String(36))
    score = Column(Float)
    criteria = Column(String(255))
class GHGScope3Inventory(Base):
    __tablename__ = "ghg_scope3_inventories"
    __table_args__ = {"extend_existing": True}
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    year = Column(Integer, nullable=False)
    total_scope3_emissions = Column(Float)
    verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    organization = relationship("GHGOrganization", back_populates="inventories")
# Model aliases for backward compatibility
OrganizationDB = GHGOrganization
EmissionFactorDB = GHGEmissionFactor
ActivityDataDB = GHGActivityData
CalculationResultDB = GHGCalculationResult
Scope3InventoryDB = GHGScope3Inventory
ReportingPeriodDB = GHGReportingPeriod
DataQualityScoreDB = GHGDataQualityScore
class GHGAuditLog(Base):
    """Audit log for GHG data changes"""
    __tablename__ = "ghg_audit_logs"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("ghg_organizations.id"))
    entity_type = Column(String(100))
    entity_id = Column(String(36))
    action = Column(String(50))
    timestamp = Column(DateTime)
    user_id = Column(String(36))
    changes = Column(Text)

AuditLogDB = GHGAuditLog


