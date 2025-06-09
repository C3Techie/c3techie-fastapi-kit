# deps.py - Dependency utilities for FastAPI endpoints
# Provides authentication and user retrieval dependencies.

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.domains.shared.crud.user import UserCRUD
from app.domains.shared.crud.admin import AdminCRUD
from app.dependencies import get_db

bearer_scheme = HTTPBearer()


# --- Get Current Authenticated User Dependency ---
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db)
):
    """
    Retrieve the current authenticated user from the JWT token.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await UserCRUD(db).get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# --- Get Current Authenticated Admin Dependency ---
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db)
):
    """
    Retrieve the current authenticated admin from the JWT token.
    Raises 403 if the user is not an admin.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        admin = await AdminCRUD(db).get_by_user_id(user_id)
        if not admin or not getattr(admin, "is_active", True):
            raise HTTPException(status_code=403, detail="Not an active admin")
        return admin
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
