# Tenant/Clinic Model Improvements

**Current Status:** Review & Suggestions  
**Date:** 2026-06-06

---

## 📋 Current State Analysis

### Existing Tenant Fields (Good ✅)

| Category | Fields | Status |
|----------|--------|--------|
| **Basic Info** | `id`, `name`, `email`, `phone` | ✅ Good |
| **Clinic** | `clinic_name`, `clinic_address` | ⚠️ Basic - needs expansion |
| **Location** | `division_id`, `district_id`, `upazila_id` | ✅ Good (Bangladesh specific) |
| **Medical** | `specializations[]` (homeopathy, ayurveda, unani, herbal) | ✅ Excellent |
| **License** | `license_number`, `is_verified`, `verified_at` | ✅ Good |
| **Subscription** | `plan`, `plan_started_at`, `plan_expires_at` | ✅ Good |
| **Status** | `is_active`, `is_approved`, `approved_at`, `approved_by` | ✅ Good |
| **Audit** | `created_at`, `updated_at`, `created_by`, `updated_by` | ✅ Good |

### Missing Critical Fields ❌

1. **Clinic Contact & Hours**
   - ❌ `clinic_phone` (separate from owner phone)
   - ❌ `clinic_email` (separate from owner email)
   - ❌ `website_url`
   - ❌ `working_hours` (JSON: day → time slots)
   - ❌ `emergency_contact`

2. **Location Details**
   - ❌ `postal_code` / `zip_code`
   - ❌ `latitude` / `longitude` (for maps)
   - ❌ `full_address_line_1`, `full_address_line_2`
   - ❌ `landmark` (common in Bangladesh)

3. **Professional Details**
   - ❌ `registration_body` (e.g., BMDC, Homeopathic Board)
   - ❌ `registration_number` (different from license)
   - ❌ `registration_year`
   - ❌ `degrees[]` (BHMS, BAMS, BUMS, etc.)
   - ❌ `years_of_experience`

4. **Clinic Metadata**
   - ❌ `logo_url`
   - ❌ `description` (clinic bio)
   - ❌ `description_bn` (Bengali)
   - ❌ `services_offered[]` (list of services)
   - ❌ `languages_spoken[]` (English, Bengali, etc.)
   - ❌ `consultation_fee` (default fee)
   - ❌ `follow_up_fee` (discounted fee)

5. **Operational**
   - ❌ `timezone` (default: Asia/Dhaka)
   - ❌ `currency` (default: BDT)
   - ❌ `tax_id` / `tin` (Tax ID Number)
   - ❌ `accepts_online_appointment`
   - ❌ `accepts_online_payment`

6. **Settings/Preferences**
   - ❌ `appointment_slot_duration` (default: 15 mins)
   - ❌ `booking_advance_limit_days` (how far patients can book)
   - ❌ `cancellation_policy`
   - ❌ `prescription_header` (custom header text)
   - ❌ `prescription_footer` (custom footer text)

7. **Social & Marketing**
   - ❌ `facebook_url`
   - ❌ `instagram_url`
   - ❌ `linkedin_url`
   - ❌ `google_maps_link`

---

## 🎯 Recommended Improvements

### Priority 1: Essential Clinic Information (HIGH)

Add these fields immediately for MVP+:

```python
# In Tenant model (app/shared/models/tenant.py)

class Tenant(BaseAuditModel):
    # ... existing fields ...
    
    # === PRIORITY 1: Essential Clinic Info ===
    
    # Contact details (separate from owner)
    clinic_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    clinic_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clinic_whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Full address breakdown
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Geolocation for maps
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    
    # Clinic branding
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Professional credentials
    registration_body: Mapped[str | None] = mapped_column(
        String(100), 
        nullable=True,
        comment="e.g., BMDC, Bangladesh Homeopathic Board"
    )
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registration_year: Mapped[int | None] = mapped_column(nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(nullable=True)
    
    # Operational settings
    timezone: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="Asia/Dhaka"
    )
    currency: Mapped[str] = mapped_column(
        String(3), 
        nullable=False, 
        default="BDT"
    )
    
    # Fees (in paisa/cents for precision)
    consultation_fee: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Fee in paisa (100 paisa = 1 BDT)"
    )
    follow_up_fee: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Follow-up fee in paisa"
    )
```

---

### Priority 2: Working Hours & Availability (HIGH)

Use JSONB for flexible scheduling:

