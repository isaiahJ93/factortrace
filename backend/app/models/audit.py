# app/models/audit.py
"""
SQLAlchemy model for audit logging - CSRD compliance.

Tracks all CRUD operations on tenant-owned entities for audit trail.
This is critical for regulatory compliance (no data can be silently changed).
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Audit log action types."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    RESTORE = "RESTORE"


class AuditLog(Base):
    """
    Audit log for tracking all CRUD operations.

    CSRD Compliance: Required for data integrity verification and audit trails.
    Every change to emission data must be logged with who/when/what.
    """
    __tablename__ = "audit_logs"

    # Primary key (auto-incrementing)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(String(36), nullable=False, index=True)

    # User who performed the action (nullable for system actions)
    user_id = Column(Integer, nullable=True)

    # What entity was affected
    entity_type = Column(String(50), nullable=False)  # e.g., "Emission", "EvidenceDocument"
    entity_id = Column(Integer, nullable=False)

    # What action was performed
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, RESTORE

    # What changed (JSON diff for UPDATE actions)
    # Format: {"field_name": {"old": old_value, "new": new_value}}
    changes = Column(JSON, nullable=True)

    # Request context for security analysis
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    # Timestamp (auto-set on insert)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<AuditLog({self.id}: {self.action} {self.entity_type}:{self.entity_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
