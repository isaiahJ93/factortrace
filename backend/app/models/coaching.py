# app/models/coaching.py
"""
Coaching Layer Models - Multi-tenant enabled.

Provides supplier readiness assessment and improvement tracking
for ESG regimes (CSRD, CBAM, EUDR, ISSB).

Security: All coaching queries MUST be filtered by tenant_id.
Ethics: This module follows the non-punitive design principles
from docs/product/ethics-incentives.md.

See docs/features/coaching-layer.md for specification.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class ReadinessBand(str, enum.Enum):
    """
    Supplier readiness maturity bands.

    Ethics Note: We use bands instead of numerical scores (0-100) to
    avoid gamification and shame. Each band represents a stage in the
    journey, not a judgment.
    """
    FOUNDATIONAL = "foundational"  # Started but significant gaps
    EMERGING = "emerging"          # Basic compliance, room to improve
    ADVANCED = "advanced"          # High coverage, specific methodology
    LEADER = "leader"              # Best-in-class, primary data usage


class DimensionType(str, enum.Enum):
    """Assessment dimensions for readiness evaluation."""
    DATA_COVERAGE = "data_coverage"
    METHODOLOGY = "methodology_quality"
    GOVERNANCE = "governance_maturity"
    AUDIT = "audit_trail_strength"


class ActionStatus(str, enum.Enum):
    """Status of improvement actions."""
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class ProgressTrend(str, enum.Enum):
    """Trend indicator for supplier progress."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class EffortLevel(str, enum.Enum):
    """Effort required for an improvement action."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImpactLevel(str, enum.Enum):
    """Impact of completing an improvement action."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# DATABASE MODELS
# =============================================================================

class SupplierReadiness(Base):
    """
    Supplier readiness assessment snapshot.

    Records point-in-time assessment of supplier maturity for a regime.
    Each assessment captures dimension scores and recommended actions.

    Security: All queries MUST be filtered by tenant_id.
    Ethics: score_raw is INTERNAL ONLY - never expose in API responses.
    """
    __tablename__ = "supplier_readiness"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Assessment context
    regime = Column(String(20), nullable=False, index=True)  # csrd, cbam, eudr, issb

    # Overall assessment
    overall_band = Column(SQLEnum(ReadinessBand), nullable=False)
    previous_band = Column(SQLEnum(ReadinessBand), nullable=True)
    progress_trend = Column(SQLEnum(ProgressTrend), default=ProgressTrend.STABLE)

    # Dimension scores (JSON array of DimensionScore objects)
    # Each entry: {dimension, band, score_raw (internal), rationale}
    dimension_scores = Column(JSON, nullable=False, default=list)

    # Recommended improvement actions (JSON array)
    # Each entry: {id, regime, dimension, title, description, effort, impact, suggested_role}
    improvement_actions = Column(JSON, nullable=False, default=list)

    # Metadata
    methodology_version = Column(String(20), nullable=True)  # e.g., "1.0"
    confidence_level = Column(String(20), default="medium")  # low, medium, high

    # Timestamps
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="supplier_readiness_assessments")

    # Indexes for performance
    __table_args__ = (
        Index('idx_readiness_tenant_regime', 'tenant_id', 'regime'),
        Index('idx_readiness_tenant_assessed', 'tenant_id', 'assessed_at'),
        Index('idx_readiness_regime_band', 'regime', 'overall_band'),
    )


class CoachingAcknowledgment(Base):
    """
    Tracks supplier progress on improvement actions.

    When a supplier starts, completes, or dismisses an action,
    we record it here for progress tracking.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "coaching_acknowledgments"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Action reference
    action_id = Column(String(100), nullable=False, index=True)
    regime = Column(String(20), nullable=False)

    # Status tracking
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.PENDING)

    # Progress timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Optional notes from supplier
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")

    # Indexes for performance
    __table_args__ = (
        Index('idx_ack_tenant_action', 'tenant_id', 'action_id'),
        Index('idx_ack_tenant_regime', 'tenant_id', 'regime'),
        Index('idx_ack_status', 'tenant_id', 'status'),
    )


# =============================================================================
# PYDANTIC SCHEMAS (for API responses)
# =============================================================================
# Note: These are here for reference but should be moved to app/schemas/coaching.py

"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class DimensionScore(BaseModel):
    '''Score for a single assessment dimension.'''
    dimension: DimensionType
    band: ReadinessBand
    # NOTE: score_raw is INTERNAL ONLY - never included in API responses
    rationale: str = Field(..., min_length=10, description="REQUIRED: Explain WHY this band")


class ImprovementAction(BaseModel):
    '''A specific improvement action for the supplier.'''
    id: str
    regime: str
    dimension: DimensionType
    title: str
    description: str
    effort: EffortLevel
    impact: ImpactLevel
    suggested_role: str
    prerequisites: List[str] = []


class SupplierReadinessResponse(BaseModel):
    '''API response for readiness assessment - Ethics Charter compliant.'''
    id: str
    tenant_id: str
    regime: str
    overall_band: ReadinessBand
    dimension_scores: List[DimensionScore]
    improvement_actions: List[ImprovementAction]  # REQUIRED per Ethics Charter
    assessed_at: datetime
    previous_band: Optional[ReadinessBand] = None
    progress_trend: ProgressTrend
    methodology_version: Optional[str] = None
    confidence_level: str = "medium"


class CoachingPassport(BaseModel):
    '''Multi-regime readiness summary for supplier profile.'''
    tenant_id: str
    regimes: List[dict]  # {regime, band, trend}
    overall_maturity: ReadinessBand
    last_assessed: datetime
"""


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ReadinessBand",
    "DimensionType",
    "ActionStatus",
    "ProgressTrend",
    "EffortLevel",
    "ImpactLevel",
    # Database models
    "SupplierReadiness",
    "CoachingAcknowledgment",
]