```python
from sqlalchemy.dialects.postgresql import JSONB

class Tenant(BaseAuditModel):
    # ... existing fields ...
    
    # Working hours (flexible JSON structure)
    working_hours: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Day-wise working hours"
    )
    
    # Example working_hours structure:
    """
    {
        "saturday": [
            {"start": "09:00", "end": "13:00"},
            {"start": "17:00", "end": "21:00"}
        ],
        "sunday": [{"start": "09:00", "end": "13:00"}],
        "monday": [{"start": "09:00", "end": "21:00"}],
        "tuesday": [{"start": "09:00", "end": "21:00"}],
        "wednesday": [{"start": "09:00", "end": "21:00"}],
        "thursday": [{"start": "09:00", "end": "21:00"}],
        "friday": []  // Closed
    }
    """
    
    # Appointment settings
    appointment_slot_duration: Mapped[int] = mapped_column(
        nullable=False,
        default=15,
        comment="Appointment duration in minutes"
    )
    booking_advance_limit_days: Mapped[int] = mapped_column(
        nullable=False,
        default=30,
        comment="How many days in advance patients can book"
    )
    same_day_booking_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    
    # Online capabilities
    accepts_online_appointment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    accepts_online_payment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
```

---

### Priority 3: Services & Capabilities (MEDIUM)

```python
class Tenant(BaseAuditModel):
    # ... existing fields ...
    
    # Services offered
    services_offered: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="e.g., Consultation, Diagnosis, Treatment, Home Visit"
    )
    
    # Languages
    languages_spoken: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)),
        nullable=False,
        server_default='{"english", "bengali"}',
        comment="Languages for consultation"
    )
    
    # Tax information
    tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="TIN (Tax Identification Number)"
    )
    vat_registered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
```

---

### Priority 4: Settings & Customization (MEDIUM)

```python
class Tenant(BaseAuditModel):
    # ... existing fields ...
    
    # Prescription customization
    prescription_settings: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    
    # Example prescription_settings:
    """
    {
        "header_text": "Dr. XYZ Homeopathic Clinic",
        "header_text_bn": "ডা. XYZ হোমিওপ্যাথিক ক্লিনিক",
        "footer_text": "Follow instructions carefully",
        "footer_text_bn": "নির্দেশাবলী সাবধানে অনুসরণ করুন",
        "show_logo": true,
        "show_license": true,
        "show_registration": true,
        "watermark_text": "Confidential"
    }
    """
    
    # Cancellation policy
    cancellation_policy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cancellation/refund policy text"
    )
    cancellation_policy_bn: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    
    # Notification preferences
    notification_settings: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    
    # Example notification_settings:
    """
    {
        "send_appointment_reminders": true,
        "reminder_hours_before": 24,
        "send_sms": true,
        "send_email": false,
        "send_whatsapp": true
    }
    """
```

---

### Priority 5: Social & Web Presence (LOW)

```python
class Tenant(BaseAuditModel):
    # ... existing fields ...
    
    # Web presence
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_maps_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # SEO
    slug: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="URL-friendly clinic identifier (e.g., dr-abc-homeopathy-dhaka)"
    )
```

---

## 📦 Implementation Plan

### Step 1: Database Migration

Create migration file:

```bash
cd backend
source venv/bin/activate
alembic revision -m "add_comprehensive_clinic_fields"
```

**Migration file** (`backend/alembic/versions/XXXX_add_comprehensive_clinic_fields.py`):

