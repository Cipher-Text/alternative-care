"""Roles and permissions at run time (ADR 010): keeping the catalogue in the database, and resolving what a user may do."""

from sqlalchemy import select, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permission_cache
from app.core.permissions import BY_KEY, PERMISSIONS, SYSTEM_ROLES, system_role_id
from app.shared.models.rbac import Role, RolePermission, UserRole


def sync_catalogue(connection: Connection) -> None:
    """Make the database match the code: every permission, the four system roles and their permission sets.

    Idempotent, and safe to run on every deploy. A system role's permissions are reset to the code's set (clinics
    cannot edit system roles; platform-side editing arrives in Phase 4 of ADR 010 and will change this)."""
    for p in PERMISSIONS:
        connection.execute(
            text(
                "INSERT INTO permissions (key, scope, module, description_en, description_bn, is_sensitive) "
                "VALUES (:key, :scope, :module, :en, :bn, :sensitive) "
                "ON CONFLICT (key) DO UPDATE SET scope = EXCLUDED.scope, module = EXCLUDED.module, "
                "description_en = EXCLUDED.description_en, description_bn = EXCLUDED.description_bn, "
                "is_sensitive = EXCLUDED.is_sensitive"
            ),
            {"key": p.key, "scope": p.scope, "module": p.module, "en": p.en, "bn": p.bn, "sensitive": p.sensitive},
        )
    # A permission removed from the code leaves the catalogue (and every role) with it
    connection.execute(text("DELETE FROM permissions WHERE key <> ALL(:keys)"), {"keys": [p.key for p in PERMISSIONS]})

    for role in SYSTEM_ROLES.values():
        role_id = system_role_id(role.key)
        connection.execute(
            text(
                "INSERT INTO roles (id, key, name_en, name_bn, scope, tenant_id, is_system, is_active, created_at) "
                "VALUES (:id, :key, :en, :bn, :scope, NULL, true, true, now()) "
                "ON CONFLICT (id) DO UPDATE SET name_en = EXCLUDED.name_en, name_bn = EXCLUDED.name_bn, "
                "scope = EXCLUDED.scope, is_system = true"
            ),
            {"id": role_id, "key": role.key, "en": role.en, "bn": role.bn, "scope": role.scope},
        )
        connection.execute(
            text("DELETE FROM role_permissions WHERE role_id = :id AND permission_key <> ALL(:keys)"),
            {"id": role_id, "keys": sorted(role.permissions)},
        )
        for key in sorted(role.permissions):
            connection.execute(
                text("INSERT INTO role_permissions (role_id, permission_key) VALUES (:id, :key) ON CONFLICT DO NOTHING"),
                {"id": role_id, "key": key},
            )
    permission_cache.invalidate_all()


async def sync_catalogue_async(db: AsyncSession) -> None:
    await db.run_sync(lambda session: sync_catalogue(session.connection()))


def assign_system_role(connection: Connection, user_id: str, role_key: str) -> None:
    """Give a user the system role named by `users.role`, replacing any other system role they hold.

    A no-op when the role is not one of the four, or the roles table has not been seeded yet."""
    system_ids = [system_role_id(k) for k in SYSTEM_ROLES]
    connection.execute(text("DELETE FROM user_roles WHERE user_id = :u AND role_id = ANY(:ids)"), {"u": user_id, "ids": system_ids})
    if role_key in SYSTEM_ROLES:
        connection.execute(
            text("INSERT INTO user_roles (user_id, role_id, granted_at) SELECT :u, id, now() FROM roles WHERE id = :r ON CONFLICT DO NOTHING"),
            {"u": user_id, "r": system_role_id(role_key)},
        )
    permission_cache.invalidate_user(user_id)


async def effective_permissions(db: AsyncSession, user_id: str, legacy_role: str, platform_user: bool) -> frozenset[str]:
    """Everything this user may do: the union of the permissions of their active roles.

    A user with no `user_roles` rows at all falls back to the system role named by `users.role`, so a missing or
    not-yet-seeded assignment can never lock someone out or, worse, grant too much. Permissions of the wrong level
    (a clinic user holding a platform permission, or the reverse) are dropped."""
    cached = permission_cache.get(user_id)
    if cached is not None:
        return cached

    held = (await db.execute(select(Role.id, Role.is_active).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id))).all()
    if not held:
        perms = SYSTEM_ROLES[legacy_role].permissions if legacy_role in SYSTEM_ROLES else frozenset()
    else:
        active = [role_id for role_id, is_active in held if is_active]
        keys = (
            (await db.execute(select(RolePermission.permission_key).where(RolePermission.role_id.in_(active)))).scalars().all()
            if active
            else []
        )
        perms = frozenset(keys)
    level = "platform" if platform_user else "tenant"
    perms = frozenset(k for k in perms if k in BY_KEY and BY_KEY[k].scope == level)
    permission_cache.put(user_id, perms)
    return perms
