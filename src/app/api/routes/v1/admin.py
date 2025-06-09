from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID
from app.domains.shared.schemas.admin import (
    AdminCreate, AdminUpdate, AdminRead, AdminList
)
from app.domains.shared.services.admin_service import AdminService
from app.domains.shared.crud.admin import AdminCRUD
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_admin
from app.core.exceptions import NotFoundError, PermissionError


router = APIRouter(tags=["admins"])


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    admin_crud = AdminCRUD(db)
    return AdminService(admin_crud)


@router.post(
    "/", 
    response_model=AdminRead, 
    status_code=status.HTTP_201_CREATED
)
async def create_admin(
    admin_in: AdminCreate,
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(get_current_admin),
):
    try:
        admin = await admin_service.create_admin(admin_in, current_admin)
        return AdminRead.model_validate(admin)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/", response_model=AdminList)
async def list_admins(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(get_current_admin),
):
    skip = (page - 1) * per_page
    admins, total = await admin_service.list_admins(
        skip=skip,
        limit=per_page,
        role=role,
        search=search,
        acting_admin=current_admin,
    )
    has_next = skip + per_page < total
    has_prev = page > 1
    return AdminList(
        admins=[AdminRead.model_validate(a) for a in admins],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev,
    )


@router.get("/{admin_id}", response_model=AdminRead)
async def get_admin(
    admin_id: UUID,
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(get_current_admin),
):
    try:
        admin = await admin_service.get_admin(admin_id, current_admin)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return AdminRead.model_validate(admin)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.patch("/{admin_id}", response_model=AdminRead)
async def update_admin(
    admin_id: UUID,
    admin_update: AdminUpdate,
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(get_current_admin),
):
    try:
        updated_admin = await admin_service.update_admin(admin_id, admin_update, current_admin)
        return AdminRead.model_validate(updated_admin)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Admin not found")


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: UUID,
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(get_current_admin),
):
    try:
        deleted = await admin_service.delete_admin(admin_id, acting_admin=current_admin)
        if not deleted:
            raise HTTPException(status_code=404, detail="Admin not found")
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Admin not found")
