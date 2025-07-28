from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy import String, DateTime, Float, Text, ForeignKey
from datetime import datetime

from app.db.base import Base

class EvidenceDocument(Base):
    __tablename__ = "evidence_documents"

    id = Column(Integer, primary_key=True, index=True)
    emission_id = Column(Integer, ForeignKey("emissions.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    evidence_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    emission = relationship("Emission", back_populates="evidence_documents")