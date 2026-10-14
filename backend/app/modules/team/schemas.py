"""Request and response shapes for the clinic Team page (ADR 010, Phase 3)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RoleBrief(BaseModel):
    id: str
    key: str
    name_en: str
    name_bn: str
    is_system: bool


class RoleItem(RoleBrief):
    based_on_role_id: str | None = None
    permissions: list[str]
    member_count: int
    # What the person looking at the page may do with this role
    can_edit: bool
    can_assign: bool


class PermissionItem(BaseModel):
    key: str
    module: str
    description_en: str
    description_bn: str
    is_sensitive: bool
    # False when the person looking holds nothing like it: they cannot hand it out (no escalation)
    can_grant: bool


class RoleCreate(BaseModel):
    name_en: str = Field(min_length=2, max_length=100)
    name_bn: str | None = Field(default=None, max_length=100)
    permissions: list[str] = Field(min_length=1)
    based_on_role_id: str | None = None
    # Must be true when the role carries a sensitive permission, so it is never granted by accident
    acknowledge_sensitive: bool = False


class RoleUpdate(BaseModel):
    name_en: str | None = Field(default=None, min_length=2, max_length=100)
    name_bn: str | None = Field(default=None, max_length=100)
    permissions: list[str] | None = Field(default=None, min_length=1)
    acknowledge_sensitive: bool = False


class MemberItem(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None = None
    is_active: bool
    is_email_verified: bool
    last_login_at: datetime | None = None
    is_you: bool
    roles: list[RoleBrief]
    # Whether the person looking may change this member's roles
    can_manage: bool


class MemberInvite(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    language: str = Field(default="en", pattern="^(en|bn)$")
    role_ids: list[str] = Field(min_length=1)


class MemberRolesUpdate(BaseModel):
    role_ids: list[str] = Field(min_length=1)


class MemberStatusUpdate(BaseModel):
    is_active: bool


class AuditItem(BaseModel):
    id: str
    created_at: datetime
    action: str
    actor_name: str | None = None
    member_name: str | None = None
    role_name: str | None = None
    before: dict | None = None
    after: dict | None = None


class AuditPage(BaseModel):
    items: list[AuditItem]
    total: int
