import logging
import re
import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    auth,
    patients,
    insurance,
    claims,
    payments,
    appeals,
    analytics,
)

from app.core.database import check_database_connection
from app.core.config import settings
from app.core.errors import error_body, http_error_handler, server_error_handler, validation_error_handler
from app.core.request_context import correlation_id_var
from app.core.logging_config import configure_logging
from app.services.recovery import recover_pending_claims

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        check_database_connection()
    except Exception:
        logger.exception("PostgreSQL is unavailable. Run migrations after the database is reachable.")
        raise
    stop = asyncio.Event()

    async def recovery_loop():
        while not stop.is_set():
            await asyncio.to_thread(recover_pending_claims)
            try:
                await asyncio.wait_for(stop.wait(), timeout=settings.RECOVERY_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                pass

    task = asyncio.create_task(recovery_loop())
    try:
        yield
    finally:
        stop.set()
        await task


# Create FastAPI application
app = FastAPI(
    title="Canadian Health Claims Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(Exception, server_error_handler)


@app.middleware("http")
async def request_safety(request: Request, call_next):
    supplied_id = request.headers.get("x-correlation-id", "")
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_id) else str(uuid.uuid4())
    token = correlation_id_var.set(request_id)
    try:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                too_large = int(content_length) > settings.MAX_REQUEST_BYTES
            except ValueError:
                return JSONResponse(error_body("INVALID_CONTENT_LENGTH", "Content-Length must be an integer"), status_code=400, headers={"X-Correlation-ID": request_id})
            if too_large:
                return JSONResponse(error_body("REQUEST_TOO_LARGE", "Request body exceeds the configured limit"), status_code=413, headers={"X-Correlation-ID": request_id})
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request_id
        logger.info("request_complete", extra={"correlation_id": request_id, "method": request.method, "path": request.url.path, "status_code": response.status_code})
        return response
    finally:
        correlation_id_var.reset(token)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

app.include_router(
    auth.router,
    prefix="/api/v1",
)

app.include_router(
    patients.router,
    prefix="/api/v1",
)

app.include_router(
    insurance.router,
    prefix="/api/v1",
)

app.include_router(
    claims.router,
    prefix="/api/v1",
)

app.include_router(
    appeals.router,
    prefix="/api/v1",
)

app.include_router(
    payments.router,
    prefix="/api/v1",
)

app.include_router(
    analytics.router,
    prefix="/api/v1",
)


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
