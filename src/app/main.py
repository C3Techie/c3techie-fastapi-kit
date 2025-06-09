from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings

from app.api.routes.v1.router import api_router
from app.api.routes.health import router as health_router
from app.core.exceptions import (
    NotFoundError, AuthenticationError, ConflictError,
    ValidationError, DatabaseError, AuthorizationError
)
from app.core.middleware import LoggingMiddleware
from app.core.rate_limiter import init_rate_limiter

REDIS_URL = settings.REDIS_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await init_rate_limiter(REDIS_URL)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(LoggingMiddleware)

# Global exception handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.exception_handler(ConflictError)
async def conflict_error_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Register health check
app.include_router(health_router, prefix="/api/health", tags=["health"])

# Register all v1 endpoints (users, auth, admin etc.)
app.include_router(api_router, prefix="/api/v1")
