# router.py - Main API router for FastAPI v1
# Includes authentication and user management endpoints.

from fastapi import APIRouter
from app.api.routes.v1.users import router as users_router
from app.api.routes.v1.auth import router as auth_router
from app.api.routes.v1.admin import router as admin_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(admin_router, prefix="/admins", tags=["admins"])
