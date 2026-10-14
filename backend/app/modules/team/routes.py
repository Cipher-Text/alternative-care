"""A clinic's view of its own team: staff, roles and the audit trail (ADR 010). Read only, needs `team.read`.

Adding staff, creating roles and assigning them is done by the platform (`/admin/tenants/{id}/team`, see
app/modules/staff). A clinic that needs a change asks AltCare."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.team.schemas import AuditPage, MemberItem, PermissionItem, RoleItem
from app.modules.team.service import TeamService

router = APIRouter()


def get_team_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TeamService:
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clinic users have a clinic team")
    return TeamService(db, current_user)


Service = Annotated[TeamService, Depends(get_team_service)]


@router.get("/permissions", response_model=list[PermissionItem], summary="Permissions a clinic role can carry")
async def list_permissions(service: Service):
    return await service.list_permissions()


@router.get("/roles", response_model=list[RoleItem], summary="Roles this clinic uses")
async def list_roles(service: Service):
    return await service.list_roles()


@router.get("/members", response_model=list[MemberItem], summary="The clinic's staff and their roles")
async def list_members(service: Service):
    return await service.list_members()


@router.get("/audit", response_model=AuditPage, summary="Who changed which role or access, and when")
async def list_audit(service: Service, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return await service.list_audit(limit, offset)
