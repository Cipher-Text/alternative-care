# ADR 010: Dynamic roles and permissions: a fixed permission catalogue, roles that are global or tenant-specific, and users who hold roles

- Status: **Accepted 2026-10-14 with the recommended answers to the four decisions below. Phases 1 to 3 are built**
  (see "Phase 1 as built", "Phase 3 as built"); Phase 4 is not.
- Date: 2026-10-14
- Related: ADR 002 (platform vs tenant data), `docs/architecture/roles-access.md` (the current, hard-coded model),
  `docs/architecture/multi-tenancy.md`, `backend/app/core/entitlements.py` (the plan/entitlement system, which this
  design deliberately mirrors).

## Context

Access today is four roles written as strings in code: `admin`, `operator` (platform), `doctor`, `receptionist`
(tenant). A user has exactly one, stored in `users.role` and copied into the JWT.

Verified in the code on 2026-10-14:

- `backend/app/core/dependencies.py` gates routes with `require_role("doctor")`, `RequireAdmin`,
  `RequireAdminOrOperator`, plus `deny_receptionist_writes` / `deny_receptionist` applied to whole routers in
  `main.py`. These guards are used in about 17 modules, and there are about 47 other places that compare a role string.
- The frontend decides what to show from the same string (`lib/auth/permissions.ts` `useCan()` is used in 11 files;
  about 59 role comparisons overall).
- "Receptionist is read-only on clinical records" is therefore not a rule that can be edited: it is `if role ==
  "receptionist" and method not in safe`. A clinic that wants an assistant doctor who can write notes but not issue
  prescriptions, or an accountant who sees payments but not clinical data, cannot have one. The platform cannot
  create a "support" or "finance" staff role without a code change.
- The plan system already solved the same shape of problem well: a code-defined catalogue of entitlements,
  admin-editable plan values, and per-tenant overrides, with an audit log (`plans`, `plan_entitlements`,
  `tenant_entitlement_overrides`, `plan_audit_log`).

The owner's requirement (2026-10-14): make this dynamic. **Users, roles and permissions must each be able to be
global (platform-wide) or tenant-specific.**

## Decision

### 1. Four separate ideas, kept separate

| Idea | What it is | Where it lives | Who changes it |
|---|---|---|---|
| **Permission** | One thing the code can allow or refuse, e.g. `patients.write`, `prescriptions.issue`, `billing.manage` | A **catalogue defined in code** (`app/core/permissions.py`), mirrored into a `permissions` table by a migration/sync | Developers, through a release |
| **Role** | A named set of permissions | `roles` table: **global** (`tenant_id` null) or **tenant-specific** (`tenant_id` set) | Platform admins (global), clinic owners (their own) |
| **User** | A person's login | `users` (already platform-level when `tenant_id` is null, tenant-level otherwise) | As today |
| **Entitlement** | What the clinic *bought* (plan features and limits) | Existing plan system | Platform admins |

Effective access is **a permission the user holds AND an entitlement the clinic has**. They stay two systems: a role
decides what a person may do, a plan decides what the clinic may use.

Permissions are **not** created by tenants. A permission only means something if code enforces it, so inventing one
in a database row would grant nothing. "Dynamic" means roles are data and the *grants* are data; the *vocabulary*
is code. This is the same split the entitlement catalogue already uses.

### 2. Scope on everything

- Every **permission** has a scope, `platform` or `tenant`. Platform permissions (`tenants.manage`, `plans.manage`,
  `roles.manage_global`, `content.publish`) exist only for platform staff; tenant permissions (`patients.read`,
  `prescriptions.issue`) exist only inside a clinic.
- A **role** has the same scope as its permissions. A role can only contain permissions of its own scope, enforced in
  the service and by a database check. A tenant role can therefore never carry a platform permission, whatever a
  clinic owner clicks. This is the main privilege-escalation guard.
- **Global roles** (`tenant_id` null) are visible to every clinic. The four existing roles become **system roles**
  with fixed keys (`admin`, `operator`, `doctor`, `receptionist`) whose permission sets exactly reproduce today's
  behaviour, so enabling the new model changes nothing for any current user.
