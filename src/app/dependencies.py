from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.config import settings
from typing import AsyncGenerator

# --- Database Session Dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session

# --- Settings Dependency ---
def get_settings():
    return settings
