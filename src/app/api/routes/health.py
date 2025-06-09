# health.py - Health check endpoint for FastAPI application

from fastapi import APIRouter


router = APIRouter(tags=["health"])


# --- Health Check Endpoint ---
@router.get("/")
async def health_check():
    """
    Health check endpoint.
    Returns a simple status message indicating the service is running.
    """
    return {"status": "healthy"}
