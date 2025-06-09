from typing import List

# Define permission constants
ADMIN_PERMISSIONS = [
    "manage_users",
    "view_reports",
    "edit_settings",
]

SUPERADMIN_PERMISSIONS = [
    *ADMIN_PERMISSIONS,
    "manage_admins",
    "system_settings",
]

def has_permission(admin, permission: str) -> bool:
    """
    Check if the admin has a specific permission.
    Assumes admin.permissions is a list of strings.
    """
    if not admin or not admin.permissions:
        return False
    return permission in admin.permissions

def is_superadmin(admin) -> bool:
    """
    Check if the admin is a superadmin.
    Assumes admin.role is a string.
    """
    return getattr(admin, "role", None) == "superadmin"
