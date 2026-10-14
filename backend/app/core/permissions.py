"""The permission catalogue and the four system roles (ADR 010).

A permission is one thing the code can allow or refuse. The vocabulary lives here, in code, because a permission
only means something if code enforces it; what is data is which roles hold which permissions.

Scope: a `platform` permission exists only for platform staff, a `tenant` permission only inside a clinic. A role has
the scope of its permissions and can never hold one of the other scope.

The system roles reproduce, exactly, what the hard-coded roles could do before this model existed (see
docs/architecture/roles-access.md): changing a system role's set here is a change of behaviour for every user who
holds it. `tests/unit/test_permissions.py` pins the sets.
"""

from dataclasses import dataclass
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

Scope = Literal["platform", "tenant"]


@dataclass(frozen=True)
class Permission:
    key: str
    scope: Scope
    module: str
    en: str
    bn: str
    sensitive: bool = False


def _t(key: str, module: str, en: str, bn: str, sensitive: bool = False) -> Permission:
    return Permission(key, "tenant", module, en, bn, sensitive)


def _p(key: str, module: str, en: str, bn: str, sensitive: bool = False) -> Permission:
    return Permission(key, "platform", module, en, bn, sensitive)


TENANT_PERMISSIONS: tuple[Permission, ...] = (
    _t("dashboard.view", "dashboard", "See the clinic dashboard", "ক্লিনিকের ড্যাশবোর্ড দেখা"),
    _t("patients.read", "patients", "View patients", "রোগীদের তথ্য দেখা"),
    _t("patients.write", "patients", "Add and edit patients", "রোগী যোগ ও সম্পাদনা"),
    _t("patients.delete", "patients", "Deactivate patients", "রোগী নিষ্ক্রিয় করা", sensitive=True),
    _t("diagnoses.write", "patients", "Record and change diagnoses", "রোগনির্ণয় লেখা ও পাল্টানো"),
    _t("health_profile.read", "health", "View a patient's health background", "রোগীর স্বাস্থ্যের পটভূমি দেখা"),
    _t("health_profile.write", "health", "Edit a patient's health background", "রোগীর স্বাস্থ্যের পটভূমি সম্পাদনা"),
    _t("case_taking.read", "health", "View case-taking details", "কেস-টেকিংয়ের তথ্য দেখা"),
    _t("case_taking.write", "health", "Record case-taking details", "কেস-টেকিংয়ের তথ্য লেখা"),
    _t("appointments.read", "appointments", "View appointments", "অ্যাপয়েন্টমেন্ট দেখা"),
    _t("appointments.write", "appointments", "Schedule and change appointments", "অ্যাপয়েন্টমেন্ট দেওয়া ও পাল্টানো"),
    _t("appointment_requests.manage", "appointments", "Answer patients' appointment requests", "রোগীদের অ্যাপয়েন্টমেন্ট অনুরোধের উত্তর দেওয়া"),
    _t("visits.read", "visits", "View visits and vitals", "ভিজিট ও ভাইটাল দেখা"),
    _t("visits.write", "visits", "Record visits and vitals", "ভিজিট ও ভাইটাল লেখা"),
    _t("prescriptions.read", "prescriptions", "View and print prescriptions", "প্রেসক্রিপশন দেখা ও প্রিন্ট"),
    _t("prescriptions.write", "prescriptions", "Write prescription drafts", "প্রেসক্রিপশনের খসড়া লেখা"),
    _t("prescriptions.issue", "prescriptions", "Issue prescriptions", "প্রেসক্রিপশন ইস্যু করা"),
    _t("prescriptions.void", "prescriptions", "Void prescriptions", "প্রেসক্রিপশন বাতিল করা"),
    _t("payments.read", "payments", "View payments", "পেমেন্ট দেখা"),
    _t("payments.write", "payments", "Record payments", "পেমেন্ট লেখা"),
    _t("invoices.read", "payments", "View invoices", "ইনভয়েস দেখা"),
    _t("invoices.write", "payments", "Create and edit invoices", "ইনভয়েস তৈরি ও সম্পাদনা"),
    _t("medicines.read", "library", "View the medicine library", "ওষুধের তালিকা দেখা"),
    _t("medicines.write", "library", "Add and edit medicines", "ওষুধ যোগ ও সম্পাদনা"),
    _t("symptoms.read", "library", "View the symptom library", "উপসর্গের তালিকা দেখা"),
    _t("symptoms.write", "library", "Add and edit symptoms", "উপসর্গ যোগ ও সম্পাদনা"),
    _t("identity.link", "identity", "Verify a patient's phone and link records", "রোগীর ফোন যাচাই ও রেকর্ড যুক্ত করা"),
    _t("identity.revoke", "identity", "Remove a patient's link to an AltCare account", "রোগীর AltCare অ্যাকাউন্টের সংযোগ সরানো"),
    _t("shared_records.read", "identity", "Read records patients share from other clinics", "রোগীর শেয়ার করা অন্য ক্লিনিকের রেকর্ড পড়া"),
    _t("clinic_profile.read", "clinic", "View the clinic profile", "ক্লিনিকের প্রোফাইল দেখা"),
    _t("clinic_profile.write", "clinic", "Edit the clinic profile and logo", "ক্লিনিকের প্রোফাইল ও লোগো সম্পাদনা"),
    _t("doctor_profile.manage", "clinic", "Manage the doctor's own profile, degrees and trainings", "ডাক্তারের নিজের প্রোফাইল, ডিগ্রি ও প্রশিক্ষণ"),
    _t("directory.manage", "directory", "Manage the public directory listing", "পাবলিক ডিরেক্টরির তালিকা পরিচালনা"),
    _t("marketing.request", "marketing", "Ask for a Facebook feature", "ফেসবুকে প্রচারের অনুরোধ"),
    _t("content.author", "content", "Write articles", "প্রবন্ধ লেখা"),
    _t("messaging.send", "messaging", "Send SMS and email to patients", "রোগীদের এসএমএস ও ইমেইল পাঠানো"),
    _t("messaging.read", "messaging", "View the message log", "পাঠানো বার্তার তালিকা দেখা"),
    _t("billing.view", "billing", "View the messaging credit balance and history", "মেসেজিং ক্রেডিটের হিসাব ও ইতিহাস দেখা"),
    _t("billing.manage", "billing", "See the plan and receipts; buy plans and credits", "প্ল্যান ও রসিদ দেখা; প্ল্যান ও ক্রেডিট কেনা", sensitive=True),
    _t("ai.use", "ai", "Use the AI assistant", "এআই সহকারী ব্যবহার"),
    _t("team.read", "team", "See the clinic's staff and roles", "ক্লিনিকের কর্মী ও ভূমিকা দেখা"),
    _t("team.manage", "team", "Add staff and manage roles", "কর্মী যোগ ও ভূমিকা পরিচালনা", sensitive=True),
)

