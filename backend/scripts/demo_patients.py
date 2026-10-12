"""Demo patients for local development (called from seed.py).

Creates clinic patient records for the sample clinics, some with issued prescriptions and diagnoses,
plus patient-portal accounts linked to them so the patient side can be tried end to end:

    Nasrin Akter   01700000001  — account holder; linked at Dr. Rahman's and Dr. Karim's clinics, plus her
                                   child Arif (linked at Dr. Rahman's). Two clinics, so sharing can be tried.
    Rahim Uddin    01700000002  — account holder linked at Dr. Rahman's only.

Everything has a fixed id, so running the seed again changes nothing. In development the sign-in code for
these two numbers is always DEMO_OTP_CODE (see app/modules/identity/otp.py); the demo phones are not real.
"""

from datetime import date, datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.service import name_key
from app.shared.models import (
    ConsentEvent,
    Patient,
    PatientDiagnosis,
    PatientHealthProfile,
    PatientLink,
    PersonAccount,
    PersonProfile,
    Prescription,
    PrescriptionItem,
    Visit,
)

RAHMAN_TENANT = "550e8400-e29b-41d4-a716-446655440001"
KARIM_TENANT = "550e8400-e29b-41d4-a716-446655440002"


def _id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "altcare-demo:" + ":".join(parts)))


def _years_ago(years: int) -> date:
    return date.today().replace(year=date.today().year - years, month=6, day=15)


# (key, tenant, name, gender, years old, phone, complaint, history, blood group)
PATIENTS = [
    ("nasrin-r", RAHMAN_TENANT, "Nasrin Akter", "female", 34, "01700000001", "Recurring migraine", "Migraine since 2019; worse with heat", "B+"),
    ("arif-r", RAHMAN_TENANT, "Arif Hasan", "male", 8, "01700000001", "Frequent colds", "Allergic rhinitis", "B+"),
    ("rahim-r", RAHMAN_TENANT, "Rahim Uddin", "male", 52, "01700000002", "Joint pain", "Knee osteoarthritis, type 2 diabetes", "O+"),
    ("sufia-r", RAHMAN_TENANT, "Sufia Begum", "female", 61, "01711000003", "Insomnia", "Hypertension", "A+"),
    ("kamal-r", RAHMAN_TENANT, "Kamal Hossain", "male", 29, "01711000004", "Acidity", None, "AB+"),
    ("nasrin-k", KARIM_TENANT, "Nasrin Akter", "female", 34, "01700000001", "Digestive trouble", "Gastritis", "B+"),
    ("jahid-k", KARIM_TENANT, "Jahid Islam", "male", 45, "01722000005", "Back pain", "Desk job, no prior surgery", "O-"),
]

# patient key -> (doctor email id lookup by tenant, diagnosis, [(medicine, dosage, frequency, duration)], advice)
CLINICAL = {
    "nasrin-r": ("Migraine without aura", "G43.0", [("Belladonna 30C", "4 pills", "Twice a day", "7 days"), ("Natrum Mur 200C", "4 pills", "Once a day", "14 days")], "Avoid long exposure to sun. Drink plenty of water."),
    "rahim-r": ("Knee osteoarthritis", "M17.9", [("Rhus Tox 30C", "4 pills", "Three times a day", "10 days")], "Gentle walking every morning. Keep the diabetes diet."),
    "nasrin-k": ("Chronic gastritis", "K29.5", [("Triphala churna", "1 teaspoon", "At bedtime", "30 days")], "Eat small meals. Avoid spicy food."),
}

# patient key -> health background (codes from app/shared/health_options.py)
HEALTH_PROFILES = {
    "nasrin-r": dict(
        chronic_conditions=["thyroid_disorder"],
        allergies=[{"type": "drug", "substance": "Penicillin", "severity": "severe"}],
        family_history=["diabetes", "hypertension"],
        smoking="never", alcohol="never", betel_tobacco="never", diet_type="mixed",
    ),
    "rahim-r": dict(
        chronic_conditions=["diabetes", "hypertension", "arthritis"],
        allergies=[{"type": "food", "substance": "Prawn", "severity": "moderate"}],
        family_history=["diabetes", "heart_disease"],
        smoking="former", alcohol="never", betel_tobacco="current", diet_type="non_vegetarian",
        on_allopathic_medicines=True, on_blood_thinners=True,
        current_medicines_note="Metformin 500 mg twice a day; aspirin 75 mg",
    ),
    "sufia-r": dict(
        chronic_conditions=["hypertension"], allergies=[], family_history=["hypertension"],
        smoking="never", alcohol="never", betel_tobacco="current", diet_type="vegetarian",
        on_allopathic_medicines=True, current_medicines_note="Amlodipine 5 mg",
    ),
}

# patient key -> a recent visit with vitals
VISITS = {
    "nasrin-r": dict(complaint="Recurring headache", temperature_c=36.8, pulse_bpm=78, bp_systolic=118, bp_diastolic=76, respiratory_rate=16, spo2_percent=99, weight_kg=58.0, height_cm=160.0, pain_score=5),
    "rahim-r": dict(complaint="Knee pain on climbing stairs", temperature_c=36.9, pulse_bpm=84, bp_systolic=142, bp_diastolic=90, respiratory_rate=18, spo2_percent=97, weight_kg=82.0, height_cm=171.0, blood_sugar_mmol=8.4, blood_sugar_type="fasting", pain_score=6),
    "sufia-r": dict(complaint="Poor sleep for a month", temperature_c=36.7, pulse_bpm=72, bp_systolic=150, bp_diastolic=92, spo2_percent=98, weight_kg=64.0, height_cm=152.0, pain_score=2),
}

