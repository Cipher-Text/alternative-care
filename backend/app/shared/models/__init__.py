"""Database models."""

from app.shared.models.base import Base, BaseAuditModel, TenantScopedModel, GlobalCatalogModel
from app.shared.models.tenant import Tenant, User, UserSession
from app.shared.models.doctor import DoctorDegree, DoctorTraining
from app.shared.models.institution import Institution
from app.shared.models.pharmacy import Pharmacy
from app.shared.models.article import Article
from app.shared.models.identity import (
    AppointmentRequest,
    ClaimCode,
    ConsentEvent,
    DataShare,
    DataShareAccess,
    OtpChallenge,
    PatientLink,
    PersonAccount,
    PersonProfile,
)
from app.shared.models.contact import ContactMessage
from app.shared.models.marketing import FacebookFeatureRequest
from app.shared.models.billing import BillingOrder, CreditPack
from app.shared.models.credits import CreditBalance, CreditLedger
from app.shared.models.directory import ContactRequest, ListingEvent, PractitionerListing
from app.shared.models.geographic import Division, District, Upazila
from app.shared.models.case_taking import PatientCaseProfile, VisitAssessment
from app.shared.models.patient import Patient, PatientTag, PatientDiagnosis, PatientHealthProfile
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
from app.shared.models.plan import (
    Plan,
    PlanEntitlement,
    TenantEntitlementOverride,
    PlanAuditLog,
)

__all__ = [
    "Plan",
    "PlanEntitlement",
    "TenantEntitlementOverride",
    "PlanAuditLog",
    "Base",
    "BaseAuditModel",
    "TenantScopedModel",
    "GlobalCatalogModel",
    "Tenant",
    "User",
    "UserSession",
    "DoctorDegree",
    "DoctorTraining",
    "Institution",
    "Pharmacy",
    "AppointmentRequest",
    "Article",
    "ClaimCode",
    "ConsentEvent",
    "DataShare",
    "DataShareAccess",
    "OtpChallenge",
    "PatientLink",
    "PersonAccount",
    "PersonProfile",
    "ContactMessage",
    "FacebookFeatureRequest",
    "BillingOrder",
    "CreditPack",
    "CreditBalance",
    "CreditLedger",
    "ContactRequest",
    "ListingEvent",
    "PractitionerListing",
    "Division",
    "District",
    "Upazila",
    "Patient",
    "PatientTag",
    "PatientDiagnosis",
    "PatientHealthProfile",
    "PatientCaseProfile",
    "VisitAssessment",
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
