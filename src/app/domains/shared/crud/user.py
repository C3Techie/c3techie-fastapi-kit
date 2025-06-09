from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import Select

from app.domains.shared.models.user import User
from app.domains.shared.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import DatabaseError, ConflictError, NotFoundError
from app.utils.logging import get_logger

logger = get_logger(__name__)

def db_operation(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"{func.__name__} failed: {e}")
            raise DatabaseError(f"{func.__name__} failed: {str(e)}") from e
    return wrapper

class UserCRUD:
    """Complete CRUD operations for User model with advanced query support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_relationship_options(self):
        """Helper method for relationship loading."""
        return [
            selectinload(User.student_profile),
            selectinload(User.admin_profile),
            selectinload(User.audit_logs),
        ]

    async def _execute_query(self, query: Select) -> Optional[User]:
        """Internal method to execute queries with error handling."""
        try:
            result = await self.db.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error("Query execution failed: %s", e)
            raise DatabaseError(f"Database operation failed: {str(e)}")

    async def _execute_list_query(self, query: Select) -> List[User]:
        """Internal method to execute list queries with error handling."""
        try:
            result = await self.db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error("List query execution failed: %s", e)
            raise DatabaseError(f"Database operation failed: {str(e)}")

    async def get_by_id(
        self,
        user_id: UUID,
        include_relationships: bool = False
    ) -> Optional[User]:
        """Retrieve user by ID."""
        query = select(User).where(User.id == user_id)

        if include_relationships:
            query = query.options(*self._get_relationship_options())

        return await self._execute_query(query)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Case-insensitive email search."""
        return await self._execute_query(
            select(User).where(func.lower(User.email) == email.lower())
        )

    async def get_by_username(self, username: str) -> Optional[User]:
        """Exact username match."""
        return await self._execute_query(
            select(User).where(func.lower(User.username) == username.lower())
        )

    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Find user by phone number."""
        return await self._execute_query(
            select(User).where(User.phone_number == phone_number)
        )

    async def _check_uniqueness(
        self,
        *,
        email: Optional[str] = None,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
        exclude_user_id: Optional[UUID] = None
    ) -> None:
        """Raise ConflictError if email/username/phone_number is already used by another user."""
        checks = [
            ("Email", email, func.lower(User.email) == email.lower() if email else None),
            ("Username", username, func.lower(User.username) == username.lower() if username else None),
            ("Phone number", phone_number, User.phone_number == phone_number if phone_number else None),
        ]

        for field_name, value, condition in checks:
            if value and condition is not None:
                query = select(User).where(condition)
                if exclude_user_id:
                    query = query.where(User.id != exclude_user_id)
                existing = await self._execute_query(query)
                if existing:
                    raise ConflictError(f"{field_name} already registered")

    def _normalize_user_input(self, data: dict) -> dict:
        if 'email' in data and data['email']:
            data['email'] = data['email'].lower()
        if 'username' in data and data['username']:
            data['username'] = data['username'].lower()
        if 'profile_image_url' in data and data['profile_image_url']:
            data['profile_image_url'] = str(data['profile_image_url'])
        return data

    @db_operation
    async def create(self, user_data: UserCreate) -> User:
        """Create new user with conflict checks."""
        await self._check_uniqueness(
            email=user_data.email,
            username=user_data.username,
            phone_number=user_data.phone_number,
        )

        db_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number,
            profile_image_url=str(user_data.profile_image_url) if user_data.profile_image_url else None,
            is_active=True,
            email_verified=False,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        logger.info("Created user %s", db_user.username)
        return db_user

    @db_operation
    async def update(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Partially update user data."""
        existing_user = await self.get_by_id(user_id)
        if not existing_user:
            raise NotFoundError("User not found")

        update_values = user_data.model_dump(exclude_unset=True)
        update_values = self._normalize_user_input(update_values)

        await self._check_uniqueness(
            email=update_values.get("email"),
            username=update_values.get("username"),
            phone_number=update_values.get("phone_number"),
            exclude_user_id=user_id,
        )

        if "password" in update_values:
            update_values["password"] = get_password_hash(update_values["password"])

        update_values["updated_at"] = func.now()

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_values)
        )
        await self.db.commit()

        logger.info("Updated user %s", user_id)
        return await self.get_by_id(user_id)  # type: ignore

    @db_operation
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        result = await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        await self.db.commit()
        if result.rowcount > 0:
            logger.info("Deleted user %s", user_id)
        return result.rowcount > 0

    @db_operation
    async def authenticate(self, identifier: str, password: str) -> Optional[User]:
        """Authenticate user by username/email and password."""
        user = await self.get_by_username(identifier) or await self.get_by_email(identifier)

        if not user or not user.is_active:
            logger.warning("Authentication failed: user not found or inactive for %s", identifier)
            return None

        if not verify_password(password, user.password):
            logger.warning("Authentication failed: invalid password for %s", identifier)
            return None

        logger.info("User %s authenticated successfully", identifier)
        return user

    @db_operation
    async def update_last_login(self, user_id: UUID) -> None:
        """Update last login timestamp efficiently."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=func.now())
        )
        await self.db.commit()
        logger.info("Updated last login for user %s", user_id)

    @db_operation
    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """Change user password with current password verification."""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if not verify_password(current_password, user.password):
            logger.warning("Password change failed: invalid current password for user %s", user_id)
            return False

        new_password_hash = get_password_hash(new_password)

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password=new_password_hash, updated_at=func.now())
        )
        await self.db.commit()

        logger.info("Password changed successfully for user %s", user_id)
        return True

    @db_operation
    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        email_verified: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> Tuple[List[User], int]:
        """List users with pagination, filtering, and search."""
        query = select(User)
        count_query = select(func.count(User.id))

        filters = []
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if email_verified is not None:
            filters.append(User.email_verified == email_verified)

        if search:
            search_term = f"%{search.lower()}%"
            filters.append(
                or_(
                    func.lower(User.username).contains(search_term),
                    func.lower(User.email).contains(search_term),
                    User.phone_number.contains(search) if search.replace('+', '').replace('-', '').replace(' ', '').isdigit() else False
                )
            )

        if filters:
            filter_condition = and_(*filters)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(User, sort_by, User.created_at)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        query = query.offset(skip).limit(limit)

        users = await self._execute_list_query(query)

        logger.info("Listed %d users (total: %d)", len(users), total)
        return users, total

    @db_operation
    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete user by setting is_active to False."""
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await self.db.commit()
        if result.rowcount > 0:
            logger.info("Soft deleted user %s", user_id)
        return result.rowcount > 0
