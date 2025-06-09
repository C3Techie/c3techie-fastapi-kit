# auth.py - Authentication endpoints for FastAPI v1
# Handles user login and token generation.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.shared.schemas.user import UserLogin, UserRead
from app.domains.shared.crud.user import UserCRUD
from app.domains.shared.crud.audit_log import AuditLogCRUD
from app.domains.shared.services.auth_service import AuthService
from app.dependencies import get_db
from app.core.security import create_access_token
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from app.core.exceptions import AuthenticationError
from app.core.rate_limiter import RateLimiter


router = APIRouter(tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# --- Dependency to get the user service ---
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    user_crud = UserCRUD(db)
    audit_crud = AuditLogCRUD(db)
    return AuthService(user_crud, audit_crud)


# --- User Login Endpoint ---
@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return access token.
    """
    try:
        user = await auth_service.authenticate_user(login_data.identifier, login_data.password)
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=UserRead.model_validate(user)
    )


# --- Verify Email Endpoint ---
@router.get("/verify-email")
async def verify_email(
    token: str,
    user_service: AuthService = Depends(get_auth_service)
):
    """
    Verify a user's email using a token sent to their email address.
    """
    try:
        user = await user_service.verify_email_token(token)
        return {"detail": "Email verified successfully", "user": UserRead.model_validate(user)}
    except AuthenticationError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )
