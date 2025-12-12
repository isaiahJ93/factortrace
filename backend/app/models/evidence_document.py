# app/models/evidence_document.py
"""Evidence document model - Multi-tenant enabled.

Security: All evidence queries MUST be filtered by tenant_id.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class EvidenceDocument(Base):
    """
    Evidence document supporting an emission entry.

    Security: All evidence queries MUST be filtered by tenant_id.
    """
    __tablename__ = "evidence_documents"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

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

    # Indexes for performance - tenant_id first for multi-tenant queries
    __table_args__ = (
        Index('idx_evidence_tenant_emission', 'tenant_id', 'emission_id'),
    )