from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from typing import Optional
from datetime import datetime, timezone
from app.domains.shared.models.base import DomainBase


class Admin(DomainBase):
    """Admin model representing privileged users with administrative capabilities."""
    __tablename__ = "admins"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    permissions: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship to User
    user = relationship("User", backref="admin", uselist=False)

    __table_args__ = (
        Index('idx_admin_user_id_active', 'user_id', 'is_active'),
        Index('idx_admin_assigned_at', 'assigned_at'),
    )

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, user_id={self.user_id}, role={self.role})>"
