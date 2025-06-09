from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional, TYPE_CHECKING
from app.domains.shared.models.base import DomainBase
import uuid

if TYPE_CHECKING:
    from app.domains.shared.models.user import User


class AuditLog(DomainBase):
    """Audit log model tracking user actions within the application."""
    __tablename__ = "audit_logs"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        """Debug-friendly representation with action truncation."""
        return f"<AuditLog(id={self.id}, action={self.action[:20]}...)>"
