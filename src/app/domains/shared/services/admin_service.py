from uuid import UUID
from typing import Optional, List, Tuple
from app.domains.shared.crud.admin import AdminCRUD
from app.domains.shared.schemas.admin import AdminCreate, AdminUpdate, AdminRead
from app.domains.shared.models.admin import Admin
from app.core.exceptions import NotFoundError, PermissionError
from app.core.permissions import is_superadmin

class AdminService:
    def __init__(self, admin_crud: AdminCRUD):
        self.admin_crud = admin_crud

    async def create_admin(self, admin_data: AdminCreate, acting_admin: Admin) -> Admin:
        if admin_data.role == "superadmin" and not is_superadmin(acting_admin):
            raise PermissionError("Only superadmins can create other superadmins.")
        existing_admin = await self.admin_crud.get_by_user_id(admin_data.user_id)
        if existing_admin:
            raise PermissionError("User is already an admin.")
        return await self.admin_crud.create(admin_data)

    async def update_admin(self, admin_id: UUID, admin_data: AdminUpdate, acting_admin: Admin) -> Admin:
        admin = await self.admin_crud.get_by_id(admin_id)
        if not admin:
            raise NotFoundError("Admin not found")
        # Only superadmins can update admins
        if not is_superadmin(acting_admin):
            raise PermissionError("Only superadmins can update admins.")
        # Superadmins can only update themselves if target is superadmin
        if admin.role == "superadmin" and acting_admin.id != admin.id:
            raise PermissionError("Superadmins can only update themselves, not other superadmins.")
        return await self.admin_crud.update(admin_id, admin_data)

    async def get_admin(self, admin_id: UUID, acting_admin: Admin) -> Optional[Admin]:
        admin = await self.admin_crud.get_by_id(admin_id)
        if not admin:
            return None
        # Prevent regular admins from viewing superadmins
        if admin.role == "superadmin" and not is_superadmin(acting_admin):
            raise PermissionError("You are not allowed to view this admin.")
        return admin

    async def get_admin_by_user_id(self, user_id: UUID) -> Optional[Admin]:
        return await self.admin_crud.get_by_user_id(user_id)

    async def delete_admin(self, admin_id: UUID, acting_admin: Admin) -> bool:
        if not is_superadmin(acting_admin):
            raise PermissionError("Only superadmins can delete admins.")
        admin = await self.admin_crud.get_by_id(admin_id)
        if not admin:
            raise NotFoundError("Admin not found")
        if is_superadmin(admin) and acting_admin.id != admin.id:
            raise PermissionError("Superadmins can only delete themselves.")
        return await self.admin_crud.delete(admin_id)

    async def list_admins(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "assigned_at",
        sort_desc: bool = True,
        acting_admin: Optional[Admin] = None,
    ) -> Tuple[List[Admin], int]:
        admins, total = await self.admin_crud.list(
            skip=skip,
            limit=limit,
            role=role,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )
        if acting_admin and not is_superadmin(acting_admin):
            admins = [a for a in admins if a.role != "superadmin"]
            total = len(admins)
        return admins, total