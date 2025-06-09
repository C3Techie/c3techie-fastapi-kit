from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, TYPE_CHECKING
from app.domains.shared.models.base import DomainBase
from datetime import datetime

if TYPE_CHECKING:
    from app.domains.shared.models.audit_log import AuditLog
    from app.domains.shared.models.password_reset import PasswordReset


class User(DomainBase):
    """User model representing application users with authentication capabilities."""
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    password_resets: Mapped[List["PasswordReset"]] = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_last_login', 'last_login'),
    )

    def is_authenticated(self) -> bool:
        return self.is_active and self.password is not None

    def is_eligible_for_login(self) -> bool:
        return self.is_active and self.email_verified

    def __repr__(self) -> str:
        username_display = self.username[:10] + '...' if len(self.username) > 10 else self.username
        return f"<User(id={self.id}, username={username_display})>"