```python
"""Add comprehensive clinic fields to tenants table

Revision ID: XXXX
Revises: YYYY
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'XXXX'
down_revision = 'YYYY'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Priority 1: Essential Clinic Info
    op.add_column('tenants', sa.Column('clinic_phone', sa.String(20), nullable=True))
    op.add_column('tenants', sa.Column('clinic_email', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('clinic_whatsapp', sa.String(20), nullable=True))
    
    op.add_column('tenants', sa.Column('address_line_1', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('address_line_2', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('postal_code', sa.String(10), nullable=True))
    op.add_column('tenants', sa.Column('landmark', sa.String(255), nullable=True))
    
    op.add_column('tenants', sa.Column('latitude', sa.Float, nullable=True))
    op.add_column('tenants', sa.Column('longitude', sa.Float, nullable=True))
    
    op.add_column('tenants', sa.Column('logo_url', sa.String(500), nullable=True))
    op.add_column('tenants', sa.Column('description_en', sa.Text, nullable=True))
    op.add_column('tenants', sa.Column('description_bn', sa.Text, nullable=True))
    
    op.add_column('tenants', sa.Column('registration_body', sa.String(100), nullable=True))
    op.add_column('tenants', sa.Column('registration_number', sa.String(100), nullable=True))
    op.add_column('tenants', sa.Column('registration_year', sa.Integer, nullable=True))
    op.add_column('tenants', sa.Column('years_of_experience', sa.Integer, nullable=True))
    
    op.add_column('tenants', sa.Column('timezone', sa.String(50), nullable=False, server_default='Asia/Dhaka'))
    op.add_column('tenants', sa.Column('currency', sa.String(3), nullable=False, server_default='BDT'))
    op.add_column('tenants', sa.Column('consultation_fee', sa.Integer, nullable=True, comment='Fee in paisa'))
    op.add_column('tenants', sa.Column('follow_up_fee', sa.Integer, nullable=True, comment='Follow-up fee in paisa'))
    
    # Priority 2: Working Hours
    op.add_column('tenants', sa.Column('working_hours', postgresql.JSONB, nullable=True))
    op.add_column('tenants', sa.Column('appointment_slot_duration', sa.Integer, nullable=False, server_default='15'))
    op.add_column('tenants', sa.Column('booking_advance_limit_days', sa.Integer, nullable=False, server_default='30'))
    op.add_column('tenants', sa.Column('same_day_booking_enabled', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('tenants', sa.Column('accepts_online_appointment', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('tenants', sa.Column('accepts_online_payment', sa.Boolean, nullable=False, server_default='false'))
    
    # Priority 3: Services
    op.add_column('tenants', sa.Column('services_offered', postgresql.ARRAY(sa.String(100)), nullable=True))
    op.add_column('tenants', sa.Column('languages_spoken', postgresql.ARRAY(sa.String(20)), 
                                       nullable=False, server_default='{"english", "bengali"}'))
    op.add_column('tenants', sa.Column('tax_id', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('vat_registered', sa.Boolean, nullable=False, server_default='false'))
    
    # Priority 4: Settings
    op.add_column('tenants', sa.Column('prescription_settings', postgresql.JSONB, nullable=True))
    op.add_column('tenants', sa.Column('cancellation_policy', sa.Text, nullable=True))
    op.add_column('tenants', sa.Column('cancellation_policy_bn', sa.Text, nullable=True))
    op.add_column('tenants', sa.Column('notification_settings', postgresql.JSONB, nullable=True))
    
    # Priority 5: Social
    op.add_column('tenants', sa.Column('website_url', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('facebook_url', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('instagram_url', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('linkedin_url', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('google_maps_link', sa.String(500), nullable=True))
    op.add_column('tenants', sa.Column('slug', sa.String(100), nullable=True, unique=True))
    
    # Create index on slug
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_tenants_slug', 'tenants')
    
    # Drop all new columns
    columns_to_drop = [
        'clinic_phone', 'clinic_email', 'clinic_whatsapp',
        'address_line_1', 'address_line_2', 'postal_code', 'landmark',
        'latitude', 'longitude',
        'logo_url', 'description_en', 'description_bn',
        'registration_body', 'registration_number', 'registration_year', 'years_of_experience',
        'timezone', 'currency', 'consultation_fee', 'follow_up_fee',
        'working_hours', 'appointment_slot_duration', 'booking_advance_limit_days',
        'same_day_booking_enabled', 'accepts_online_appointment', 'accepts_online_payment',
        'services_offered', 'languages_spoken', 'tax_id', 'vat_registered',
        'prescription_settings', 'cancellation_policy', 'cancellation_policy_bn', 'notification_settings',
        'website_url', 'facebook_url', 'instagram_url', 'linkedin_url', 'google_maps_link', 'slug'
    ]
    
    for col in columns_to_drop:
        op.drop_column('tenants', col)
```

---

### Step 2: Update Pydantic Schemas

**Create** `backend/app/shared/schemas/tenant.py`:

