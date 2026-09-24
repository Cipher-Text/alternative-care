"""Database models."""

from app.shared.models.base import Base, BaseAuditModel, TenantScopedModel, GlobalCatalogModel
from app.shared.models.tenant import Tenant, User, UserSession
from app.shared.models.doctor import DoctorDegree, DoctorTraining
from app.shared.models.geographic import Division, District, Upazila
from app.shared.models.patient import Patient, PatientTag, PatientDiagnosis
from app.shared.models.prescription import Prescription, PrescriptionItem
from app.shared.models.payment import Payment, Invoice
from app.shared.models.medicine import Medicine, MedicineAlias
from app.shared.models.symptom import (
    Symptom,
    SymptomAlias,
    MedicineSymptomMapping,
)
from app.shared.models.appointment import Appointment, Visit
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
    "GlobalCatalogModel",
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
    "MedicineAlias",
    "Symptom",
    "SymptomAlias",
    "MedicineSymptomMapping",
    "Appointment",
    "Visit",
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
