"""Database models."""

from app.shared.models.base import Base, BaseAuditModel, TenantScopedModel
from app.shared.models.tenant import Tenant, User, UserSession
from app.shared.models.doctor import DoctorDegree, DoctorTraining
from app.shared.models.geographic import Division, District, Upazila
from app.shared.models.patient import Patient, PatientTag, PatientDiagnosis
from app.shared.models.prescription import Prescription, PrescriptionItem
from app.shared.models.payment import Payment, Invoice
from app.shared.models.medicine import Medicine, MedicineSymptom
from app.shared.models.library import (
    Book,
    Chapter,
    Section,
    Embedding,
    ReadingProgress,
    Bookmark,
    Highlight,
)
from app.shared.models.integration import (
    IntegrationProvider,
    TenantIntegration,
    IntegrationLog,
)
from app.shared.models.translation import Translation
from app.shared.models.usage import UsageTracking

__all__ = [
    "Base",
    "BaseAuditModel",
    "TenantScopedModel",
    "Tenant",
    "User",
    "UserSession",
    "DoctorDegree",
    "DoctorTraining",
    "Division",
    "District",
    "Upazila",
    "Patient",
    "PatientTag",
    "PatientDiagnosis",
    "Prescription",
    "PrescriptionItem",
    "Payment",
    "Invoice",
    "Medicine",
    "MedicineSymptom",
    "Book",
    "Chapter",
    "Section",
    "Embedding",
    "ReadingProgress",
    "Bookmark",
    "Highlight",
    "IntegrationProvider",
    "TenantIntegration",
    "IntegrationLog",
    "Translation",
    "UsageTracking",
]
