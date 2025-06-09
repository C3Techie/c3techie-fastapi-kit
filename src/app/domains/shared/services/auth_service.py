from typing import Optional
from uuid import UUID
from app.domains.shared.crud.user import UserCRUD
from app.domains.shared.crud.audit_log import AuditLogCRUD
from app.domains.shared.models.user import User
from app.core.exceptions import AuthenticationError
from app.domains.shared.schemas.audit_log import AuditLogCreate
from app.core.sanitizer import sanitize_email, sanitize_username
from app.utils.logging import get_logger
from app.utils.date import utcnow

logger = get_logger(__name__)


class AuthService:
    """Handles authentication and login audit logic."""

    def __init__(self, user_crud: UserCRUD, audit_crud: AuditLogCRUD):
        self.user_crud = user_crud
        self.audit_crud = audit_crud

    async def authenticate_user(
        self,
        identifier: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Authenticate user and update last login."""
        try:
            # Sanitize identifier
            if "@" in identifier:
                identifier = sanitize_email(identifier)
            else:
                identifier = sanitize_username(identifier)

            user = await self.user_crud.authenticate(identifier, password)
            if not user:
                await self.audit_crud.create(
                    AuditLogCreate(
                        user_id=None,
                        action="LOGIN_FAILED",
                        entity_type="User",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={"identifier": identifier},
                        created_at=utcnow(),
                    )
                )
                raise AuthenticationError("Invalid credentials")

            await self.user_crud.update_last_login(user.id)
            await self.user_crud.db.refresh(user)

            await self.audit_crud.create(
                AuditLogCreate(
                    user_id=user.id,
                    action="LOGIN_SUCCESS",
                    entity_id=str(user.id),
                    entity_type="User",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=utcnow(),
                )
            )
            logger.info("User authenticated successfully: %s", identifier)
            return user
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Authentication failed: %s", e)
            raise
