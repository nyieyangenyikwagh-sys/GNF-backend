from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    patients,
    insurance,
    claims,
    payments,
    appeals,
    analytics,
)

from app.models import Base
from app.core.database import engine


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Canadian Health Claims Platform",
    version="1.0.0",
)


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
    return {"status": "ok"}