PLATFORM_PERMISSIONS: tuple[Permission, ...] = (
    _p("tenants.read", "tenants", "View clinics and the platform dashboard", "ক্লিনিক ও প্ল্যাটফর্ম ড্যাশবোর্ড দেখা"),
    _p("tenants.manage", "tenants", "Provision, approve, suspend and verify clinics", "ক্লিনিক তৈরি, অনুমোদন, স্থগিত ও যাচাই"),
    _p("users.read", "users", "View users across the platform", "প্ল্যাটফর্মের ব্যবহারকারী দেখা"),
    _p("users.manage", "users", "Change users' roles and status", "ব্যবহারকারীর ভূমিকা ও অবস্থা পাল্টানো", sensitive=True),
    _p("plans.read", "plans", "View plans and clinic entitlements", "প্ল্যান ও ক্লিনিকের সুবিধা দেখা"),
    _p("plans.manage", "plans", "Edit plans and clinic overrides", "প্ল্যান ও ক্লিনিকভিত্তিক ব্যতিক্রম সম্পাদনা"),
    _p("billing.admin", "billing", "Manage credit packs, orders and manual plan grants", "ক্রেডিট প্যাক, অর্ডার ও ম্যানুয়াল প্ল্যান দেওয়া", sensitive=True),
    _p("content.manage", "content", "Review and publish articles", "প্রবন্ধ পর্যালোচনা ও প্রকাশ"),
    _p("pharmacies.manage", "catalogue", "Manage the pharmacy directory", "ফার্মেসি ডিরেক্টরি পরিচালনা"),
    _p("institutions.manage", "catalogue", "Manage the institution directory", "প্রতিষ্ঠান ডিরেক্টরি পরিচালনা"),
    _p("catalogue.global_write", "catalogue", "Edit the global medicine and symptom catalogue", "গ্লোবাল ওষুধ ও উপসর্গ তালিকা সম্পাদনা"),
    _p("contact.manage", "contact", "Read and handle contact messages", "যোগাযোগ বার্তা পড়া ও নিষ্পত্তি"),
    _p("marketing.manage", "marketing", "Draft and post Facebook features", "ফেসবুক প্রচারের খসড়া ও পোস্ট"),
    _p("roles.manage_global", "roles", "Manage global roles and platform staff roles", "গ্লোবাল ও প্ল্যাটফর্ম কর্মীর ভূমিকা পরিচালনা", sensitive=True),
    _p("audit.read", "audit", "View the role and access audit log", "ভূমিকা ও প্রবেশাধিকারের অডিট লগ দেখা"),
)

