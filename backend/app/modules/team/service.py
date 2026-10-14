"""Staff and roles (ADR 010, Phases 3 and 4). Only the platform changes them; a clinic that needs a change asks AltCare.

One service serves three uses, chosen by who acts and on what:
- a platform user acting on the platform itself (no `target_tenant_id`): platform staff and platform-level roles;
- a platform user acting on one clinic (`target_tenant_id`): that clinic's staff and clinic-level roles. The platform
  is the authority over clinic permissions, so the no-escalation check does not apply to it;
- a clinic user: read access to their own clinic's staff, roles and audit trail (the routes expose no writes).

Every rule from the ADR's safety section is enforced here, in the service, not left to the UI:

1. No escalation: nobody puts into a role, or hands to a person, a permission they do not hold themselves.
2. A role holds permissions of its own level only (clinic roles clinic-level, platform roles platform-level).
3. Nobody is locked out: the platform always keeps someone who can manage roles (`roles.manage_global`), and a clinic
   always keeps at least one active practitioner (someone who can issue prescriptions).
4. Sensitive permissions need an explicit acknowledgement.
5. Every change is written to `role_audit_log`.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permission_cache
from app.core.config import settings
from app.core.dependencies import CurrentUser, get_permissions
from app.core.entitlements import EntitlementService
from app.core.permissions import BY_KEY, PermissionRuleError, check_can_grant, validate_role_permissions
from app.core.security import generate_secure_token, get_password_hash, hash_token
from app.core.system_email import send_system_email_task
from app.modules.team.schemas import (
    AuditItem,
    AuditPage,
    MemberInvite,
    MemberItem,
    PermissionItem,
    RoleBrief,
    RoleCreate,
    RoleItem,
    RoleUpdate,
)
from app.shared.models.rbac import PermissionRow, Role, RoleAuditLog, RolePermission, UserRole
from app.shared.models.tenant import Tenant, User, UserSession

MAX_CLINIC_ROLES = 20
INVITE_TOKEN_TTL = timedelta(days=3)
CLINIC_OWNER_PERMISSION = "prescriptions.issue"
PLATFORM_OWNER_PERMISSION = "roles.manage_global"


def _error(code: int, key: str, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail={"code": key, "message": message})


async def count_active_owners(db: AsyncSession, tenant_id: str | None, permission: str) -> int:
    """Active people at this level (one clinic, or the platform when `tenant_id` is None) who hold `permission` right now."""
    level = User.tenant_id.is_(None) if tenant_id is None else User.tenant_id == tenant_id
    result = await db.execute(
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .where(level, User.is_active.is_(True), Role.is_active.is_(True), RolePermission.permission_key == permission)
    )
    return int(result.scalar_one())


class TeamService:
    def __init__(self, db: AsyncSession, actor: CurrentUser, target_tenant_id: str | None = None):
        self.db = db
        self.actor = actor
        # A platform user acting on one clinic; clinic users only ever act on their own
        self.acting_for_clinic = actor.tenant_id is None and target_tenant_id is not None
        self.tenant_id = target_tenant_id if self.acting_for_clinic else actor.tenant_id
        self.is_platform = actor.tenant_id is None and target_tenant_id is None
        self.scope = "platform" if self.is_platform else "tenant"
        self.owner_permission = PLATFORM_OWNER_PERMISSION if self.is_platform else CLINIC_OWNER_PERMISSION
        self._actor_permissions: frozenset[str] | None = None

    # ------------------------------------------------------------------ helpers

    async def _held(self) -> frozenset[str]:
        if self._actor_permissions is None:
            if self.acting_for_clinic:
                # The platform decides what a clinic may hold: every clinic-level permission is grantable by it
                self._actor_permissions = frozenset(k for k, p in BY_KEY.items() if p.scope == "tenant")
            else:
                self._actor_permissions = await get_permissions(self.actor, self.db)
        return self._actor_permissions

    async def _audit(self, action: str, *, role_id: str | None = None, user_id: str | None = None, before=None, after=None) -> None:
        self.db.add(
            RoleAuditLog(
                id=str(uuid.uuid4()),
                actor_user_id=self.actor.user_id,
                tenant_id=self.tenant_id,
                role_id=role_id,
                user_id=user_id,
                action=action,
                before=before,
                after=after,
            )
        )

    def _member_level(self):
        """Whose staff this is: the platform's (no clinic) or one clinic's."""
        return User.tenant_id.is_(None) if self.is_platform else User.tenant_id == self.tenant_id

    def _visible_roles(self):
        """Roles that can be seen and used here. A clinic: the global clinic-level templates and its own. The platform:
        the global platform-level roles."""
        own = Role.tenant_id.is_(None) if self.is_platform else (Role.tenant_id.is_(None)) | (Role.tenant_id == self.tenant_id)
        return select(Role).where(Role.scope == self.scope, Role.is_active.is_(True), own)

    async def _role_permissions(self, role_ids: list[str]) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {r: set() for r in role_ids}
        if role_ids:
            rows = await self.db.execute(select(RolePermission.role_id, RolePermission.permission_key).where(RolePermission.role_id.in_(role_ids)))
            for role_id, key in rows.all():
                out[role_id].add(key)
        return out

    async def _get_role(self, role_id: str) -> Role:
        role = (await self.db.execute(self._visible_roles().where(Role.id == role_id))).scalar_one_or_none()
        if role is None:
            raise _error(404, "role_not_found", "Role not found")
        return role

    async def _get_member(self, user_id: str) -> User:
        user = (await self.db.execute(select(User).where(User.id == user_id, self._member_level()))).scalar_one_or_none()
        if user is None:
            raise _error(404, "member_not_found", "Team member not found")
        return user

    async def _check_assignable(self, role_ids: list[str]) -> list[Role]:
        """Every role exists for this clinic, and the actor holds everything it carries (rule 1)."""
        unique = list(dict.fromkeys(role_ids))
        roles = []
        for role_id in unique:
            roles.append(await self._get_role(role_id))
        perms = await self._role_permissions(unique)
        held = await self._held()
        for role in roles:
            if not perms[role.id] <= held:
                raise _error(403, "cannot_assign_role", f"You cannot assign '{role.name_en}': it carries permissions you do not hold.")
        return roles

    def _check_permissions_input(self, keys: list[str], held: frozenset[str], acknowledge_sensitive: bool, already: set[str] | None = None) -> set[str]:
        wanted = set(keys)
        try:
            validate_role_permissions(self.scope, wanted)
        except PermissionRuleError as exc:
            raise _error(422, "invalid_permissions", str(exc)) from exc
        try:
            check_can_grant(held, wanted)
        except PermissionRuleError as exc:
            raise _error(403, "cannot_grant", str(exc)) from exc
        newly_sensitive = sorted(k for k in wanted - (already or set()) if BY_KEY[k].sensitive)
        if newly_sensitive and not acknowledge_sensitive:
            raise _error(
                422,
                "sensitive_not_acknowledged",
                f"These permissions are sensitive and need an explicit confirmation: {', '.join(newly_sensitive)}",
            )
        return wanted

    async def _count_owners(self) -> int:
        """Active people at this level who can manage the roles right now."""
        return await count_active_owners(self.db, self.tenant_id, self.owner_permission)

    async def _require_an_owner(self) -> None:
        """Rule 3. Called after a change has been flushed, inside the transaction, so a violation rolls everything back."""
        if await self._count_owners() == 0:
            await self.db.rollback()
            message = (
                "The platform must keep at least one active person who can manage roles and staff."
                if self.is_platform
                else "The clinic must keep at least one active practitioner (someone who can issue prescriptions)."
            )
            raise _error(409, "last_owner", message)

    async def _refresh_legacy_role(self, user: User, *, check_seat: bool = True) -> None:
        """`users.role` stays during the transition (ADR 010, Phase 4 retires it). Whoever can issue prescriptions is
        a 'doctor' there, which is also what a practitioner seat counts. Written with a plain UPDATE on purpose: the ORM
        hook that mirrors `users.role` into `user_roles` must not run, or it would replace the roles just chosen."""
        perms = await self._effective_of(user.id)
        if self.is_platform:
            legacy = "admin" if PLATFORM_OWNER_PERMISSION in perms else "operator"
        else:
            legacy = "doctor" if "prescriptions.issue" in perms else "receptionist"
        if legacy == user.role:
            return
        if legacy == "doctor" and check_seat and user.is_active:
            await EntitlementService(self.db).check_limit(self.tenant_id, "max_seats")
        await self.db.execute(update(User).where(User.id == user.id).values(role=legacy))
        await self.db.refresh(user)

    async def _effective_of(self, user_id: str) -> set[str]:
        rows = await self.db.execute(
            select(RolePermission.permission_key)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.is_active.is_(True))
        )
        return set(rows.scalars().all())

    async def _replace_roles(self, user_id: str, role_ids: list[str]) -> None:
        await self.db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        for role_id in dict.fromkeys(role_ids):
            await self.db.execute(insert(UserRole).values(user_id=user_id, role_id=role_id, granted_by=self.actor.user_id))
        permission_cache.invalidate_user(user_id)

    async def _roles_of(self, user_ids: list[str]) -> dict[str, list[RoleBrief]]:
        out: dict[str, list[RoleBrief]] = {u: [] for u in user_ids}
        if not user_ids:
            return out
        rows = await self.db.execute(
            select(UserRole.user_id, Role).join(Role, Role.id == UserRole.role_id).where(UserRole.user_id.in_(user_ids)).order_by(Role.is_system.desc(), Role.name_en)
        )
        for user_id, role in rows.all():
            out[user_id].append(RoleBrief(id=role.id, key=role.key, name_en=role.name_en, name_bn=role.name_bn, is_system=role.is_system))
        return out

    # ------------------------------------------------------------------ catalogue

    async def list_permissions(self) -> list[PermissionItem]:
        held = await self._held()
        rows = (await self.db.execute(select(PermissionRow).where(PermissionRow.scope == self.scope).order_by(PermissionRow.module, PermissionRow.key))).scalars().all()
        return [
            PermissionItem(
                key=p.key,
                module=p.module,
                description_en=p.description_en,
                description_bn=p.description_bn,
                is_sensitive=p.is_sensitive,
                can_grant=p.key in held,
            )
            for p in rows
        ]

    # ------------------------------------------------------------------ roles

    async def list_roles(self) -> list[RoleItem]:
        roles = (await self.db.execute(self._visible_roles().order_by(Role.is_system.desc(), Role.name_en))).scalars().all()
        ids = [r.id for r in roles]
        perms = await self._role_permissions(ids)
        counts = {
            role_id: n
            for role_id, n in (
                await self.db.execute(
                    select(UserRole.role_id, func.count())
                    .join(User, User.id == UserRole.user_id)
                    .where(UserRole.role_id.in_(ids), self._member_level(), User.is_active.is_(True))
                    .group_by(UserRole.role_id)
                )
            ).all()
        }
        held = await self._held()
        return [
            RoleItem(
                id=r.id,
                key=r.key,
                name_en=r.name_en,
                name_bn=r.name_bn,
                is_system=r.is_system,
                based_on_role_id=r.based_on_role_id,
                permissions=sorted(perms[r.id]),
                member_count=counts.get(r.id, 0),
                can_edit=(not r.is_system) and perms[r.id] <= held,
                can_assign=perms[r.id] <= held,
            )
            for r in roles
        ]

    async def create_role(self, data: RoleCreate) -> RoleItem:
        held = await self._held()
        keys = self._check_permissions_input(data.permissions, held, data.acknowledge_sensitive)
        if data.based_on_role_id:
            await self._get_role(data.based_on_role_id)

        own = Role.tenant_id.is_(None) if self.is_platform else Role.tenant_id == self.tenant_id
        existing = (await self.db.execute(select(func.count()).select_from(Role).where(own, Role.is_system.is_(False), Role.scope == self.scope))).scalar_one()
        if existing >= MAX_CLINIC_ROLES:
            raise _error(409, "too_many_roles", f"At most {MAX_CLINIC_ROLES} custom roles are allowed.")

        name_en = data.name_en.strip()
        taken = (await self.db.execute(select(func.count()).select_from(self._visible_roles().where(func.lower(Role.name_en) == name_en.lower()).subquery()))).scalar_one()
        if taken:
            raise _error(409, "role_name_taken", "A role with this name already exists.")

        slug = re.sub(r"[^a-z0-9]+", "-", name_en.lower()).strip("-")[:30] or "role"
        key = f"custom-{slug}-{uuid.uuid4().hex[:6]}"
        role = Role(
            id=str(uuid.uuid4()),
            key=key,
            name_en=name_en,
            name_bn=(data.name_bn or name_en).strip(),
            scope=self.scope,
            tenant_id=self.tenant_id,
            is_system=False,
            based_on_role_id=data.based_on_role_id,
            is_active=True,
            created_by=self.actor.user_id,
            updated_by=self.actor.user_id,
        )
        self.db.add(role)
        await self.db.flush()
        for permission_key in sorted(keys):
            self.db.add(RolePermission(role_id=role.id, permission_key=permission_key))
        await self._audit("role_created", role_id=role.id, after={"name": name_en, "permissions": sorted(keys)})
        await self.db.commit()
        return next(r for r in await self.list_roles() if r.id == role.id)

    async def _editable_role(self, role_id: str) -> tuple[Role, set[str]]:
        role = await self._get_role(role_id)
        if role.is_system or role.tenant_id != self.tenant_id:
            raise _error(403, "system_role", "System roles cannot be changed by a clinic. Copy it to make your own.")
        current = (await self._role_permissions([role.id]))[role.id]
        if not current <= await self._held():
            raise _error(403, "cannot_edit_role", "This role carries permissions you do not hold, so you cannot change it.")
        return role, current

    async def update_role(self, role_id: str, data: RoleUpdate) -> RoleItem:
        role, current = await self._editable_role(role_id)
        before = {"name": role.name_en, "permissions": sorted(current)}
        if data.name_en is not None:
            role.name_en = data.name_en.strip()
        if data.name_bn is not None:
            role.name_bn = data.name_bn.strip() or role.name_en
        if data.permissions is not None:
            keys = self._check_permissions_input(data.permissions, await self._held(), data.acknowledge_sensitive, already=current)
            await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
            for permission_key in sorted(keys):
                self.db.add(RolePermission(role_id=role.id, permission_key=permission_key))
        role.updated_by = self.actor.user_id
        await self.db.flush()
        await self._audit(
            "role_updated",
            role_id=role.id,
            before=before,
            after={"name": role.name_en, "permissions": sorted(data.permissions) if data.permissions is not None else sorted(current)},
        )
        await self._require_an_owner()
        # Everyone holding the role may have gained or lost the ability to prescribe: their legacy role follows
        for member in await self._members_with_role(role.id):
            await self._refresh_legacy_role(member, check_seat=False)
        await self.db.commit()
        permission_cache.invalidate_all()
        return next(r for r in await self.list_roles() if r.id == role.id)

    async def delete_role(self, role_id: str) -> None:
        role, current = await self._editable_role(role_id)
        in_use = (await self.db.execute(select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id))).scalar_one()
        if in_use:
            raise _error(409, "role_in_use", f"{in_use} team member(s) still hold this role. Change their roles first.")
        await self._audit("role_deleted", role_id=role.id, before={"name": role.name_en, "permissions": sorted(current)})
        await self.db.delete(role)
        await self.db.commit()
        permission_cache.invalidate_all()

    async def _members_with_role(self, role_id: str) -> list[User]:
        return list(
            (await self.db.execute(select(User).join(UserRole, UserRole.user_id == User.id).where(UserRole.role_id == role_id, self._member_level()))).scalars().all()
        )

    # ------------------------------------------------------------------ members

    async def list_members(self) -> list[MemberItem]:
        users = (await self.db.execute(select(User).where(self._member_level()).order_by(User.is_active.desc(), User.full_name))).scalars().all()
        roles = await self._roles_of([u.id for u in users])
        held = await self._held()
        role_perms = await self._role_permissions(list({r.id for rs in roles.values() for r in rs}))
        return [
            MemberItem(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                phone=u.phone,
                is_active=u.is_active,
                is_email_verified=u.is_email_verified,
                last_login_at=u.last_login_at,
                is_you=u.id == self.actor.user_id,
                roles=roles[u.id],
                can_manage=all(role_perms[r.id] <= held for r in roles[u.id]),
            )
            for u in users
        ]

    async def _member_item(self, user_id: str) -> MemberItem:
        return next(m for m in await self.list_members() if m.id == user_id)

    async def invite_member(self, data: MemberInvite) -> MemberItem:
        roles = await self._check_assignable(data.role_ids)
        email = data.email.lower()
        if (await self.db.execute(select(User).where(func.lower(User.email) == email))).scalar_one_or_none():
            raise _error(400, "email_taken", "Email already registered")

        perms = await self._role_permissions([r.id for r in roles])
        will_prescribe = (not self.is_platform) and any("prescriptions.issue" in p for p in perms.values())
        if will_prescribe:
            await EntitlementService(self.db).check_limit(self.tenant_id, "max_seats")
        if self.is_platform:
            legacy_role = "admin" if any(PLATFORM_OWNER_PERMISSION in p for p in perms.values()) else "operator"
        else:
            legacy_role = "doctor" if will_prescribe else "receptionist"

        raw_token = generate_secure_token()
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            email=email,
            # Nobody knows this password; the person sets their own through the emailed link
            password_hash=get_password_hash(generate_secure_token()),
            role=legacy_role,
            full_name=data.full_name.strip(),
            phone=data.phone,
            language=data.language,
            is_active=True,
            is_email_verified=False,
            password_reset_token_hash=hash_token(raw_token),
            password_reset_expires_at=datetime.now(timezone.utc) + INVITE_TOKEN_TTL,
            created_by=self.actor.user_id,
            updated_by=self.actor.user_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self._replace_roles(user.id, [r.id for r in roles])
        await self._audit("member_invited", user_id=user.id, after={"email": email, "roles": [r.name_en for r in roles]})
        await self.db.commit()

        if self.is_platform:
            clinic = "the AltCare platform team"
        else:
            clinic = (await self.db.execute(select(Tenant.clinic_name).where(Tenant.id == self.tenant_id))).scalar_one_or_none() or "your clinic"
        link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        send_system_email_task.delay(
            recipient=user.email,
            subject=f"You have been added to {clinic} on AltCare",
            body_html=(
                f"<p>Hi {user.full_name},</p>"
                f"<p>You have been added to <strong>{clinic}</strong> on AltCare. Set your password with the link below. "
                f"It works for 3 days.</p><p><a href=\"{link}\">{link}</a></p>"
            ),
            body_text=f"Hi {user.full_name},\n\nYou have been added to {clinic} on AltCare. Set your password (the link works for 3 days):\n\n{link}\n",
        )
        return await self._member_item(user.id)

    async def set_member_roles(self, user_id: str, role_ids: list[str]) -> MemberItem:
        user = await self._get_member(user_id)
        new_roles = await self._check_assignable(role_ids)
        old = (await self._roles_of([user.id]))[user.id]
        old_ids, new_ids = {r.id for r in old}, {r.id for r in new_roles}
        # Removing a role is as much a use of its permissions as giving it: you cannot strip what you could not hold
        removed = old_ids - new_ids
        if removed:
            perms = await self._role_permissions(list(removed))
            held = await self._held()
            for role in old:
                if role.id in removed and not perms[role.id] <= held:
                    raise _error(403, "cannot_remove_role", f"You cannot remove '{role.name_en}': it carries permissions you do not hold.")
        if old_ids == new_ids:
            return await self._member_item(user.id)

        await self._replace_roles(user.id, [r.id for r in new_roles])
        await self.db.flush()
        await self._audit(
            "roles_assigned",
            user_id=user.id,
            before={"roles": sorted(r.name_en for r in old)},
            after={"roles": sorted(r.name_en for r in new_roles)},
        )
        await self._require_an_owner()
        await self._refresh_legacy_role(user)
        await self.db.commit()
        permission_cache.invalidate_user(user.id)
        return await self._member_item(user.id)

    async def set_member_active(self, user_id: str, active: bool) -> MemberItem:
        user = await self._get_member(user_id)
        if user.id == self.actor.user_id and not active:
            raise _error(400, "cannot_deactivate_self", "You cannot deactivate your own account.")
        if user.is_active == active:
            return await self._member_item(user.id)
        # Whoever the actor may not manage (their roles carry more than the actor holds) cannot be switched off by them
        member = await self._member_item(user.id)
        if not member.can_manage:
            raise _error(403, "cannot_manage_member", "This person holds permissions you do not, so you cannot change their access.")

        if active and not self.is_platform and "prescriptions.issue" in await self._effective_of(user.id):
            await EntitlementService(self.db).check_limit(self.tenant_id, "max_seats")
        user.is_active = active
        user.updated_by = self.actor.user_id
        if not active:
            # Sign them out everywhere now
            user.token_version += 1
            for session in (await self.db.execute(select(UserSession).where(UserSession.user_id == user.id, UserSession.is_revoked.is_(False)))).scalars().all():
                session.is_revoked = True
                session.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._audit("member_deactivated" if not active else "member_activated", user_id=user.id)
        await self._require_an_owner()
        await self.db.commit()
        permission_cache.invalidate_user(user.id)
        return await self._member_item(user.id)

    # ------------------------------------------------------------------ audit

    async def list_audit(self, limit: int = 50, offset: int = 0, level: str = "all") -> AuditPage:
        """A clinic reads its own trail. The platform reads everything: `level` narrows it to the platform's own changes
        ("platform") or to those made inside clinics ("clinic")."""
        if self.is_platform:
            conditions = {"platform": [RoleAuditLog.tenant_id.is_(None)], "clinic": [RoleAuditLog.tenant_id.is_not(None)]}.get(level, [])
        else:
            conditions = [RoleAuditLog.tenant_id == self.tenant_id]
        total = (await self.db.execute(select(func.count()).select_from(RoleAuditLog).where(*conditions))).scalar_one()
        logs = (
            (await self.db.execute(select(RoleAuditLog).where(*conditions).order_by(RoleAuditLog.created_at.desc()).limit(limit).offset(offset)))
            .scalars()
            .all()
        )
        user_ids = {i for log in logs for i in (log.actor_user_id, log.user_id) if i}
        names = {}
        if user_ids:
            names = dict((await self.db.execute(select(User.id, User.full_name).where(User.id.in_(user_ids)))).all())
        role_ids = {log.role_id for log in logs if log.role_id}
        role_names = {}
        if role_ids:
            role_names = dict((await self.db.execute(select(Role.id, Role.name_en).where(Role.id.in_(role_ids)))).all())
        clinic_names = {}
        tenant_ids = {log.tenant_id for log in logs if log.tenant_id} if self.is_platform else set()
        if tenant_ids:
            clinic_names = dict((await self.db.execute(select(Tenant.id, Tenant.clinic_name).where(Tenant.id.in_(tenant_ids)))).all())
        return AuditPage(
            total=int(total),
            items=[
                AuditItem(
                    id=log.id,
                    created_at=log.created_at,
                    action=log.action,
                    actor_name=names.get(log.actor_user_id),
                    member_name=names.get(log.user_id),
                    # A deleted role is gone from `roles`; its name survives in the audit entry
                    role_name=role_names.get(log.role_id) or (log.before or {}).get("name"),
                    clinic_name=clinic_names.get(log.tenant_id),
                    before=log.before,
                    after=log.after,
                )
                for log in logs
            ],
        )
