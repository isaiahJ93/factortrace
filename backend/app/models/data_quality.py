# app/models/data_quality.py
"""Data quality score model - Multi-tenant enabled.

Security: All data quality queries MUST be filtered by tenant_id.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DataQualityScore(Base):
    """
    Data quality assessment for an emission entry.

    Security: All data quality queries MUST be filtered by tenant_id.
    """
    __tablename__ = "data_quality_scores"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Reference to emission
    emission_id = Column(Integer, ForeignKey("emissions.id"))

    # Quality metrics
    completeness_score = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    timeliness_score = Column(Float, default=0.0)

    # Overall score
    overall_score = Column(Float, default=0.0)

    # Details
    assessment_details = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    emission = relationship("Emission", back_populates="data_quality_scores")

    # Indexes for performance - tenant_id first for multi-tenant queries
    __table_args__ = (
        Index('idx_dq_tenant_emission', 'tenant_id', 'emission_id'),
    )
