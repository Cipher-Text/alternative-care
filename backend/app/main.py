"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import structlog
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.core.config import settings
from app.core.rate_limit import close_redis_client
from app.core.middleware import rate_limit_middleware, add_security_headers

# Import all models for Alembic autogenerate
from app.shared.models import *  # noqa: F401, F403

logger = structlog.get_logger(__name__)


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
    await close_redis_client()
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


# Apply middleware (order matters: first added = outermost layer)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(add_security_headers)


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


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
from app.modules.medicine import router as medicine_router
from app.modules.symptom import router as symptom_router
from app.modules.tenant import router as tenant_router

app.include_router(auth_router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(tenant_router, prefix=f"{settings.API_V1_PREFIX}/tenant", tags=["Tenant/Clinic"])
app.include_router(ai_router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["AI"])
app.include_router(appointments_router, prefix=f"{settings.API_V1_PREFIX}/appointments", tags=["Appointments"])
app.include_router(dashboard_router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Dashboard"])
app.include_router(doctor_router, prefix=f"{settings.API_V1_PREFIX}/doctor", tags=["Doctor"])
app.include_router(patient_router, prefix=f"{settings.API_V1_PREFIX}/patients", tags=["Patients"])
app.include_router(prescription_router, prefix=f"{settings.API_V1_PREFIX}/prescriptions", tags=["Prescriptions"])
app.include_router(payment_router, prefix=f"{settings.API_V1_PREFIX}/payments", tags=["Payments"])
app.include_router(integration_router, prefix=f"{settings.API_V1_PREFIX}/integrations", tags=["Integrations"])
app.include_router(medicine_router, prefix=f"{settings.API_V1_PREFIX}/medicines", tags=["Medicines"])
app.include_router(symptom_router, prefix=f"{settings.API_V1_PREFIX}/symptoms", tags=["Symptoms"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
