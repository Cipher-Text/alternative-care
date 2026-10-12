"""Reading and saving case-taking answers, tenant-scoped."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.case_taking import SCHEMA_VERSION, CaseValidationError, System, validate
from app.shared.case_taking.systems import SYSTEMS
from app.shared.models import Patient, PatientCaseProfile, Visit, VisitAssessment


def get_system(key: str) -> System:
    system = SYSTEMS.get(key)
    if system is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown case-taking system")
    return system


def _invalid(exc: CaseValidationError) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": "invalid_case_data", "message": "Some answers are not valid.", "errors": exc.errors},
    )


class CaseTakingService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def _patient(self, patient_id: str) -> Patient:
        patient = (
            await self.db.execute(select(Patient).where(Patient.id == patient_id, Patient.tenant_id == self.tenant_id))
        ).scalar_one_or_none()
        if patient is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
        return patient

    async def _visit(self, visit_id: str) -> Visit:
        visit = (
            await self.db.execute(select(Visit).where(Visit.id == visit_id, Visit.tenant_id == self.tenant_id))
        ).scalar_one_or_none()
        if visit is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Visit not found")
        return visit

    @staticmethod
    def _out(row, key: str, owner: dict) -> dict:
        return {
            **owner,
            "system": key,
            "data": row.data if row is not None else {},
            "schema_version": row.schema_version if row is not None else SCHEMA_VERSION,
            "exists": row is not None,
            "updated_at": row.updated_at if row is not None else None,
        }

    # ----- patient profile ------------------------------------------------------------------

    async def _profile_row(self, patient_id: str, key: str) -> PatientCaseProfile | None:
        return (
            await self.db.execute(
                select(PatientCaseProfile).where(
                    PatientCaseProfile.tenant_id == self.tenant_id,
                    PatientCaseProfile.patient_id == patient_id,
                    PatientCaseProfile.system == key,
                )
            )
        ).scalar_one_or_none()

    async def get_profile(self, patient_id: str, key: str) -> dict:
        get_system(key)
        await self._patient(patient_id)
        return self._out(await self._profile_row(patient_id, key), key, {"patient_id": patient_id})

    async def save_profile(self, patient_id: str, key: str, data: dict, user_id: str) -> dict:
        system = get_system(key)
        await self._patient(patient_id)
        try:
            cleaned = validate(system, "patient", data)
        except CaseValidationError as exc:
            raise _invalid(exc) from exc
        row = await self._profile_row(patient_id, key)
        if row is None:
            row = PatientCaseProfile(
                id=str(uuid4()), tenant_id=self.tenant_id, patient_id=patient_id, system=key, created_by=user_id
            )
            self.db.add(row)
        row.data, row.schema_version = cleaned, SCHEMA_VERSION
        row.updated_by, row.updated_at = user_id, datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return self._out(row, key, {"patient_id": patient_id})

    # ----- visit assessment -----------------------------------------------------------------

    async def _assessment_row(self, visit_id: str, key: str) -> VisitAssessment | None:
        return (
            await self.db.execute(
                select(VisitAssessment).where(
                    VisitAssessment.tenant_id == self.tenant_id,
                    VisitAssessment.visit_id == visit_id,
                    VisitAssessment.system == key,
                )
            )
        ).scalar_one_or_none()

    async def get_assessment(self, visit_id: str, key: str) -> dict:
        get_system(key)
        visit = await self._visit(visit_id)
        return self._out(
            await self._assessment_row(visit_id, key), key, {"visit_id": visit_id, "patient_id": visit.patient_id}
        )

    async def save_assessment(self, visit_id: str, key: str, data: dict, user_id: str) -> dict:
        system = get_system(key)
        visit = await self._visit(visit_id)
        try:
            cleaned = validate(system, "visit", data)
        except CaseValidationError as exc:
            raise _invalid(exc) from exc
        row = await self._assessment_row(visit_id, key)
        if row is None:
            row = VisitAssessment(
                id=str(uuid4()), tenant_id=self.tenant_id, visit_id=visit_id, patient_id=visit.patient_id,
                system=key, created_by=user_id,
            )
            self.db.add(row)
        row.data, row.schema_version = cleaned, SCHEMA_VERSION
        row.updated_by, row.updated_at = user_id, datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(row)
        return self._out(row, key, {"visit_id": visit_id, "patient_id": visit.patient_id})