```python
"""Tenant/Clinic Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from typing import Literal


# ============================================================================
# Tenant Profile Schemas
# ============================================================================


class TenantProfileUpdate(BaseModel):
    """Update clinic profile information."""
    
    # Basic
    name: str | None = Field(None, max_length=255)
    clinic_name: str | None = Field(None, max_length=255)
    
    # Contact
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    clinic_phone: str | None = Field(None, max_length=20)
    clinic_email: EmailStr | None = None
    clinic_whatsapp: str | None = Field(None, max_length=20)
    
    # Address
    address_line_1: str | None = Field(None, max_length=255)
    address_line_2: str | None = Field(None, max_length=255)
    clinic_address: str | None = None  # Keep for backward compatibility
    postal_code: str | None = Field(None, max_length=10)
    landmark: str | None = Field(None, max_length=255)
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None
    
    # Geolocation
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    
    # Professional
    license_number: str | None = Field(None, max_length=100)
    registration_body: str | None = Field(None, max_length=100)
    registration_number: str | None = Field(None, max_length=100)
    registration_year: int | None = Field(None, ge=1900, le=2100)
    years_of_experience: int | None = Field(None, ge=0, le=100)
    specializations: list[str] | None = Field(None, min_length=1, max_length=4)
    
    # Branding
    logo_url: HttpUrl | None = None
    description_en: str | None = None
    description_bn: str | None = None
    
    # Operational
    timezone: str | None = Field(None, max_length=50)
    currency: str | None = Field(None, max_length=3)
    consultation_fee: int | None = Field(None, ge=0, description="Fee in paisa")
    follow_up_fee: int | None = Field(None, ge=0, description="Follow-up fee in paisa")
    
    # Services
    services_offered: list[str] | None = None
    languages_spoken: list[str] | None = None
    tax_id: str | None = Field(None, max_length=50)
    vat_registered: bool | None = None
    
    # Social
    website_url: HttpUrl | None = None
    facebook_url: HttpUrl | None = None
    instagram_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None
    google_maps_link: HttpUrl | None = None
    
    @field_validator("specializations")
    @classmethod
    def validate_specializations(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        allowed = {"homeopathy", "ayurveda", "unani", "herbal"}
        for spec in v:
            if spec not in allowed:
                raise ValueError(f"Invalid specialization '{spec}'. Allowed: {allowed}")
        return list(set(v))


class WorkingHoursSlot(BaseModel):
    """Single time slot."""
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")


class WorkingHoursUpdate(BaseModel):
    """Update working hours."""
    saturday: list[WorkingHoursSlot] | None = None
    sunday: list[WorkingHoursSlot] | None = None
    monday: list[WorkingHoursSlot] | None = None
    tuesday: list[WorkingHoursSlot] | None = None
    wednesday: list[WorkingHoursSlot] | None = None
    thursday: list[WorkingHoursSlot] | None = None
    friday: list[WorkingHoursSlot] | None = None


class AppointmentSettingsUpdate(BaseModel):
    """Update appointment settings."""
    appointment_slot_duration: int | None = Field(None, ge=5, le=120, description="Minutes")
    booking_advance_limit_days: int | None = Field(None, ge=1, le=365)
    same_day_booking_enabled: bool | None = None
    accepts_online_appointment: bool | None = None
    accepts_online_payment: bool | None = None


class PrescriptionSettingsUpdate(BaseModel):
    """Update prescription customization settings."""
    header_text: str | None = None
    header_text_bn: str | None = None
    footer_text: str | None = None
    footer_text_bn: str | None = None
    show_logo: bool | None = None
    show_license: bool | None = None
    show_registration: bool | None = None
    watermark_text: str | None = None


class NotificationSettingsUpdate(BaseModel):
    """Update notification preferences."""
    send_appointment_reminders: bool | None = None
    reminder_hours_before: int | None = Field(None, ge=1, le=72)
    send_sms: bool | None = None
    send_email: bool | None = None
    send_whatsapp: bool | None = None


class TenantResponse(BaseModel):
    """Complete tenant/clinic profile response."""
    
    # Basic
    id: str
    name: str
    clinic_name: str | None
    
    # Contact
    email: str
    phone: str | None
    clinic_phone: str | None
    clinic_email: str | None
    clinic_whatsapp: str | None
    
    # Address
    address_line_1: str | None
    address_line_2: str | None
    clinic_address: str | None
    postal_code: str | None
    landmark: str | None
    division_id: int | None
    district_id: int | None
    upazila_id: int | None
    latitude: float | None
    longitude: float | None
    
    # Professional
    specializations: list[str]
    license_number: str | None
    registration_body: str | None
    registration_number: str | None
    registration_year: int | None
    years_of_experience: int | None
    is_verified: bool
    verified_at: datetime | None
    
    # Branding
    logo_url: str | None
    description_en: str | None
    description_bn: str | None
    slug: str | None
    
    # Operational
    timezone: str
    currency: str
    consultation_fee: int | None
    follow_up_fee: int | None
    
    # Working hours & settings
    working_hours: dict | None
    appointment_slot_duration: int
    booking_advance_limit_days: int
    same_day_booking_enabled: bool
    accepts_online_appointment: bool
    accepts_online_payment: bool
    
    # Services
    services_offered: list[str] | None
    languages_spoken: list[str]
    tax_id: str | None
    vat_registered: bool
    
    # Customization
    prescription_settings: dict | None
    notification_settings: dict | None
    cancellation_policy: str | None
    cancellation_policy_bn: str | None
    
    # Social
    website_url: str | None
    facebook_url: str | None
    instagram_url: str | None
    linkedin_url: str | None
    google_maps_link: str | None
    
    # Subscription
    plan: str
    plan_started_at: datetime
    plan_expires_at: datetime | None
    
    # Status
    is_active: bool
    is_approved: bool
    approved_at: datetime | None
    
    # Audit
    created_at: datetime
    updated_at: datetime | None
    
    model_config = {"from_attributes": True}


class TenantListItem(BaseModel):
    """Minimal tenant info for listings."""
    id: str
    name: str
    clinic_name: str | None
    specializations: list[str]
    division_id: int | None
    district_id: int | None
    is_verified: bool
    plan: str
    
    model_config = {"from_attributes": True}
```

