from fastapi.testclient import AsyncClient
import pytest_asyncio
from src.app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
