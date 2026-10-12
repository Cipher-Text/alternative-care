"""Patient identity across clinics (ADR 009, Phase 1).

Platform-level (no tenant_id) personal data, kept apart from every clinic's own patient record. An
identity holds who a person is and which clinic records belong to them; it holds no clinical data.
Linking is by consent only, never inferred.
"""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseAuditModel

RELATIONSHIPS = ("self", "child", "spouse", "parent", "other")
MAX_PROFILES_PER_ACCOUNT = 10


class PersonAccount(BaseAuditModel):
    """The account holder: a verified Bangladesh mobile number."""

    __tablename__ = "person_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    phone_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    # First time this phone signed in to the patient portal. Links made before this moment stay
    # hidden until a clinic code activates them (ADR 009 rule 10: a recycled number sees no history).
    portal_registered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PersonProfile(BaseAuditModel):
    """One person under an account (self, child, spouse, parent). Basic details only."""

    __tablename__ = "person_profiles"
    __table_args__ = (
        CheckConstraint(
            "relationship IN ('self','child','spouse','parent','other')", name="ck_person_profile_relationship"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("person_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Lower-cased, punctuation-free form used for matching a typed name and for de-duplication
    name_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    approx_birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    division_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    upazila_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relationship: Mapped[str] = mapped_column(String(10), nullable=False, default="self")
    # A child under 18, or someone who cannot act for themselves: the holder is their guardian
    is_dependent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    # Where the profile came from: 'clinic' (staff linked a record) or 'portal' (the holder added it)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="clinic", server_default="clinic")


class OtpChallenge(BaseAuditModel):
    """One SMS code sent to a phone. The code itself is never stored, only a keyed hash."""

    __tablename__ = "otp_challenges"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('clinic_verify','claim','portal_login')", name="ck_otp_challenge_purpose"
        ),
        Index("ix_otp_challenges_phone_created", "phone", "created_at"),
        Index("ix_otp_challenges_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(15), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True
    )
    requested_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    claim_code_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # sent | verified | failed | expired | send_failed (the last one is not counted against a plan cap)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="sent")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # After a successful clinic verification: a short-lived token that lets that staff member look
    # up profiles for this phone and link records. Stored hashed.
    account_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    search_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    link_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ConsentEvent(BaseAuditModel):
    """Append-only record of a consent to link, or of a revocation."""

    __tablename__ = "identity_consent_events"
    __table_args__ = (
        CheckConstraint("kind IN ('link','revoke','portal_access')", name="ck_identity_consent_kind"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(36), nullable=False)
    method: Mapped[str] = mapped_column(String(15), nullable=False)  # clinic_otp | claim_code | revoked
    staff_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Version of the wording the patient was shown or told; the staff member confirmed telling them
    script_version: Mapped[str] = mapped_column(String(20), nullable=False)
    staff_confirmed_told: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    otp_challenge_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)


class PatientLink(BaseAuditModel):
    """A clinic's patient record linked to a person profile, by consent."""

    __tablename__ = "patient_links"
    __table_args__ = (
        CheckConstraint("status IN ('linked','revoked')", name="ck_patient_link_status"),
        CheckConstraint("method IN ('clinic_otp','claim_code','appointment')", name="ck_patient_link_method"),
        # A clinic record links to at most one profile, and a profile to at most one record per clinic
        Index(
            "uq_patient_link_one_active_per_patient", "tenant_id", "patient_id",
            unique=True, postgresql_where=text("status = 'linked'"),
        ),
        Index(
            "uq_patient_link_one_active_per_profile", "tenant_id", "profile_id",
            unique=True, postgresql_where=text("status = 'linked'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    method: Mapped[str] = mapped_column(String(15), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="linked")
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    linked_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    consent_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # When the holder gained access to this clinic's records in the patient portal; null = not visible
    portal_access_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ClaimCode(BaseAuditModel):
    """A code a clinic gives a patient so they can link an existing record later (hashed)."""

    __tablename__ = "identity_claim_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 'link': links an unlinked record (Phase 1). 'portal': gives the holder portal access to an
    # already-linked record, so it is tied to that link.
    purpose: Mapped[str] = mapped_column(String(10), nullable=False, default="link", server_default="link")
    link_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


REQUEST_STATUSES = ("requested", "confirmed", "declined", "cancelled")
REQUEST_WINDOWS = ("morning", "afternoon", "evening", "any")


class AppointmentRequest(BaseAuditModel):
    """A signed-in patient's request for an appointment with a public practitioner (ADR 009 phase 3).

    The clinic sees only `snapshot` (the basic details the patient consented to share when asking), never
    the live profile. Confirming it creates the clinic's patient record (if this person is not linked there
    yet), links it by consent, and books the appointment through the normal appointment rules."""

    __tablename__ = "appointment_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested','confirmed','declined','cancelled')", name="ck_appointment_request_status"
        ),
        CheckConstraint(
            "preferred_window IN ('morning','afternoon','evening','any')", name="ck_appointment_request_window"
        ),
        # One open request per person per clinic
        Index(
            "uq_appointment_request_one_open", "tenant_id", "profile_id",
            unique=True, postgresql_where=text("status = 'requested'"),
        ),
        Index("ix_appointment_requests_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_id: Mapped[str | None] = mapped_column(
        ForeignKey("practitioner_listings.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("person_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="requested", index=True)
    preferred_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferred_window: Mapped[str] = mapped_column(String(10), nullable=False, default="any")
    reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    patient_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    appointment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(String(10), nullable=True)  # patient | clinic
