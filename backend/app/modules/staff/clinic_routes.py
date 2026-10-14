"""The platform manages a clinic's staff and roles (ADR 010): adding staff, creating clinic roles, assigning roles,
switching access on or off. Looking needs `tenants.read`, changing needs `clinic_roles.manage`.

Clinics cannot do this themselves. A clinic that needs a change contacts AltCare."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.team.schemas import (
    AuditPage,
    MemberInvite,
    MemberItem,
    MemberRolesUpdate,
    MemberStatusUpdate,
    PermissionItem,
    RoleCreate,
    RoleItem,
    RoleUpdate,
)
from app.modules.team.service import TeamService
from app.shared.models.tenant import Tenant

router = APIRouter()


async def get_clinic_team_service(
    tenant_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TeamService:
    if current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform staff can manage a clinic's team")
    if (await db.execute(select(Tenant.id).where(Tenant.id == tenant_id))).scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    return TeamService(db, current_user, target_tenant_id=tenant_id)


Service = Annotated[TeamService, Depends(get_clinic_team_service)]


@router.get("/permissions", response_model=list[PermissionItem], summary="Permissions a clinic role can carry")
async def list_permissions(service: Service):
    return await service.list_permissions()


@router.get("/roles", response_model=list[RoleItem], summary="Roles this clinic can use")
async def list_roles(service: Service):
    return await service.list_roles()


@router.post("/roles", response_model=RoleItem, status_code=status.HTTP_201_CREATED, summary="Create a role for this clinic")
async def create_role(data: RoleCreate, service: Service):
    return await service.create_role(data)


@router.patch("/roles/{role_id}", response_model=RoleItem, summary="Rename a clinic role or change its permissions")
async def update_role(role_id: str, data: RoleUpdate, service: Service):
    return await service.update_role(role_id, data)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a clinic role nobody holds")
async def delete_role(role_id: str, service: Service):
    await service.delete_role(role_id)


@router.get("/members", response_model=list[MemberItem], summary="The clinic's staff and their roles")
async def list_members(service: Service):
    return await service.list_members()


@router.post("/members", response_model=MemberItem, status_code=status.HTTP_201_CREATED, summary="Add a staff member to this clinic by email")
async def invite_member(data: MemberInvite, service: Service):
    return await service.invite_member(data)


@router.put("/members/{user_id}/roles", response_model=MemberItem, summary="Set a clinic staff member's roles")
async def set_member_roles(user_id: str, data: MemberRolesUpdate, service: Service):
    return await service.set_member_roles(user_id, data.role_ids)


@router.patch("/members/{user_id}/status", response_model=MemberItem, summary="Switch a clinic staff member's access on or off")
async def set_member_status(user_id: str, data: MemberStatusUpdate, service: Service):
    return await service.set_member_active(user_id, data.is_active)


@router.get("/audit", response_model=AuditPage, summary="Role and access changes in this clinic")
async def list_audit(service: Service, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return await service.list_audit(limit, offset)
