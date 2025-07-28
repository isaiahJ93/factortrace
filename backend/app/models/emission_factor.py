from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON, Numeric
from sqlalchemy import String, Boolean, DateTime, Float, Text, ForeignKey, JSON, Numeric
from app.db.base import Base
from datetime import datetime

class EmissionFactor(Base):
    __tablename__ = "emission_factors"
    __table_args__ = (
        Index('idx_factor_category_scope', 'category', 'scope'),
        Index('idx_factor_active', 'is_active'),
        Index('idx_factor_name', 'name'),  # Added for faster searches
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    scope = Column(Integer, nullable=False)
    factor = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    source = Column(String(255))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Direct uncertainty field for simple cases (added for compatibility)
    uncertainty_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Advanced uncertainty fields
    uncertainty_assessment_id = Column(Integer, ForeignKey('uncertainty_assessments.id'))
    data_quality_score = Column(Integer)  # 1-5 (1=best)
    temporal_representativeness = Column(String(50))
    geographical_representativeness = Column(String(100))
    
    # Additional metadata fields
    version = Column(String(50), default='2024.1')
    lifecycle_stage = Column(String(100))  # e.g., "cradle-to-gate", "well-to-tank"
    methodology = Column(String(255))  # Calculation methodology used
    region = Column(String(100))  # Regional specificity
    tier_level = Column(String(20))  # TIER_1, TIER_2, TIER_3
    
    # Scope 3 specific fields
    scope3_category = Column(String(50))  # e.g., "purchased_goods_services"
    calculation_method = Column(String(50))  # e.g., "spend_based", "activity_based"
    
    # Timestamps
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = Column(DateTime)  # When the factor was last verified/validated
    
    # Relationships
    uncertainty_assessment = relationship("UncertaintyAssessment", backref="emission_factors")
    history = relationship("EmissionFactorHistory", backref="factor", cascade="all, delete-orphan")
    
    @hybrid_property
    def effective_uncertainty(self):
        """Get uncertainty percentage from either direct field or assessment"""
        if self.uncertainty_percentage is not None:
            return float(self.uncertainty_percentage)
        elif self.uncertainty_assessment:
            return self.uncertainty_assessment.uncertainty_percentage
        else:
            # Default uncertainty based on tier level
            tier_defaults = {
                'TIER_1': 30.0,
                'TIER_2': 10.0,
                'TIER_3': 5.0
            }
            return tier_defaults.get(self.tier_level, 15.0)
    
    @property
    def is_valid(self):
        """Check if the factor is currently valid"""
        now = datetime.utcnow()
        return (self.is_active and 
                self.valid_from <= now and 
                (self.valid_to is None or self.valid_to > now))
    
    @property
    def quality_indicator(self):
        """Generate overall quality indicator"""
        if self.data_quality_score:
            return {
                1: "Excellent",
                2: "Good",
                3: "Fair",
                4: "Poor",
                5: "Estimate"
            }.get(self.data_quality_score, "Unknown")
        return "Not assessed"
    
    def __repr__(self):
        return f"<EmissionFactor(name='{self.name}', scope={self.scope}, factor={self.factor} {self.unit})>"


class UncertaintyAssessment(Base):
    __tablename__ = "uncertainty_assessments"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    uncertainty_percentage = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    confidence_level = Column(Float, default=95.0)
    distribution = Column(String(50), default='normal')  # normal, lognormal, triangular, uniform
    method = Column(String(100))  # monte_carlo, analytical, expert_judgment
    
    # Additional uncertainty metadata
    correlation_factors = Column(Text)  # JSON string of correlations with other factors
    sensitivity_analysis = Column(Text)  # JSON string of sensitivity results
    data_sources = Column(Text)  # JSON string of data sources used
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UncertaintyAssessment(percentage={self.uncertainty_percentage}%, distribution={self.distribution})>"


class EmissionFactorHistory(Base):
    __tablename__ = "emission_factor_history"
    __table_args__ = (
        Index('idx_history_factor_id', 'factor_id'),
        Index('idx_history_changed_at', 'changed_at'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    factor_id = Column(Integer, ForeignKey('emission_factors.id', ondelete='CASCADE'))
    field_name = Column(String(100))
    old_value = Column(String(500))
    new_value = Column(String(500))
    change_reason = Column(Text)
    regulatory_reference = Column(String(255))  # e.g., "IPCC AR6 Update"
    changed_by = Column(String(255))
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional audit fields
    change_type = Column(String(50))  # CREATE, UPDATE, DELETE, VERIFY
    approval_status = Column(String(50))  # PENDING, APPROVED, REJECTED
    approved_by = Column(String(255))
    approved_at = Column(DateTime)
    
    def __repr__(self):
        return f"<EmissionFactorHistory(factor_id={self.factor_id}, field={self.field_name}, changed_at={self.changed_at})>"


# Helper functions for working with emission factors
def get_active_factors_by_category(session, category, scope=None):
    """Get all active emission factors for a category"""
    query = session.query(EmissionFactor).filter(
        EmissionFactor.category == category,
        EmissionFactor.is_active == True
    )
    if scope is not None:
        query = query.filter(EmissionFactor.scope == scope)
    return query.all()


def get_factor_with_uncertainty(session, factor_id):
    """Get emission factor with full uncertainty information"""
    return session.query(EmissionFactor).options(
        relationship(EmissionFactor.uncertainty_assessment)
    ).filter(EmissionFactor.id == factor_id).first()


def create_factor_with_history(session, factor_data, created_by):
    """Create a new emission factor with history tracking"""
    factor = EmissionFactor(**factor_data)
    session.add(factor)
    session.flush()  # Get the ID
    
    # Create history entry
    history = EmissionFactorHistory(
        factor_id=factor.id,
        field_name="ALL",
        old_value=None,
        new_value=str(factor_data),
        change_reason="Initial creation",
        change_type="CREATE",
        changed_by=created_by
    )
    session.add(history)
    
    return factor