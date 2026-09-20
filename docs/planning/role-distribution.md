# Role Distribution — Implementation Spec

**Status:** Shipped — `GET /admin/users` and `PATCH /admin/users/{id}` are live in
`backend/app/modules/admin/routes.py`, and `/admin/users` (role distribution + user
management) is live in the frontend. Kept here as the reference spec; see
`docs/status/current.md` for current-state summary.  
**Last updated:** 2026-09-21  
**Depends on:** `docs/planning/admin-module.md` (Phase A — implemented alongside this)

---

## Goal

Give the platform admin a real-time view of all users in the system, grouped by role and
scoped by tenant, with the ability to update a user's role or activation status without
requiring a re-seeding or direct DB change.

---

## Scope

Two perspectives:

| View | Who sees it | What it shows |
|---|---|---|
| **Role group summary** | Platform admin | All 4 roles with counts and user lists, across the entire platform |
| **User wise management** | Platform admin | Individual user records — change role, activate/deactivate |

This is a **platform admin feature only**. Tenant users (doctors, receptionists) cannot
see other tenants' users. A doctor managing their own team (e.g. adding a receptionist)
is a separate future feature (Phase C).

---

## Backend endpoints

All endpoints added to `app/modules/admin/routes.py` alongside the Phase A tenant endpoints.
All guarded by `RequireAdmin`.

### `GET /admin/users`

Returns all users in the system grouped by role.

**Query params:**
- `role` (optional): filter by role — `admin | operator | doctor | receptionist`
- `tenant_id` (optional): filter to one tenant's users
- `is_active` (optional): `true | false`

**Response:**
```json
{
  "summary": {
    "total": 25,
    "by_role": {
      "admin": 1,
      "operator": 1,
      "doctor": 18,
      "receptionist": 5
    }
  },
  "users": [
    {
      "id": "uuid",
      "email": "dr.rahman@example.com",
      "full_name": "Dr. Rahman",
      "role": "doctor",
      "is_active": true,
      "is_email_verified": true,
      "last_login_at": "2026-07-10T12:00:00Z",
      "tenant_id": "uuid",
      "tenant_name": "Rahman Homeo Clinic",
      "created_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

### `PATCH /admin/users/{user_id}`

Update a user's role or activation status.

**Payload** (all fields optional — send only what changes):
```json
{
  "role": "receptionist | doctor | operator | admin",
  "is_active": true | false
}
```

**Rules:**
- `role` change increments `token_version` to invalidate current JWT (consistent with
  existing security pattern in `change_password`)
- Platform users (`admin`, `operator`) must have `tenant_id = null` — cannot assign a
  platform role to a tenant user or vice versa
- Cannot demote/remove the last active admin (guard: count admins before change)
- Deactivating a user immediately blocks their next API call (token version check enforces this)

**Response:** Updated `AdminUserItem`

---

## Schemas (`admin/schemas.py`)

```python
class AdminUserItem(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    last_login_at: datetime | None
    tenant_id: str | None
    tenant_name: str | None
    created_at: datetime

class AdminUsersResponse(BaseModel):
    summary: dict  # { total, by_role: { admin, operator, doctor, receptionist } }
    users: list[AdminUserItem]

class AdminUpdateUserRequest(BaseModel):
    role: str | None = None   # must be valid role string
    is_active: bool | None = None
```

---

## Frontend — `/admin/users`

**URL:** `/admin/users`  
**Nav label:** Users  
**Sidebar icon:** Users icon

### Layout

```
[ Role distribution cards — 4 cards, one per role ]

admin (1)  |  operator (1)  |  doctor (18)  |  receptionist (5)

[ Users table — filterable ]
Search ____   Role [All ▾]   Status [All ▾]

| Full Name       | Email                   | Role          | Tenant          | Status  | Last Login    | Actions |
|-----------------|-------------------------|---------------|-----------------|---------|---------------|---------|
| Admin User      | admin@altcare.com       | admin         | —               | Active  | 2026-07-10    | Edit    |
| Dr. Rahman      | dr.rahman@example.com   | doctor        | Rahman Clinic   | Active  | 2026-07-09    | Edit    |
| Jane Doe        | jane@example.com        | receptionist  | Rahman Clinic   | Active  | —             | Edit    |
```

### Role cards

Clicking a role card filters the table to that role. Active card is highlighted.

### Edit user modal

Inline action — clicking Edit opens a modal:
```
Edit User: Dr. Rahman

Role:    [ doctor ▾ ]   (dropdown: admin/operator/doctor/receptionist)
Status:  [ Active  ▾ ]  (dropdown: Active/Inactive)

[ Cancel ]  [ Save Changes ]
```

**Warning shown** when changing role: "Changing this user's role will immediately
invalidate their current session."

**Error shown** if trying to set a platform role on a tenant user (or vice versa).

---

## Admin sidebar (updated)

When `role === 'admin'`, show only the admin nav (no doctor nav items):

```
Platform Dashboard     /admin/dashboard
Clients                /admin/clients
Users                  /admin/users      ← NEW
```

Badge on Clients tab: count of pending approvals.

---

## File checklist

### Backend
- [x] `backend/app/modules/admin/routes.py` — add `GET /admin/users`, `PATCH /admin/users/{id}`
- [x] `backend/app/modules/admin/service.py` — add `list_users()`, `update_user()`
- [x] `backend/app/modules/admin/schemas.py` — add `AdminUserItem`, `AdminUsersResponse`, `AdminUpdateUserRequest`

### Frontend
- [x] `frontend/src/lib/api/admin.ts` — add `getAdminUsers()`, `updateAdminUser()`
- [x] `frontend/src/lib/hooks/useAdminUsers.ts` — React Query hooks
- [x] `frontend/src/types/admin.ts` — TypeScript interfaces for admin types
- [x] `frontend/src/app/(dashboard)/admin/users/page.tsx` — NEW role distribution page
- [x] `frontend/src/components/layout/Sidebar.tsx` — add Users nav item for admin

---

## Implementation order

1. Backend admin module (Phase A endpoints + role distribution endpoints together)
2. Update `main.py` to register `/api/v1/admin`
3. Frontend sidebar — admin-only nav
4. Frontend `/admin/dashboard` page
5. Frontend `/admin/users` page
6. Update `/admin/clients` to use new API paths

Phase A and role distribution share the same module — implement them in one pass.
