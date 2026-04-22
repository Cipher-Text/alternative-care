"""Pydantic schemas for API requests and responses."""

from app.shared.schemas.appointment import (
    AppointmentBase,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentCancel,
    AppointmentResponse,
    AppointmentListItem,
    VisitBase,
    VisitCreate,
    VisitUpdate,
    VisitResponse,
    VisitListItem,
)
from app.shared.schemas.symptom import (
    SymptomBase,
    SymptomCreate,
    SymptomUpdate,
    SymptomResponse,
    SymptomWithAliases,
    SymptomSearchResult,
    SymptomAliasBase,
    SymptomAliasCreate,
    SymptomAliasUpdate,
    SymptomAliasResponse,
    MedicineSymptomMappingBase,
    MedicineSymptomMappingCreate,
    MedicineSymptomMappingUpdate,
    MedicineSymptomMappingResponse,
)

__all__ = [
    # Appointments
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentCancel",
    "AppointmentResponse",
    "AppointmentListItem",
    # Visits
    "VisitBase",
    "VisitCreate",
    "VisitUpdate",
    "VisitResponse",
    "VisitListItem",
    # Symptoms
    "SymptomBase",
    "SymptomCreate",
    "SymptomUpdate",
    "SymptomResponse",
    "SymptomWithAliases",
    "SymptomSearchResult",
    # Symptom Aliases
    "SymptomAliasBase",
    "SymptomAliasCreate",
    "SymptomAliasUpdate",
    "SymptomAliasResponse",
    # Medicine-Symptom Mappings
    "MedicineSymptomMappingBase",
    "MedicineSymptomMappingCreate",
    "MedicineSymptomMappingUpdate",
    "MedicineSymptomMappingResponse",
]