- **Tenant roles** (`tenant_id` set) are created by that clinic, usually by copying a global template and editing it
  ("Assistant doctor", "Pharmacist", "Accountant"). They are invisible to every other clinic.
- **Platform custom roles** are global roles an admin creates for staff ("Support", "Finance"), with platform
  permissions only.
- **Users** keep their current meaning: `tenant_id` null is platform staff, a tenant id is clinic staff. A user's
  roles must match their level (a clinic user can only hold global tenant-scope roles and that clinic's own roles).

### 3. Data model (all additive; `users.role` stays during the transition)

```
permissions        key (PK), scope, module, description_en, description_bn, is_sensitive
roles              id, key, name_en, name_bn, scope, tenant_id NULL, is_system, based_on_role_id NULL, is_active
                   unique (coalesce(tenant_id, ''), key)
role_permissions   role_id, permission_key            (primary key of both)
user_roles         user_id, role_id, granted_by, granted_at
role_audit_log     who, when, tenant_id, role_id, user_id NULL, action, before, after
```

- `is_system` roles cannot be deleted, renamed or have their permission set changed by clinics; only a platform admin
  holding `roles.manage_global` may adjust a system role, and every change is audited.
- A user may hold **several** roles; effective permissions are the union. (A single role would force an "assistant
  doctor who is also the accountant" into yet another role. Decision 1 below.)
- Row-level security: `roles`, `role_permissions` and `user_roles` get the same tenant policy as the clinical tables,
  except that `roles` with `tenant_id` null are readable by everyone, because every clinic must be able to see the
  global templates.

### 4. Enforcement

- New dependency `require_permission("patients.write")` (and `require_any_permission(...)`). It reads the user's
  effective permission set and refuses with the same structured 403 used today.
- Permissions are resolved **server-side on each request** from the database, behind a short cache (60 seconds,
  cleared when a role or assignment changes), and **never embedded in the JWT**. A role edit or a removed role takes
  effect immediately, not at token expiry; changing a user's roles also bumps `token_version` as it does today.
- The JWT keeps a `role` claim, set to the user's primary role, only for display and backward compatibility.
- A new `GET /auth/me/permissions` returns the effective list. The frontend's `useCan()` is rewritten to read it
  (`can('prescriptions.issue')`) instead of comparing role strings. The server stays the only authority.
- `require_role` and the role-string checks keep working, implemented on top of permissions, until every call site
  is migrated, so the change can ship in small steps.

### 5. Safety rules (these are requirements, not suggestions)

1. **No escalation by delegation.** A user may only grant or put into a role permissions they hold themselves. A
   clinic owner can never hand out something the clinic's own roles do not contain.
2. **Scope check** (above): a role never holds a permission outside its scope.
3. **A clinic always has an owner.** The first doctor of a clinic holds `team.manage`; the last holder of that
   permission cannot be removed, demoted or deactivated by anyone but a platform admin.
4. **Sensitive permissions are flagged** (`is_sensitive`): `team.manage`, `billing.manage`, `patients.delete`,
   `integrations.manage`, `roles.manage_global`. They are never in a default template for non-owner roles, and the
   UI warns before granting one.
5. **Every change is audited** with the before and after (`role_audit_log`), visible to the clinic owner for their
   own clinic and to platform admins for everything.
6. **Patient-controlled data is not a role matter.** Record sharing, patient consent and the identity rules in
   ADR 009 stay as they are; a role can never reach another clinic's data (tenant isolation is unchanged).
7. **Doctor-only clinical judgement stays doctor-only until chosen otherwise.** Issuing and voiding prescriptions
   and recording diagnoses carry their own permissions (`prescriptions.issue`, `prescriptions.void`,
   `diagnoses.write`), so a clinic can decide who may do them. The default `doctor` role holds them; the default
   `receptionist` does not.

### 6. First permission catalogue (draft, to be refined against the code in Phase 1)

Tenant scope: `dashboard.view`, `patients.read|write|delete`, `appointments.read|write`, `visits.read|write`,
`prescriptions.read|write|issue|void`, `health_profile.read|write`, `case_taking.read|write`,
`payments.read|write`, `invoices.read|write`, `medicines.read|write`, `symptoms.read|write`,
`appointment_requests.manage`, `identity.verify` (link a patient by code), `shared_records.read`,
`directory.manage`, `marketing.request`, `integrations.manage`, `clinic_settings.manage`, `billing.view|manage`,
`team.read|manage`.

Platform scope: `tenants.read|manage`, `users.read|manage`, `plans.manage`, `billing.admin`, `content.manage`,
`pharmacies.manage`, `institutions.manage`, `contact.manage`, `marketing.manage`, `catalogue.global_write`,
`roles.manage_global`, `audit.read`.

## Phases

Each phase is shippable and none changes what any current user can do until Phase 3.

| Phase | What | Risk |
|---|---|---|
| **1. Foundation** | Catalogue in code; the five tables; seed the four system roles with permission sets that reproduce today's behaviour; backfill one `user_roles` row per user; `require_permission`; `GET /auth/me/permissions`; a test that every existing role-guarded route behaves identically for each of the four roles. | Low: additive, behaviour-preserving, tested against the old guards |
| **2. Migrate the guards** | Replace `require_role` / `deny_receptionist*` and the frontend role checks with permissions, module by module (about 17 backend modules, 11 frontend files). | Medium: many small edits; the equivalence test from Phase 1 catches mistakes |
| **3. Clinic roles** | Team page for clinic owners: list staff, assign roles, create a role from a template, edit its permissions, audit view. The safety rules above are enforced here. | Medium: this is where escalation bugs would live, so it gets the most tests |
| **4. Platform roles and audit** | Admin UI for global roles and platform custom roles; global audit view; drop `users.role` as a source of truth. | Low |

Phases 1 and 2 are invisible to users. Phase 3 is the first visible change.

## Consequences

- Clinics get the staffing flexibility they ask for; the platform gets "Support" and "Finance" without releases.
- Slightly more cost per request (a cached permission lookup).
- A real chance of subtle access bugs during Phase 2. Mitigation: the equivalence test, and keeping the old
  guards as a thin layer over the new ones until the last call site moves.
- More surface to secure: role management is itself a privileged feature (safety rules 1 to 5).
- The permission catalogue becomes a public contract in the code: adding a permission is a code change and a
  migration; removing one is a breaking change.

## Phase 1 as built (2026-10-14)

- `app/core/permissions.py`: the catalogue (57 permissions: 42 clinic-level, 15 platform-level), the four system roles
  with their pinned permission sets, and the two safety rules that need no database (`validate_role_permissions`:
  scope; `check_can_grant`: no escalation). `tests/unit/test_permissions.py` pins every set.
- Tables `permissions`, `roles`, `role_permissions`, `user_roles`, `role_audit_log` (migration `i4e0a6d2f8b5`), loaded
  by `sync_catalogue()` (`app/core/rbac.py`), which the migration runs and any later catalogue change runs again.
  Every existing user was given the system role named by `users.role`.
- `users.role` is still the source of truth. An ORM hook (`app/shared/models/rbac.py`) keeps `user_roles` in step when a
  user is created or their role changes, so no existing code needed editing. A user with no assignment falls back to
  the system role named by `users.role`, so a missing row can never lock anyone out or grant more than before.
- `require_permission(...)` (all required) and `require_any_permission(...)` in `app/core/dependencies.py`, backed by
  a per-process cache of 60 seconds (`PERMISSION_CACHE_SECONDS`; a role change clears the cache of the process that
  made it).
- `GET /auth/me/permissions` returns the user's roles and effective permissions.
- **No route guard was changed in Phase 1**; Phase 2 then moved every guard to permissions (`require_role` and the
  receptionist guards are gone), proven by a frozen route-by-role snapshot (`tests/golden/access_matrix.json`) and a
  default-deny test that fails for any route without a permission guard.
- **Deviation from section 3:** row-level security is on `roles` only. `role_permissions` and `user_roles` hold no
  clinic id and are reachable only through `roles`; a policy on them would need a join and protects nothing while the
  app connects as a superuser. Revisit with the least-privileged database role.
- **Phase 2 mapping notes** (guards that are not a plain role check): `identity` routes use two roles (`Staff` =
  doctor + receptionist, mapped to `identity.link`; `DoctorOnly` for revoking, mapped to `identity.revoke`, and for
  reading shared records, `shared_records.read`); billing uses `TenantStaff` (`billing.view`) and `Buyer`
  (`billing.manage`); content authoring allows a doctor or an admin (`content.author` or `content.manage`).

## Phase 3 as built (2026-10-14)

- Module `app/modules/team` (10 endpoints under `/api/v1/team`, router guard: `team.read` to look, `team.manage` to
  change): `GET /permissions`, `GET|POST /roles`, `PATCH|DELETE /roles/{id}`, `GET|POST /members`,
  `PUT /members/{id}/roles`, `PATCH /members/{id}/status`, `GET /audit`. Frontend: `/team` with Staff, Roles and
  Activity tabs (menu item shown with `team.read`; English and Bengali).
- Rules, all enforced in `TeamService` and covered by `tests/integration/test_team.py` (22 tests):
  1. **No escalation**: creating or editing a role, assigning a role and removing one each require the actor to hold
     every permission involved; a role holding permissions the actor lacks cannot be edited, assigned or removed by
     them, and a person holding such a role cannot be switched off or re-roled by them (`can_manage`).
  2. **Scope**: unknown or platform-level permissions are refused (422).
  3. **A clinic keeps an owner**: after every change that could remove it, the service checks that at least one active
     person still holds `team.manage`, and rolls back with 409 `last_owner` if not. Nobody can deactivate themselves.
  4. **Sensitive permissions** need `acknowledge_sensitive: true` when newly granted; the UI asks for a tick.
  5. **Audit**: every change writes `role_audit_log` (created/updated/deleted role, roles assigned, member invited,
     switched off or on) with before and after; the clinic reads its own through `GET /team/audit`.
- A member must hold at least one role (a user with no `user_roles` rows would fall back to the legacy role and could
  gain access). A clinic may have at most 20 own roles; a role in use cannot be deleted.
- Inviting creates the user with an unknown password and emails a set-password link (the password-reset token, valid
  3 days). Practitioner seats: anyone whose roles include `prescriptions.issue` is stored with legacy `users.role =
  'doctor'` and so counts against `max_seats`; everyone else is `'receptionist'`. The legacy role is written with a
  plain UPDATE so the ORM hook that mirrors `users.role` into `user_roles` does not overwrite the chosen roles.
- Deviation from section 4: role changes do not bump `token_version`; permissions are resolved from the database on
  every request (60 s cache, cleared on change in the process that made it), so a change applies at once. Deactivating
  a member does bump it and revokes their sessions.

## Decisions needed from the product owner (answered 2026-10-14: the recommended answer for each)

1. **One role per user, or several?** Recommended: several (union of permissions). Simpler alternative: exactly one.
2. **Can clinics create their own roles?** Recommended: yes, by copying a template, limited to their own
   permissions (rules 1 to 3). Alternative: clinics only choose among global roles, which is much less work and
   less risk, but does not meet "tenant-specific roles".
3. **Which existing behaviour must stay fixed for everyone?** Recommended: nothing but the safety rules; even
   prescription issuing becomes grantable. Alternative: keep issuing and voiding prescriptions doctor-only for good.
4. **Platform custom roles in the first release, or later?** Recommended: Phase 4 (after the clinic side).

## Not decided here

- Per-user permission exceptions on top of roles (grant or deny a single permission to one person). Recommended
  against: it makes "who can do what" hard to explain; make a role instead.
- Time-limited roles (a locum doctor for a week). Easy to add later (`expires_at` on `user_roles`).
- Custom permission *names* per clinic. Not possible by design (see section 1).