---

### Step 3: Create Tenant API Endpoints

**Create** `backend/app/modules/tenant/` module:

```bash
mkdir -p app/modules/tenant
touch app/modules/tenant/__init__.py
touch app/modules/tenant/routes.py
touch app/modules/tenant/service.py
```

**File:** `backend/app/modules/tenant/routes.py`

```python
"""Tenant/Clinic profile management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.tenant.service import TenantService
from app.shared.schemas.tenant import (
    TenantResponse,
    TenantProfileUpdate,
    WorkingHoursUpdate,
    AppointmentSettingsUpdate,
    PrescriptionSettingsUpdate,
    NotificationSettingsUpdate,
)

router = APIRouter()


def get_tenant_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TenantService:
    """Dependency for tenant service."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant users can access clinic profile"
        )
    return TenantService(db=db, tenant_id=current_user.tenant_id)


# ===== Tenant Profile Management =====


@router.get("/profile", response_model=TenantResponse)
async def get_clinic_profile(
    service: Annotated[TenantService, Depends(get_tenant_service)],
):
    """
    Get current clinic/tenant profile.
    
    - Returns complete clinic information
    - Available to all tenant users (doctor, receptionist)
    """
    return await service.get_tenant_profile()


@router.patch("/profile", response_model=TenantResponse)
async def update_clinic_profile(
    data: TenantProfileUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update clinic/tenant profile.
    
    - Only doctors can update (receptionist read-only)
    - Partial updates supported
    - Logo upload handled separately via /upload-logo endpoint
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update clinic profile"
        )
    
    return await service.update_tenant_profile(data, updated_by=current_user.user_id)


@router.patch("/working-hours", response_model=TenantResponse)
async def update_working_hours(
    data: WorkingHoursUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update clinic working hours.
    
    - Set different time slots for each day
    - Empty array = closed on that day
    - Example: {"saturday": [{"start": "09:00", "end": "13:00"}]}
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update working hours"
        )
    
    return await service.update_working_hours(data, updated_by=current_user.user_id)


@router.patch("/appointment-settings", response_model=TenantResponse)
async def update_appointment_settings(
    data: AppointmentSettingsUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update appointment booking settings.
    
    - Slot duration (5-120 minutes)
    - Advance booking limit
    - Online booking enabled/disabled
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update settings"
        )
    
    return await service.update_appointment_settings(data, updated_by=current_user.user_id)


@router.patch("/prescription-settings", response_model=TenantResponse)
async def update_prescription_settings(
    data: PrescriptionSettingsUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update prescription customization settings.
    
    - Header/footer text (bilingual)
    - Logo, license, registration display
    - Watermark text
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update settings"
        )
    
    return await service.update_prescription_settings(data, updated_by=current_user.user_id)


@router.patch("/notification-settings", response_model=TenantResponse)
async def update_notification_settings(
    data: NotificationSettingsUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update notification preferences.
    
    - Appointment reminders (SMS/Email/WhatsApp)
    - Reminder timing
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update settings"
        )
    
    return await service.update_notification_settings(data, updated_by=current_user.user_id)
```

**File:** `backend/app/modules/tenant/service.py`

