from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.shared.models.audit_log import AuditLog
from app.domains.shared.schemas.audit_log import AuditLogCreate
from app.core.exceptions import DatabaseError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AuditLogCRUD:
    """CRUD operations for AuditLog model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_filters(
        self,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        user_id_filter: Optional[UUID] = None,
        days_back: Optional[int] = None,
    ) -> List[Any]:
        """Helper to build SQLAlchemy filter list."""
        filters = []
        if user_id_filter:
            filters.append(AuditLog.user_id == user_id_filter)
        if action_filter:
            filters.append(AuditLog.action == action_filter)
        if entity_type_filter:
            filters.append(AuditLog.entity_type == entity_type_filter)
        if days_back is not None:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            filters.append(AuditLog.created_at >= cutoff_date)
        return filters

    async def create(self, audit_data: AuditLogCreate) -> AuditLog:
        """Create new audit log entry."""
        try:
            db_audit = AuditLog(
                user_id=audit_data.user_id,
                action=audit_data.action,
                entity_type=audit_data.entity_type,
                entity_id=audit_data.entity_id,
                ip_address=audit_data.ip_address,
                user_agent=audit_data.user_agent,
                details=audit_data.details,
            )

            self.db.add(db_audit)
            await self.db.commit()
            await self.db.refresh(db_audit)

            logger.info("Created audit log entry for user %s: %s", audit_data.user_id, audit_data.action)
            return db_audit

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error("Audit log creation failed: %s", e)
            raise DatabaseError(f"Audit log creation failed: {str(e)}") from e

    async def get_user_logs(
        self,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        days_back: Optional[int] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs for a specific user with filtering."""
        try:
            filters = self._build_filters(
                action_filter=action_filter,
                entity_type_filter=entity_type_filter,
                user_id_filter=user_id,
                days_back=days_back,
            )
            filter_condition = and_(*filters) if filters else True

            query = select(AuditLog).where(filter_condition)
            count_query = select(func.count(AuditLog.id)).where(filter_condition)

            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
            result = await self.db.execute(query)
            logs = result.scalars().all()

            logger.info("Retrieved %d audit logs for user %s", len(logs), user_id)
            return logs, total

        except SQLAlchemyError as e:
            logger.error("User audit logs retrieval failed: %s", e)
            raise DatabaseError(f"User audit logs retrieval failed: {str(e)}") from e

    async def get_system_logs(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        user_id_filter: Optional[UUID] = None,
        days_back: Optional[int] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Get system-wide audit logs with filtering."""
        try:
            filters = self._build_filters(
                action_filter=action_filter,
                entity_type_filter=entity_type_filter,
                user_id_filter=user_id_filter,
                days_back=days_back,
            )
            filter_condition = and_(*filters) if filters else True

            query = select(AuditLog).options(selectinload(AuditLog.user)).where(filter_condition)
            count_query = select(func.count(AuditLog.id)).where(filter_condition)

            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
            result = await self.db.execute(query)
            logs = result.scalars().all()

            logger.info("Retrieved %d system audit logs", len(logs))
            return logs, total

        except SQLAlchemyError as e:
            logger.error("System audit logs retrieval failed: %s", e)
            raise DatabaseError(f"System audit logs retrieval failed: {str(e)}") from e

    async def get_action_summary(
        self,
        user_id: Optional[UUID] = None,
        days_back: int = 30,
    ) -> Dict[str, int]:
        """Get summary of actions performed within specified timeframe."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            query = (
                select(
                    AuditLog.action,
                    func.count(AuditLog.id).label("count"),
                )
                .where(AuditLog.created_at >= cutoff_date)
                .group_by(AuditLog.action)
            )

            if user_id:
                query = query.where(AuditLog.user_id == user_id)

            result = await self.db.execute(query)
            summary = {row.action: row.count for row in result.all()}

            logger.info("Generated action summary for %s days", days_back)
            return summary

        except SQLAlchemyError as e:
            logger.error("Action summary generation failed: %s", e)
            raise DatabaseError(f"Action summary generation failed: {str(e)}") from e

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Remove audit logs older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            result = await self.db.execute(
                AuditLog.__table__.delete().where(AuditLog.created_at < cutoff_date)
            )
            await self.db.commit()

            deleted_count = result.rowcount or 0
            logger.info("Cleaned up %d old audit log entries", deleted_count)

            return deleted_count

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error("Audit log cleanup failed: %s", e)
            raise DatabaseError(f"Audit log cleanup failed: {str(e)}") from e
