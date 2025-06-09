from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class AuditLogBase(BaseModel):
    """Base audit log schema with common fields."""
    user_id: Optional[UUID] = None
    action: str = Field(..., max_length=50)
    entity_type: str = Field(..., max_length=50)
    entity_id: Optional[str] = Field(None, max_length=36)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    details: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""
    pass


class AuditLogRead(AuditLogBase):
    """Schema for reading audit log entries."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """Schema for paginated audit log listing."""
    logs: List[AuditLogRead]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