PERMISSIONS: tuple[Permission, ...] = TENANT_PERMISSIONS + PLATFORM_PERMISSIONS
BY_KEY: dict[str, Permission] = {p.key: p for p in PERMISSIONS}
assert len(BY_KEY) == len(PERMISSIONS), "duplicate permission key"

_RECEPTIONIST = frozenset(
    {
        "dashboard.view", "patients.read", "health_profile.read", "case_taking.read", "appointments.read",
        "appointments.write", "appointment_requests.manage", "visits.read", "prescriptions.read", "payments.read",
        "payments.write", "invoices.read", "invoices.write", "medicines.read", "symptoms.read", "identity.link",
        "clinic_profile.read", "billing.view",
    }
)


@dataclass(frozen=True)
class SystemRole:
    key: str
    scope: Scope
    en: str
    bn: str
    permissions: frozenset[str]


SYSTEM_ROLES: dict[str, SystemRole] = {
    "admin": SystemRole("admin", "platform", "Platform admin", "প্ল্যাটফর্ম অ্যাডমিন", frozenset(p.key for p in PLATFORM_PERMISSIONS)),
    "operator": SystemRole(
        "operator", "platform", "Platform operator (read-only)", "প্ল্যাটফর্ম অপারেটর (শুধু দেখা)",
        frozenset({"tenants.read", "users.read", "plans.read", "audit.read"}),
    ),
    "doctor": SystemRole("doctor", "tenant", "Doctor", "ডাক্তার", frozenset(p.key for p in TENANT_PERMISSIONS)),
    "receptionist": SystemRole("receptionist", "tenant", "Receptionist", "রিসেপশনিস্ট", _RECEPTIONIST),
}


def system_role_id(key: str) -> str:
    """The fixed id of a system role, the same in every database, so code can refer to it without a lookup."""
    return str(uuid5(NAMESPACE_URL, f"altcare:system-role:{key}"))


# ----- rules the clinic-roles feature (Phase 3) must enforce; here so they are tested from the start ---------------


class PermissionRuleError(ValueError):
    """A role definition or grant that breaks one of the safety rules in ADR 010."""


def validate_role_permissions(scope: Scope, keys: set[str] | frozenset[str]) -> None:
    """Every key exists and has the role's scope (a clinic role can never carry a platform permission)."""
    unknown = sorted(k for k in keys if k not in BY_KEY)
    if unknown:
        raise PermissionRuleError(f"Unknown permissions: {', '.join(unknown)}")
    wrong = sorted(k for k in keys if BY_KEY[k].scope != scope)
    if wrong:
        raise PermissionRuleError(f"Not {scope}-level permissions: {', '.join(wrong)}")


def check_can_grant(actor_permissions: set[str] | frozenset[str], keys: set[str] | frozenset[str]) -> None:
    """No escalation by delegation: nobody can put into a role, or hand out, a permission they do not hold."""
    missing = sorted(k for k in keys if k not in actor_permissions)
    if missing:
        raise PermissionRuleError(f"You cannot grant permissions you do not hold: {', '.join(missing)}")
