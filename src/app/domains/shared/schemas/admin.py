from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.utils.validators import validate_role, validate_permissions_list


class AdminBase(BaseModel):
    """Base admin schema with common fields."""
    role: str = Field(..., description="Role of the admin, e.g., 'admin' or 'superadmin'")
    permissions: Optional[List[str]] = Field(
        None, description="List of permissions"
    )
    notes: Optional[str] = Field(
        None, description="Internal notes about the admin", max_length=255
    )

    @field_validator('role')
    @classmethod
    def validate_role_field(cls, v):
        return validate_role(v)

    @field_validator('permissions')
    @classmethod
    def validate_permissions_list_field(cls, v):
        return validate_permissions_list(v)

class AdminCreate(AdminBase):
    """Schema for creating a new admin."""
    user_id: UUID = Field(..., description="ID of the user to be made admin")

class AdminUpdate(BaseModel):
    """Schema for updating admin information."""
    role: Optional[str] = Field(None, description="Role of the admin")
    permissions: Optional[List[str]] = Field(None, description="List of permissions")
    notes: Optional[str] = Field(None, description="Notes", max_length=255)
    is_active: Optional[bool] = None
    last_active_at: Optional[datetime] = None

    @field_validator('role')
    @classmethod
    def validate_role_field(cls, v):
        if v is not None:
            return validate_role(v)
        return v

    @field_validator('permissions')
    @classmethod
    def validate_permissions_list_field(cls, v):
        return validate_permissions_list(v)

class AdminRead(AdminBase):
    """Schema for reading admin information."""
    id: UUID
    user_id: UUID
    is_active: bool
    assigned_at: datetime
    last_active_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdminList(BaseModel):
    """Schema for paginated admin listing."""
    admins: List[AdminRead]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
