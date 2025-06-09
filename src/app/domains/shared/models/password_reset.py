from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from app.domains.shared.models.base import DomainBase

if TYPE_CHECKING:
    from app.domains.shared.models.user import User

class PasswordReset(DomainBase):
    """Model for password reset tokens and requests."""
    __tablename__ = "password_resets"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped["User"] = relationship("User", back_populates="password_resets")

    __table_args__ = (
        Index('idx_password_reset_user', 'user_id'),
        Index('idx_password_reset_token', 'token'),
        Index('idx_password_reset_expires', 'expires_at'),
    )

    def __repr__(self) -> str:
        return f"<PasswordReset(id={self.id}, user_id={self.user_id}, used={self.used})>"
