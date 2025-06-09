# users.py - User management API endpoints for FastAPI v1
# Handles user registration, listing, retrieval, update, password change, activity summary, and deletion.

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import Optional
from uuid import UUID
from app.domains.shared.schemas.user import (
    UserCreate, UserRead, UserUpdate, UserList, UserPasswordChange
)
from app.domains.shared.crud.user import UserCRUD
from app.domains.shared.crud.audit_log import AuditLogCRUD
from app.domains.shared.services.user_service import UserService
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.rate_limiter import RateLimiter
from app.utils.logging import get_logger


logger = get_logger(__name__)


router = APIRouter(tags=["users"])


# Dependency to get the user service
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    user_crud = UserCRUD(db)
    audit_crud = AuditLogCRUD(db)
    return UserService(user_crud, audit_crud)


# --- User Registration ---
@router.post(
    "/", 
    response_model=UserRead, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=3, seconds=60))]
)
async def register_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user and send email verification.
    """
    user = await user_service.create_user(user_in)
    background_tasks.add_task(user_service.send_email_verification, user)
    return UserRead.model_validate(user)


# --- List Users (with pagination and filters) ---
@router.get("/", response_model=UserList)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    email_verified: Optional[bool] = None,
    search: Optional[str] = None,
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
):
    """
    List users with pagination and optional filters.
    """
    skip = (page - 1) * per_page
    users, total = await user_service.list_users(
        skip=skip,
        limit=per_page,
        is_active=is_active,
        email_verified=email_verified,
        search=search,
        acting_user=current_user,
    )
    has_next = skip + per_page < total
    has_prev = page > 1
    return UserList(
        users=[UserRead.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev,
    )


# --- Get User by ID ---
@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a user by their unique ID.
    """
    user = await user_service.get_user(user_id, acting_user=current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)

# --- Update User ---
@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
):
    """
    Update user information.
    """
    updated_user = await user_service.update_user(user_id, user_update, updated_by=current_user.id, acting_user=current_user)
    return UserRead.model_validate(updated_user)


# --- Change User Password ---
@router.post("/{user_id}/change-password", response_model=bool)
async def change_password(
    user_id: UUID,
    password_data: UserPasswordChange,
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
):
    """
    Change the password for a user.
    """
    success = await user_service.change_password(user_id, password_data, acting_user=current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Password change failed")
    return True


# --- User Activity Summary ---
@router.get("/{user_id}/activity-summary")
async def user_activity_summary(
    user_id: UUID,
    days_back: int = Query(30, ge=1, le=365),
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
):
    """
    Get a summary of user activity for a given period.
    """
    return await user_service.get_user_activity_summary(user_id, days_back=days_back, acting_user=current_user)


# --- Delete User ---
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    soft: bool = Query(True, description="Soft delete if True, hard delete if False"),
    user_service: UserService = Depends(get_user_service),
    current_user=Depends(get_current_user),
):
    """
    Delete a user by their unique ID. Soft delete by default.
    """
    if soft:
        deleted = await user_service.soft_delete_user(user_id, deleted_by=current_user.id, acting_user=current_user)
    else:
        deleted = await user_service.delete_user(user_id, acting_user=current_user)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None
