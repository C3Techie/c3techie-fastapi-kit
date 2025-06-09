from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, func, desc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.shared.models.admin import Admin
from app.domains.shared.schemas.admin import AdminCreate, AdminUpdate
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

class AdminCRUD:
    """CRUD operations for Admin model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @db_operation
    async def create(self, admin_data: AdminCreate) -> Admin:
        db_admin = Admin(
            user_id=admin_data.user_id,
            role=admin_data.role,
            permissions=admin_data.permissions,
            notes=admin_data.notes,
            assigned_at=datetime.now(timezone.utc),
        )
        self.db.add(db_admin)
        await self.db.commit()
        await self.db.refresh(db_admin)
        logger.info("Created admin for user_id %s", admin_data.user_id)
        return db_admin

    @db_operation
    async def get_by_id(self, admin_id: UUID) -> Optional[Admin]:
        result = await self.db.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalars().first()

    @db_operation
    async def get_by_user_id(self, user_id: UUID) -> Optional[Admin]:
        result = await self.db.execute(
            select(Admin).where(Admin.user_id == user_id)
        )
        return result.scalars().first()

    @db_operation
    async def update(self, admin_id: UUID, admin_data: AdminUpdate) -> Admin:
        existing_admin = await self.get_by_id(admin_id)
        if not existing_admin:
            raise NotFoundError("Admin not found")

        update_values = admin_data.model_dump(exclude_unset=True)
        update_values["updated_at"] = func.now()

        await self.db.execute(
            update(Admin)
            .where(Admin.id == admin_id)
            .values(**update_values)
        )
        await self.db.commit()
        logger.info("Updated admin %s", admin_id)
        return await self.get_by_id(admin_id)

    @db_operation
    async def delete(self, admin_id: UUID) -> bool:
        result = await self.db.execute(
            delete(Admin).where(Admin.id == admin_id)
        )
        await self.db.commit()
        if result.rowcount > 0:
            logger.info("Deleted admin %s", admin_id)
        return result.rowcount > 0

    @db_operation
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "assigned_at",
        sort_desc: bool = True
    ) -> Tuple[List[Admin], int]:
        query = select(Admin)
        count_query = select(func.count(Admin.id))

        if role:
            query = query.where(Admin.role == role)
            count_query = count_query.where(Admin.role == role)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(func.lower(Admin.notes).like(search_term))
            count_query = count_query.where(func.lower(Admin.notes).like(search_term))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(Admin, sort_by, Admin.assigned_at)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        admins = result.scalars().all()

        logger.info("Listed %d admins (total: %d)", len(admins), total)
        return admins, total