```python
"""Tenant service with business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.shared.models.tenant import Tenant
from app.shared.schemas.tenant import (
    TenantProfileUpdate,
    WorkingHoursUpdate,
    AppointmentSettingsUpdate,
    PrescriptionSettingsUpdate,
    NotificationSettingsUpdate,
)


class TenantService:
    """Service for managing tenant/clinic profiles."""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def get_tenant_profile(self) -> Tenant:
        """Get complete tenant profile."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic profile not found"
            )
        
        return tenant
    
    async def update_tenant_profile(
        self, 
        data: TenantProfileUpdate, 
        updated_by: str
    ) -> Tenant:
        """Update tenant profile information."""
        tenant = await self.get_tenant_profile()
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        tenant.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def update_working_hours(
        self, 
        data: WorkingHoursUpdate, 
        updated_by: str
    ) -> Tenant:
        """Update working hours."""
        tenant = await self.get_tenant_profile()
        
        # Merge with existing working hours
        existing_hours = tenant.working_hours or {}
        new_hours = data.model_dump(exclude_unset=True)
        
        # Convert Pydantic models to dicts
        for day, slots in new_hours.items():
            if slots is not None:
                existing_hours[day] = [
                    {"start": slot.start, "end": slot.end} 
                    for slot in slots
                ]
        
        tenant.working_hours = existing_hours
        tenant.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def update_appointment_settings(
        self, 
        data: AppointmentSettingsUpdate, 
        updated_by: str
    ) -> Tenant:
        """Update appointment settings."""
        tenant = await self.get_tenant_profile()
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        tenant.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def update_prescription_settings(
        self, 
        data: PrescriptionSettingsUpdate, 
        updated_by: str
    ) -> Tenant:
        """Update prescription settings."""
        tenant = await self.get_tenant_profile()
        
        existing_settings = tenant.prescription_settings or {}
        new_settings = data.model_dump(exclude_unset=True)
        existing_settings.update(new_settings)
        
        tenant.prescription_settings = existing_settings
        tenant.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def update_notification_settings(
        self, 
        data: NotificationSettingsUpdate, 
        updated_by: str
    ) -> Tenant:
        """Update notification settings."""
        tenant = await self.get_tenant_profile()
        
        existing_settings = tenant.notification_settings or {}
        new_settings = data.model_dump(exclude_unset=True)
        existing_settings.update(new_settings)
        
        tenant.notification_settings = existing_settings
        tenant.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
```

**File:** `backend/app/modules/tenant/__init__.py`

```python
"""Tenant/Clinic profile management module."""

from app.modules.tenant.routes import router

__all__ = ["router"]
```

---

### Step 4: Register Routes

**Update** `backend/app/main.py`:

```python
# ... existing imports ...
from app.modules.tenant import router as tenant_router

# ... existing routers ...
app.include_router(tenant_router, prefix=f"{settings.API_V1_PREFIX}/tenant", tags=["Tenant"])
```

---

## 📝 Summary of Improvements

### What's Missing in Current Model ❌

1. **No separate clinic contact** (phone/email) - only owner contact
2. **Poor address structure** - single text field instead of structured address
3. **No geolocation** - can't show on maps
4. **No working hours** - can't show availability
5. **No fees information** - consultation/follow-up fees
6. **No branding** - logo, description, social links
7. **No operational settings** - timezone, appointment settings
8. **No customization** - prescription headers/footers
9. **Limited professional info** - no registration details, experience

### After Implementation ✅

1. ✅ **Complete contact info** - separate clinic & owner contacts
2. ✅ **Structured address** - line 1, line 2, postal code, landmark, lat/long
3. ✅ **Map integration ready** - latitude/longitude fields
4. ✅ **Working hours** - flexible JSONB with day-wise slots
5. ✅ **Fees management** - consultation & follow-up fees (in paisa)
6. ✅ **Professional branding** - logo, bilingual descriptions, slug
7. ✅ **Full credentials** - registration body, number, year, experience
8. ✅ **Operational settings** - timezone, currency, appointment config
9. ✅ **Customization** - prescription & notification settings
10. ✅ **Social presence** - website, Facebook, Instagram, LinkedIn, Google Maps

---

## 🚀 Next Steps

1. **Review this document** - confirm field requirements
2. **Run migration** - `alembic upgrade head`
3. **Test endpoints** - use Swagger UI at `/docs`
4. **Update frontend** - add clinic profile management UI
5. **Seed sample data** - create realistic clinic profiles for testing

---

Would you like me to:
1. ✅ Create the actual migration file?
2. ✅ Implement the model changes?
3. ✅ Create the API endpoints?
4. ✅ Add frontend profile management UI?

Let me know which part to implement first!
