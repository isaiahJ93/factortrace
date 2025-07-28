# app/models/data_quality.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy import String, DateTime, Float, ForeignKey, JSON
from app.core.database import Base
from datetime import datetime

class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    
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
