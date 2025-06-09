from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.domains.shared.crud.user import UserCRUD
from app.domains.shared.crud.audit_log import AuditLogCRUD
from app.domains.shared.schemas.user import UserCreate, UserUpdate, UserPasswordChange, UserRead
from app.domains.shared.schemas.audit_log import AuditLogCreate
from app.domains.shared.models.user import User
from app.domains.shared.models.admin import Admin
from app.core.exceptions import NotFoundError, AuthenticationError, PermissionError
from app.core.permissions import is_superadmin
from app.config import settings
from app.utils.email import send_verification_email
from app.utils.logging import get_logger
from app.utils.date import utcnow, add_minutes
from app.utils.cache import RedisCache
import json

from app.core.sanitizer import sanitize_email, sanitize_username, sanitize_phone
from app.domains.shared.crud.admin import AdminCRUD

logger = get_logger(__name__)


def convert_for_json(obj):
    """Recursively convert UUIDs and datetimes in dicts/lists to strings for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(i) for i in obj]
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


class UserService:
    """Business logic layer for user operations."""

    def __init__(self, user_crud: UserCRUD, audit_crud: AuditLogCRUD, cache: RedisCache = None):
        self.user_crud = user_crud
        self.audit_crud = audit_crud
        self.cache = cache or RedisCache(settings.REDIS_URL)

    async def _log_audit(
        self,
        user_id: UUID,
        action: str,
        entity_type: str = "User",
        entity_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Helper to create audit log entries."""
        await self.audit_crud.create(AuditLogCreate(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            created_at=utcnow(),
        ))

    async def create_user(
        self,
        user_data: UserCreate,
        created_by: Optional[UUID] = None,
        ip_address: Optional[str] = None,
    ) -> User:
        """Create a new user with audit logging and cache the profile."""
        try:
            # Sanitize input fields
            user_data.email = sanitize_email(user_data.email)
            user_data.username = sanitize_username(user_data.username)
            if hasattr(user_data, "phone_number") and user_data.phone_number:
                user_data.phone_number = sanitize_phone(user_data.phone_number)

            user = await self.user_crud.create(user_data)
            await self._log_audit(
                user_id=created_by or user.id,
                action="USER_CREATED",
                entity_id=str(user.id),
                ip_address=ip_address,
                details={"username": user.username, "email": user.email},
            )
            # Convert to Pydantic and cache the user profile
            user_schema = UserRead.from_orm(user)
            await self.cache.set(f"user_profile:{user.id}", user_schema.model_dump_json(), expire=600)
            logger.info("User created successfully: %s", user.username)
            return user
        except Exception:
            logger.error("User creation failed", exc_info=True)
            raise

    async def send_email_verification(self, user: User) -> None:
        """Generate email verification token and send verification email."""
        token = self._create_email_verification_token(user)
        try:
            await send_verification_email(user.email, user.username, token)
            logger.info(f"Sent verification email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")

    def _create_email_verification_token(self, user: User) -> str:
        """Create JWT token for email verification with expiry."""
        expire = add_minutes(utcnow(), 24 * 60)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": int(expire.timestamp()),
            "type": "email_verification",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return token

    async def verify_email_token(self, token: str) -> User:
        """Verify email verification token and mark user as verified."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "email_verification":
                raise AuthenticationError("Invalid token type")

            user_id = UUID(payload.get("sub"))
            user = await self.user_crud.get_by_id(user_id)
            if not user:
                raise NotFoundError("User not found")

            if user.email_verified:
                logger.info(f"User {user.email} already verified")
                return user

            await self.user_crud.update(user_id, UserUpdate(email_verified=True))
            logger.info(f"User {user.email} email verified successfully")
            return await self.user_crud.get_by_id(user_id)
        except ExpiredSignatureError:
            logger.warning("Email verification failed: token expired")
            raise AuthenticationError("Verification token expired")
        except (InvalidTokenError, Exception) as e:
            logger.warning(f"Email verification failed: {e}")
            raise AuthenticationError("Invalid verification token")

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        email_verified: Optional[bool] = None,
        search: Optional[str] = None,
        acting_user: Optional[User] = None,
    ) -> Tuple[list, int]:
        # Add permission checks if needed
        return await self.user_crud.list_users(
            skip=skip,
            limit=limit,
            is_active=is_active,
            email_verified=email_verified,
            search=search,
        )

    async def get_user(self, user_id: UUID, acting_user: Optional[User] = None) -> Optional[User]:
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            return None
        # Only allow self or superadmin to view
        if acting_user and (acting_user.id != user_id and not is_superadmin(acting_user)):
            raise PermissionError("Not allowed to view this user.")
        return user

    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        updated_by: UUID,
        acting_user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> User:
        # Only allow self or superadmin to update
        if acting_user and (acting_user.id != user_id and not is_superadmin(acting_user)):
            raise PermissionError("Not allowed to update this user.")
        return await self._update_user(user_id, user_data, updated_by, ip_address)

    async def _update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        updated_by: UUID,
        ip_address: Optional[str] = None,
    ) -> User:
        try:
            # Sanitize fields if present
            if user_data.email:
                user_data.email = sanitize_email(user_data.email)
            if user_data.username:
                user_data.username = sanitize_username(user_data.username)
            if hasattr(user_data, "phone_number") and user_data.phone_number:
                user_data.phone_number = sanitize_phone(user_data.phone_number)

            original_user = await self.user_crud.get_by_id(user_id)
            if not original_user:
                raise NotFoundError("User not found")

            updated_user = await self.user_crud.update(user_id, user_data)
            changes = user_data.model_dump(exclude_unset=True)

            await self._log_audit(
                user_id=updated_by,
                action="USER_UPDATED",
                entity_id=str(user_id),
                ip_address=ip_address,
                details={"changes": list(changes.keys())},
            )
            # Convert to Pydantic and update the cache
            user_schema = UserRead.from_orm(updated_user)
            await self.cache.set(f"user_profile:{user_id}", user_schema.model_dump_json(), expire=600)
            logger.info("User updated successfully: %s", user_id)
            return updated_user
        except Exception as e:
            logger.error("User update failed: %s", e)
            raise

    async def change_password(
        self,
        user_id: UUID,
        password_data: UserPasswordChange,
        acting_user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        # Only allow self or superadmin to change password
        if acting_user and (acting_user.id != user_id and not is_superadmin(acting_user)):
            raise PermissionError("Not allowed to change password for this user.")
        return await self._change_password(user_id, password_data, ip_address)

    async def _change_password(
        self,
        user_id: UUID,
        password_data: UserPasswordChange,
        ip_address: Optional[str] = None,
    ) -> bool:
        try:
            success = await self.user_crud.change_password(
                user_id, password_data.current_password, password_data.new_password
            )
            if success:
                await self._log_audit(
                    user_id=user_id,
                    action="PASSWORD_CHANGED",
                    entity_id=str(user_id),
                    ip_address=ip_address,
                )
                logger.info("Password changed successfully for user: %s", user_id)
            else:
                await self._log_audit(
                    user_id=user_id,
                    action="PASSWORD_CHANGE_FAILED",
                    entity_id=str(user_id),
                    ip_address=ip_address,
                    details={"reason": "Invalid current password"},
                )
                logger.warning("Password change failed for user: %s", user_id)
            return success
        except Exception as e:
            logger.error("Password change failed: %s", e)
            raise

    async def get_user_activity_summary(
        self,
        user_id: UUID,
        days_back: int = 30,
        acting_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        # Only allow self or superadmin to view activity
        if acting_user and (acting_user.id != user_id and not is_superadmin(acting_user)):
            raise PermissionError("Not allowed to view activity for this user.")
        return await self._get_user_activity_summary(user_id, days_back)

    async def _get_user_activity_summary(
        self,
        user_id: UUID,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        cache_key = f"user_activity_summary:{user_id}:{days_back}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        try:
            user = await self.user_crud.get_by_id(user_id)
            if not user:
                raise NotFoundError("User not found")

            logs, total_logs = await self.audit_crud.get_user_logs(
                user_id, days_back=days_back, limit=1000
            )
            action_summary = await self.audit_crud.get_action_summary(
                user_id=user_id, days_back=days_back
            )

            summary = {
                "user_info": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "last_login": user.last_login,
                    "created_at": user.created_at,
                },
                "activity_summary": {
                    "total_actions": total_logs,
                    "action_breakdown": action_summary,
                    "days_analyzed": days_back,
                },
                "recent_activities": [
                    {
                        "action": log.action,
                        "entity_type": log.entity_type,
                        "created_at": log.created_at,
                        "ip_address": log.ip_address,
                    }
                    for log in logs[:10]
                ],
            }
            # Convert UUIDs before caching
            await self.cache.set(cache_key, json.dumps(convert_for_json(summary)), expire=300)
            return summary
        except Exception as e:
            logger.error("User activity summary failed: %s", e)
            raise

    async def soft_delete_user(
        self,
        user_id: UUID,
        deleted_by: Optional[UUID] = None,
        acting_user: Optional[User] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        # Only allow self, admin, or superadmin to soft delete
        if acting_user and (acting_user.id != user_id and not is_superadmin(acting_user) and getattr(acting_user, "role", None) != "admin"):
            raise PermissionError("Not allowed to delete this user.")
        return await self._soft_delete_user(user_id, deleted_by, ip_address, reason)

    async def _soft_delete_user(
        self,
        user_id: UUID,
        deleted_by: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        try:
            success = await self.user_crud.soft_delete(user_id)
            if success:
                await self._log_audit(
                    user_id=deleted_by or user_id,
                    action="USER_SOFT_DELETED",
                    entity_id=str(user_id),
                    ip_address=ip_address,
                    details={"reason": reason} if reason else None,
                )
                logger.info("User soft deleted successfully: %s", user_id)
            return success
        except Exception as e:
            logger.error("User soft delete failed: %s", e)
            raise

    async def delete_user(
        self,
        user_id: UUID,
        acting_user: Optional[User] = None,
    ) -> bool:
        admin_crud = AdminCRUD(self.user_crud.db)
        admin = await admin_crud.get_by_user_id(user_id)
        # Only superadmin or self can delete admin users
        if admin:
            if not acting_user or (not is_superadmin(acting_user) and acting_user.id != user_id):
                raise PermissionError("Only superadmins or the user themselves can delete an admin user.")
        else:
            if not acting_user or (acting_user.id != user_id and not is_superadmin(acting_user) and getattr(acting_user, "role", None) != "admin"):
                raise PermissionError("Not allowed to delete this user.")
        return await self._delete_user(user_id, acting_user)

    async def _delete_user(
        self,
        user_id: UUID,
        acting_user: Optional[User] = None,
    ) -> bool:
        try:
            await self._log_audit(
                user_id=user_id,
                action="USER_HARD_DELETED",
                entity_id=str(user_id),
            )
            success = await self.user_crud.delete(user_id)
            if success:
                await self.cache.delete(f"user_profile:{user_id}")
                logger.info("User hard deleted successfully: %s", user_id)
            return success
        except Exception as e:
            logger.error("User hard delete failed: %s", e)
            raise
