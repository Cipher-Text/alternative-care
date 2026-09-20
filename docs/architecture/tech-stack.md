# Technology Stack — Detailed Guide

> Comprehensive guide to AltCare's technology choices, rationale, and implementation best practices

**Last updated:** 2026-09-21  
**Status:** MVP v1.0 production-ready (see root `CLAUDE.md`) — several code samples below are illustrative/aspirational rather than a literal copy of the current implementation; see inline corrections where they diverge

---

## Table of Contents

- [Stack Overview](#stack-overview)
- [Backend Deep Dive](#backend-deep-dive)
- [Frontend Deep Dive](#frontend-deep-dive)
- [Database & Storage](#database--storage)
- [Security & Authentication](#security--authentication)
- [Monitoring & Observability](#monitoring--observability)
- [Testing Strategy](#testing-strategy)
- [Third-Party Integrations](#third-party-integrations)
- [Migration Paths](#migration-paths)
- [FAQs](#faqs)

---

## Stack Overview

### Philosophy

**Modular Monolith → Microservices when needed**

AltCare starts as a monolithic application with clear internal module boundaries. This approach:
- ✅ Faster initial development
- ✅ Simpler deployment and debugging
- ✅ Lower operational overhead
- ✅ Easy to extract services later if needed

### Core Principles

1. **Type Safety Everywhere**: Python type hints + Pydantic, TypeScript on frontend
2. **Async-First**: FastAPI async routes, SQLAlchemy async ORM, httpx for HTTP calls
3. **Developer Experience**: Auto-generated docs, hot reload, strong IDE support
4. **Production-Ready**: Comprehensive monitoring, logging, error tracking from day 1
5. **Cost-Conscious**: Self-hosted when possible, managed services only when scaling demands it

---

## Backend Deep Dive

### Python 3.12

**Why Python 3.12 specifically?**
- Performance improvements (15-25% faster than 3.10)
- Better error messages (PEP 678)
- Type hint improvements (PEP 695)
- Still has LTS support until 2028

**Key libraries (actual pins, from `backend/pyproject.toml` — PEP 621 `[project.dependencies]`, not Poetry):**
```toml
# backend/pyproject.toml
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.1",
    "asyncpg>=0.29.0",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "bcrypt<5",
    "python-multipart>=0.0.6",
    "pyotp>=2.9.0",           # 2FA
    "qrcode>=7.4.2",
    "celery>=5.3.4",
    "redis>=5.0.1",
    "weasyprint>=60.2",
    "ebooklib>=0.18",
    "cryptography>=42.0.0",
    "structlog>=24.1.0",
    "slowapi>=0.1.9",         # dependency present, but NOT wired up — see Rate Limiting below
    "babel>=2.14.0",
    "httpx>=0.26.0",
    "sentry-sdk[fastapi]>=1.40.0",
    "prometheus-client>=0.19.0",
    "python-dotenv>=1.0.0",
]
```

There is **no `langchain`, `openai`, or `psycopg`** dependency in the backend today — the AI/RAG assistant is an unbuilt `501` stub (`POST /api/v1/ai/query`), and the only Postgres driver in use is `asyncpg` (no sync `psycopg` driver).

### FastAPI Architecture

**Actual middleware stack (`backend/app/main.py`) — simpler than earlier drafts of this doc described:**
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.rate_limit import close_redis_client
from app.core.middleware import rate_limit_middleware, add_security_headers

app = FastAPI(
    title="AltCare API",
    description="Alternative Medicine Practice Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting is a custom Redis-backed function middleware — NOT slowapi
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(add_security_headers)
```

There is no `sentry_sdk.init()` call, `RequestIDMiddleware`, `StructlogMiddleware`, or `TenantContextMiddleware` wired up in `app/main.py` today — tenant context is set inside the `get_current_user()` dependency (`app/core/dependencies.py`), not by a request middleware. `sentry-sdk`, `structlog`, and `slowapi` are all listed as dependencies but `slowapi` specifically is unused — rate limiting is hand-rolled in `app/core/rate_limit.py` / `app/core/middleware.py`.

### SQLAlchemy 2.0 Patterns

**Async session management:**
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Multi-tenant query pattern (actual structure: `service.py`, not a `repository.py` layer; there is no `get_current_tenant` dependency):**
```python
# app/modules/patient/service.py
class PatientService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id  # from get_patient_service() in routes.py

    async def list_patients(self, skip: int = 0, limit: int = 100) -> list[Patient]:
        result = await self.db.execute(
            select(Patient)
            .where(Patient.tenant_id == self.tenant_id)
            .order_by(Patient.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
```

There is no `deleted_at` column — `Patient` soft-deletes via `is_active`, filtered explicitly where needed. See [Multi-Tenancy](multi-tenancy.md) for how `tenant_id` actually flows from the JWT into each service (explicit per-method filtering, not an automatic global filter).

### Celery Task Queue

**Task structure:**
```python
# app/tasks/prescription.py
from celery import shared_task
import structlog

logger = structlog.get_logger()

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_prescription_pdf(self, prescription_id: str, tenant_id: str):
    """Generate PDF for prescription (runs in background)"""
    try:
        logger.info("generating_pdf", prescription_id=prescription_id)
        # ... PDF generation logic
        return {"status": "success", "pdf_url": url}
    except Exception as exc:
        logger.error("pdf_generation_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)
```

**Celery configuration:**
```python
# app/core/celery_app.py
from celery import Celery

celery_app = Celery(
    "altcare",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Dhaka",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.prescription.*": {"queue": "pdf"},
    "app.tasks.notification.*": {"queue": "email"},
    "app.tasks.ai.*": {"queue": "ai"},
}
```

---

## Frontend Deep Dive

### Next.js 16 + App Router

**Directory structure:**
```
frontend/
  app/
    (auth)/
      login/
        page.tsx
      register/
        page.tsx
    (dashboard)/
      layout.tsx              ← Shared sidebar, topbar
      page.tsx                ← Dashboard home
      patients/
        page.tsx
        [id]/
          page.tsx
      prescriptions/
        page.tsx
    api/                      ← API routes (if needed)
    layout.tsx                ← Root layout
    providers.tsx             ← React Query, Theme provider
  components/
    ui/                       ← shadcn/ui components
    patient-table.tsx
    prescription-builder.tsx
  lib/
    api-client.ts             ← Axios instance with interceptors
    hooks/
      usePatients.ts          ← React Query hooks
      useAuth.ts
  types/
    patient.ts
    prescription.ts
```

**API client setup:**
```typescript
// lib/api-client.ts
import axios from 'axios';
import { useAuth } from '@/lib/hooks/useAuth';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
});

// Request interceptor (add JWT)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle token refresh)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        });
        localStorage.setItem('access_token', data.access_token);
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

**React Query setup:**

The installed package is `react-query` (v3 — `frontend/package.json` pins `"react-query": "^3.39.3"`), not `@tanstack/react-query` (the v4+ successor package). Import from `react-query` to match what's actually installed:
```typescript
// lib/hooks/usePatients.ts
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiClient } from '@/lib/api-client';

export function usePatients(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['patients', page, limit],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/patients', {
        params: { page, limit },
      });
      return data;
    },
    staleTime: 60000, // 1 minute
  });
}

export function useCreatePatient() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (patient: PatientCreate) => 
      apiClient.post('/api/v1/patients', patient),
    onSuccess: () => {
      // Invalidate patient list
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });
}
```

---

## Database & Storage

### PostgreSQL 16 Configuration

**Production postgresql.conf tuning:**
```ini
# Connection settings
max_connections = 100
shared_buffers = 2GB          # 25% of RAM
effective_cache_size = 6GB    # 75% of RAM
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1        # For SSD
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 100  # Log slow queries > 100ms
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0

# Extensions
shared_preload_libraries = 'pg_stat_statements'
```

### pgvector for AI/RAG

**Setup:**
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Embeddings table
CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
  embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for cosine similarity search
CREATE INDEX idx_embeddings_vector ON embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on data size
```

**Query pattern:**
```python
# Cosine similarity search
async def search_similar_sections(
    db: AsyncSession,
    query_embedding: list[float],
    tenant_id: UUID,
    limit: int = 5,
) -> list[Section]:
    result = await db.execute(
        text("""
            SELECT s.id, s.content, s.book_id,
                   1 - (e.embedding <=> :query_embedding) AS similarity
            FROM sections s
            JOIN embeddings e ON e.section_id = s.id
            JOIN books b ON b.id = s.book_id
            WHERE b.system = ANY(
                SELECT unnest(specializations) 
                FROM tenants 
                WHERE id = :tenant_id
            )
            ORDER BY e.embedding <=> :query_embedding
            LIMIT :limit
        """),
        {
            "query_embedding": str(query_embedding),
            "tenant_id": str(tenant_id),
            "limit": limit,
        }
    )
    return result.all()
```

---

## Security & Authentication

### JWT Implementation

**Token structure:** default access-token lifetime is 30 minutes (`settings.ACCESS_TOKEN_EXPIRE_MINUTES`), not 1 hour, and `create_refresh_token()` takes the same `data: dict` shape as `create_access_token()` (minimally `{sub, token_version}`), not a bare `user_id`. See [Authentication](authentication.md) for the accurate signatures and full claim set (including `token_version` for invalidation).

### 2FA with TOTP

**Setup flow:**
```python
# app/modules/auth/service.py
import pyotp
import qrcode

def generate_2fa_secret(user: User) -> dict:
    """Generate TOTP secret for user"""
    secret = pyotp.random_base32()
    
    # Store secret (encrypted)
    user.totp_secret = encrypt_secret(secret)
    
    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="AltCare"
    )
    
    # Generate QR code image
    qr = qrcode.make(totp_uri)
    # ... save QR code to temp file
    
    return {
        "secret": secret,  # Show once to user
        "qr_code_url": qr_code_url,
    }

def verify_2fa_token(user: User, token: str) -> bool:
    """Verify TOTP token"""
    if not user.totp_secret:
        return False
    
    secret = decrypt_secret(user.totp_secret)
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 1 window drift
```

### Rate Limiting

**Actual implementation:** a custom Redis-backed function middleware (`app/core/rate_limit.py` + `app/core/middleware.py:rate_limit_middleware`), applied globally in `app/main.py` — not `slowapi` per-route decorators (that dependency is present but unused). Limits come from `app/core/config.py`:

```python
# app/core/config.py (defaults; overridable via env vars)
RATE_LIMIT_PER_MINUTE: int = 60          # general API, per IP
RATE_LIMIT_LOGIN_PER_MINUTE: int = 5     # login, per IP
RATE_LIMIT_AI_PER_HOUR: int = 20         # AI endpoints, per user
```

The middleware inspects the request path/method to pick a scope (login vs. general vs. AI), builds a Redis key, and returns `429` with `X-RateLimit-Limit` / `X-RateLimit-Remaining` / `Retry-After` headers when exceeded — falling back to an in-memory counter if Redis is unavailable.

---

## Monitoring & Observability

### Sentry Integration

```python
# app/core/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of profiles
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        CeleryIntegration(),
    ],
    before_send=before_send_handler,  # Custom filtering
)

def before_send_handler(event, hint):
    """Filter sensitive data before sending to Sentry"""
    # Remove sensitive fields
    if 'request' in event:
        if 'headers' in event['request']:
            event['request']['headers'].pop('Authorization', None)
            event['request']['headers'].pop('Cookie', None)
    return event
```

### Structured Logging

```python
# app/core/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Usage
logger = structlog.get_logger()
logger.info(
    "patient_created",
    patient_id=patient.id,
    tenant_id=patient.tenant_id,
    created_by=current_user.id,
)
```

### Prometheus Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Counters
prescription_created_counter = Counter(
    'prescriptions_created_total',
    'Total prescriptions created',
    ['tenant_id', 'status']
)

# Histograms
api_latency_histogram = Histogram(
    'api_request_duration_seconds',
    'API request latency',
    ['method', 'endpoint', 'status_code']
)

# Gauges
active_patients_gauge = Gauge(
    'active_patients',
    'Number of active patients',
    ['tenant_id']
)

# Usage in routes
@router.post("/prescriptions")
async def create_prescription(...):
    start_time = time.time()
    try:
        # ... create prescription
        prescription_created_counter.labels(
            tenant_id=tenant_id,
            status='success'
        ).inc()
        return prescription
    finally:
        duration = time.time() - start_time
        api_latency_histogram.labels(
            method='POST',
            endpoint='/prescriptions',
            status_code=200
        ).observe(duration)
```

---

## Testing Strategy

### Backend Testing

**Pytest configuration:**
```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """Create clean test database for each test"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/altcare_test"
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    """Test client with database override"""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def tenant_factory(faker):
    """Factory for creating test tenants"""
    def _create(specializations=["homeopathy"]):
        return Tenant(
            id=uuid4(),
            name=faker.company(),
            email=faker.email(),
            specializations=specializations,
        )
    return _create
```

**Multi-tenant isolation test:**
```python
# tests/test_multi_tenant.py
import pytest

@pytest.mark.asyncio
async def test_tenant_cannot_access_other_tenant_patients(
    client,
    tenant_factory,
    db_session
):
    """Critical: Ensure tenant A cannot see tenant B's patients"""
    # Create two tenants
    tenant_a = tenant_factory()
    tenant_b = tenant_factory()
    db_session.add_all([tenant_a, tenant_b])
    await db_session.commit()
    
    # Create patient for tenant A
    patient_a = Patient(
        tenant_id=tenant_a.id,
        full_name="Patient A",
    )
    db_session.add(patient_a)
    await db_session.commit()
    
    # Login as tenant B
    token_b = create_access_token({"sub": str(tenant_b.id)})
    
    # Try to access tenant A's patient
    response = await client.get(
        f"/api/v1/patients/{patient_a.id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    
    # Should return 404 (not 403 to avoid info leakage)
    assert response.status_code == 404
```

---

## Third-Party Integrations

### SSLCommerz (Bangladesh Payments)

```python
# app/modules/payment/providers/sslcommerz.py
import hashlib
import httpx

class SSLCommerzProvider:
    def __init__(self, store_id: str, store_password: str, sandbox: bool = False):
        self.store_id = store_id
        self.store_password = store_password
        self.base_url = (
            "https://sandbox.sslcommerz.com"
            if sandbox
            else "https://securepay.sslcommerz.com"
        )
    
    async def initiate_payment(
        self,
        amount: Decimal,
        transaction_id: str,
        customer: dict,
    ) -> dict:
        """Initiate payment session"""
        payload = {
            "store_id": self.store_id,
            "store_passwd": self.store_password,
            "total_amount": str(amount),
            "currency": "BDT",
            "tran_id": transaction_id,
            "success_url": f"{settings.FRONTEND_URL}/payment/success",
            "fail_url": f"{settings.FRONTEND_URL}/payment/failed",
            "cancel_url": f"{settings.FRONTEND_URL}/payment/cancelled",
            "ipn_url": f"{settings.API_URL}/api/v1/payments/webhook/sslcommerz",
            "cus_name": customer["name"],
            "cus_email": customer["email"],
            "cus_phone": customer["phone"],
            "product_name": "AltCare Consultation",
            "product_category": "Service",
            "product_profile": "general",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/gwprocess/v4/api.php",
                data=payload,
            )
            return response.json()
    
    def verify_webhook(self, data: dict) -> bool:
        """Verify webhook signature"""
        verify_sign = data.get("verify_sign")
        verify_key = data.get("verify_key")
        
        # Calculate expected signature
        expected = hashlib.md5(
            f"{self.store_password}{verify_key}".encode()
        ).hexdigest()
        
        return verify_sign == expected
```

---

## Migration Paths

### From Self-Hosted to Managed Services

**Database migration (PostgreSQL → Managed):**
```bash
# 1. Create dump from self-hosted
pg_dump -h localhost -U postgres altcare > backup.sql

# 2. Upload to managed instance
psql -h managed-db.provider.com -U postgres altcare < backup.sql

# 3. Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:pass@managed-db.provider.com/altcare

# 4. Test connection
docker compose exec api python -c "from app.core.database import engine; engine.connect()"

# 5. Zero-downtime migration (if needed)
# - Set up streaming replication
# - Failover during low-traffic window
```

### From JWT to Keycloak

**Keycloak integration:**
```python
# app/core/security.py
from keycloak import KeycloakOpenID

keycloak_openid = KeycloakOpenID(
    server_url=settings.KEYCLOAK_URL,
    client_id=settings.KEYCLOAK_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM,
    client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
)

async def get_current_user_keycloak(
    token: str = Depends(oauth2_scheme)
) -> User:
    """Validate Keycloak JWT and get user"""
    try:
        # Verify token with Keycloak
        token_info = keycloak_openid.introspect(token)
        if not token_info.get("active"):
            raise HTTPException(401, "Invalid token")
        
        # Get or create user from Keycloak info
        user_id = token_info["sub"]
        # ... fetch from DB
        
        return user
    except Exception as e:
        raise HTTPException(401, str(e))
```

---

## FAQs

### Why FastAPI over Django/Flask?

**FastAPI wins for this project because:**
- ✅ Native async support (Django async is immature)
- ✅ Auto-generated OpenAPI docs (saves hours)
- ✅ Type hints + Pydantic = better IDE support
- ✅ Faster than Flask (Uvicorn is fast)
- ✅ Modern Python patterns (decorators, dependency injection)

**Django would be better if:**
- You needed its admin panel (we're building custom admin)
- You needed its ORM's advanced features (SQLAlchemy is equivalent)
- Team already knows Django

### Why not use Supabase?

**Supabase is great, but:**
- ❌ Vendor lock-in (hard to migrate away)
- ❌ Limited control over database tuning
- ❌ Pricing scales quickly with growth
- ❌ Steeper learning curve for team

**We chose self-hosted PostgreSQL because:**
- ✅ Full control and flexibility
- ✅ Can migrate to managed PG later (same API)
- ✅ Lower costs at scale
- ✅ Team knows PostgreSQL

### Why LangChain for RAG?

**LangChain despite its issues because:**
- ✅ Fastest way to get RAG working
- ✅ Good documentation and examples
- ✅ Handles chunking, embedding, retrieval
- ✅ Can replace with llamaindex later if needed

**Mitigations:**
- Pin exact versions in requirements.txt
- Test thoroughly before updating
- Monitor for breaking changes

### Why not use Next.js API routes?

**We separated frontend and backend because:**
- ✅ Better for mobile app (future)
- ✅ Easier to scale independently
- ✅ API can be consumed by third parties
- ✅ Clearer separation of concerns

**Next.js API routes are fine for:**
- Server actions for forms
- Edge functions for simple tasks
- BFF (backend-for-frontend) layer

---

## Resources

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Next.js App Router Docs](https://nextjs.org/docs/app)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Multi-tenant Architecture Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/multi-tenancy)

---

**Last updated:** 2026-09-21  
**Maintainer:** AltCare Engineering Team
