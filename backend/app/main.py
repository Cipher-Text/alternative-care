"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

# Import all models for Alembic autogenerate
from app.shared.models import *  # noqa: F401, F403


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 AltCare Backend starting...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Database: Connected to PostgreSQL")
    print(f"🌐 CORS Origins: {settings.CORS_ORIGINS}")

    yield

    # Shutdown
    print("👋 AltCare Backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AltCare API",
    description="Alternative Medicine Practice Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Apply baseline HTTP security headers to all responses."""
    response = await call_next(request)

    if not settings.SECURITY_HEADERS_ENABLED:
        return response

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = settings.SECURITY_CSP_POLICY

    if (
        settings.SECURITY_HSTS_ENABLED
        and settings.ENVIRONMENT.lower() == "production"
    ):
        hsts = f"max-age={settings.SECURITY_HSTS_MAX_AGE}"
        if settings.SECURITY_HSTS_INCLUDE_SUBDOMAINS:
            hsts += "; includeSubDomains"
        if settings.SECURITY_HSTS_PRELOAD:
            hsts += "; preload"
        response.headers["Strict-Transport-Security"] = hsts

    return response


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": "0.1.0",
        }
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return JSONResponse(
        content={
            "message": "Welcome to AltCare API",
            "version": "0.1.0",
            "docs": "/docs",
        }
    )


# API routes
from app.modules.auth import router as auth_router
from app.modules.ai import router as ai_router
from app.modules.appointments import router as appointments_router
from app.modules.dashboard import router as dashboard_router
from app.modules.doctor import router as doctor_router
from app.modules.patient import router as patient_router
from app.modules.prescription import router as prescription_router
from app.modules.payment import router as payment_router
from app.modules.integration import router as integration_router

app.include_router(auth_router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(ai_router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["AI"])
app.include_router(appointments_router, prefix=f"{settings.API_V1_PREFIX}/appointments", tags=["Appointments"])
app.include_router(dashboard_router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])
app.include_router(doctor_router, prefix=f"{settings.API_V1_PREFIX}/doctor", tags=["Doctor"])
app.include_router(patient_router, prefix=f"{settings.API_V1_PREFIX}/patients", tags=["Patients"])
app.include_router(prescription_router, prefix=f"{settings.API_V1_PREFIX}/prescriptions", tags=["Prescriptions"])
app.include_router(payment_router, prefix=f"{settings.API_V1_PREFIX}/payments", tags=["Payments"])
app.include_router(integration_router, prefix=f"{settings.API_V1_PREFIX}/integrations", tags=["Integrations"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
