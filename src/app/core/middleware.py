from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import uuid
from app.utils.logging import get_logger


logger = get_logger("uvicorn.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        if response.status_code >= 500:
            logger.error(
                "[%s] %s %s - %d - %.2fms",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                process_time
            )
        elif response.status_code >= 400:
            logger.warning(
                "[%s] %s %s - %d - %.2fms",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                process_time
            )
        return response
