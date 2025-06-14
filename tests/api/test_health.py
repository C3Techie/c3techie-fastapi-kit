import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