# phone -> (profiles: key, display, relationship, years old, dependent, patient keys to link)
ACCOUNTS = {
    "+8801700000001": [
        ("nasrin", "Nasrin Akter", "self", 34, False, ["nasrin-r", "nasrin-k"]),
        ("arif", "Arif Hasan", "child", 8, True, ["arif-r"]),
    ],
    "+8801700000002": [("rahim", "Rahim Uddin", "self", 52, False, ["rahim-r"])],
}


async def seed_demo_patients(session: AsyncSession) -> dict[str, int]:
    stats = {"patients": 0, "accounts": 0, "links": 0}
    now = datetime.now(timezone.utc)
    by_key = {p[0]: p for p in PATIENTS}
    doctors = {
        tid: (await session.execute(text("select id from users where tenant_id = :t and role = 'doctor' limit 1"), {"t": tid})).scalar_one_or_none()
        for tid in (RAHMAN_TENANT, KARIM_TENANT)
    }
    if not all(doctors.values()):
        print("  ⚠ sample doctors missing; skipping demo patients")
        return stats

    for key, tenant, name, gender, age, phone, complaint, history, blood in PATIENTS:
        await session.execute(text("select set_config('app.tenant_id', :t, true)"), {"t": tenant})
        pid = _id("patient", key)
        if await session.get(Patient, pid) is None:
            session.add(
                Patient(
                    id=pid, tenant_id=tenant, full_name=name, gender=gender, date_of_birth=_years_ago(age),
                    phone=phone, chief_complaint=complaint, medical_history=history, blood_group=blood, is_active=True,
                )
            )
            stats["patients"] += 1
        if key in CLINICAL and (await session.get(Prescription, _id("rx", key))) is None:
            diagnosis, icd, items, advice = CLINICAL[key]
            await session.flush()
            session.add(PatientDiagnosis(patient_id=pid, tenant_id=tenant, description=diagnosis, icd_code=icd, diagnosed_at=date.today() - timedelta(days=20), is_active=True))
            rx = Prescription(
                id=_id("rx", key), tenant_id=tenant, patient_id=pid, prescribed_by=doctors[tenant],
                diagnosis=diagnosis, advice=advice, doctors_notes="Demo private note", status="issued",
            )
            session.add(rx)
            await session.flush()
            for order, (medicine, dosage, frequency, duration) in enumerate(items):
                session.add(PrescriptionItem(prescription_id=rx.id, tenant_id=tenant, medicine_name=medicine, dosage=dosage, frequency=frequency, duration=duration, display_order=order))
    await session.flush()

    for key, values in HEALTH_PROFILES.items():
        tenant = by_key[key][1]
        await session.execute(text("select set_config('app.tenant_id', :t, true)"), {"t": tenant})
        if (await session.get(PatientHealthProfile, _id("health", key))) is None:
            session.add(PatientHealthProfile(id=_id("health", key), tenant_id=tenant, patient_id=_id("patient", key), **values))
    for key, values in VISITS.items():
        tenant = by_key[key][1]
        await session.execute(text("select set_config('app.tenant_id', :t, true)"), {"t": tenant})
        if (await session.get(Visit, _id("visit", key))) is None:
            complaint = values.pop("complaint") if "complaint" in values else None
            session.add(
                Visit(
                    id=_id("visit", key), tenant_id=tenant, patient_id=_id("patient", key), doctor_id=doctors[tenant],
                    visit_date=date.today() - timedelta(days=3), visit_type="consultation", chief_complaint=complaint,
                    status="completed", **values,
                )
            )
    await session.flush()

    for phone, profiles in ACCOUNTS.items():
        account_id = _id("account", phone)
        if await session.get(PersonAccount, account_id) is None:
            session.add(PersonAccount(id=account_id, phone=phone, phone_verified_at=now, status="active", portal_registered_at=now))
            stats["accounts"] += 1
        await session.flush()
        for pkey, display, relationship, age, dependent, patient_keys in profiles:
            profile_id = _id("profile", phone, pkey)
            if await session.get(PersonProfile, profile_id) is None:
                session.add(
                    PersonProfile(
                        id=profile_id, account_id=account_id, display_name=display, name_key=name_key(display),
                        date_of_birth=_years_ago(age), gender=by_key[patient_keys[0]][3], relationship=relationship,
                        is_dependent=dependent, status="active", source="clinic",
                    )
                )
            await session.flush()
            for patient_key in patient_keys:
                link_id = _id("link", patient_key)
                if await session.get(PatientLink, link_id) is not None:
                    continue
                tenant = by_key[patient_key][1]
                await session.execute(text("select set_config('app.tenant_id', :t, true)"), {"t": tenant})
                consent_id = _id("consent", patient_key)
                session.add(
                    ConsentEvent(
                        id=consent_id, kind="link", tenant_id=tenant, patient_id=_id("patient", patient_key),
                        profile_id=profile_id, account_id=account_id, method="clinic_otp", script_version="demo",
                        staff_confirmed_told=True, note="Demo seed data",
                    )
                )
                session.add(
                    PatientLink(
                        id=link_id, tenant_id=tenant, patient_id=_id("patient", patient_key), profile_id=profile_id,
                        method="clinic_otp", status="linked", linked_at=now, linked_by=doctors[tenant],
                        consent_event_id=consent_id, portal_access_at=now,
                    )
                )
                stats["links"] += 1
        await session.flush()
    return stats
