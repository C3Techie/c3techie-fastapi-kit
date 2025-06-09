from pydantic_settings import BaseSettings
from pydantic import EmailStr
from uuid import UUID

class Settings(BaseSettings):
    # Core
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # System constants
    SYSTEM_USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000000")

    # Admin
    DEFAULT_ADMIN_EMAIL: EmailStr = "admin@example.com"

    # Email / SMTP settings
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: EmailStr = "no-reply@example.com"
    FRONTEND_URL: str = "http://localhost:8000"
    API_BASE_URL: str = "http://localhost:8000"

    # Advanced email config for pools/retries
    EMAIL_THREAD_POOL_SIZE: int = 5
    EMAIL_MAX_RETRIES: int = 3
    EMAIL_RETRY_BASE_DELAY: float = 1.0
    EMAIL_RETRY_MAX_DELAY: float = 30.0
    SMTP_TIMEOUT: int = 10
    SMTP_POOL_SIZE: int = 3
    MAX_EMAIL_SIZE: int = 25 * 1024 * 1024

    # Caching
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
