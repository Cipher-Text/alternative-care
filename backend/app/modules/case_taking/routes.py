"""Case-taking endpoints: the form definitions, a patient's case profile, and a visit's assessment."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.case_taking.service import CaseTakingService, get_system
from app.shared.case_taking import definitions

router = APIRouter()


class CaseAnswers(BaseModel):
    """The whole form is sent each time (replace, not patch). Keys and values are checked against the registry."""

    data: dict[str, Any]


class CaseRecord(BaseModel):
    system: str
    data: dict[str, Any]
    schema_version: int
    exists: bool
    updated_at: datetime | None = None
    patient_id: str
    visit_id: str | None = None


def get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CaseTakingService:
    if not current_user.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Platform users cannot manage patient records.")
    return CaseTakingService(db, current_user.tenant_id)


Service = Annotated[CaseTakingService, Depends(get_service)]
User = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/{system}")
async def get_definitions(system: str, user: User):  # noqa: ARG001
    """The fields, their groups and choices for one system (labels are the frontend's translations)."""
    return definitions(get_system(system))


@router.get("/patients/{patient_id}/{system}", response_model=CaseRecord)
async def get_patient_case(patient_id: str, system: str, service: Service):
    return await service.get_profile(patient_id, system)


@router.put("/patients/{patient_id}/{system}", response_model=CaseRecord)
async def save_patient_case(patient_id: str, system: str, body: CaseAnswers, service: Service, user: User):
    return await service.save_profile(patient_id, system, body.data, user.user_id)


@router.get("/visits/{visit_id}/{system}", response_model=CaseRecord)
async def get_visit_case(visit_id: str, system: str, service: Service):
    return await service.get_assessment(visit_id, system)


@router.put("/visits/{visit_id}/{system}", response_model=CaseRecord)
async def save_visit_case(visit_id: str, system: str, body: CaseAnswers, service: Service, user: User):
    return await service.save_assessment(visit_id, system, body.data, user.user_id)
