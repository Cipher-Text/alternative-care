"""Patient health profile (step 1 of structured health history) and numeric visit vitals."""

from datetime import date, timedelta

import pytest

from app.modules.patient.service import age_in_years, safety_flags
from app.shared.health_options import OPTIONS

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731


def _url(patient):
    return f"/api/v1/patients/{patient.id}/health-profile"


@pytest.mark.asyncio
async def test_options_come_from_the_server_and_match_the_schemas(client, doctor_token):
    r = await client.get("/api/v1/health-options", headers=H(doctor_token))
    assert r.status_code == 200
    body = r.json()
    assert body == {name: list(codes) for name, codes in OPTIONS.items()}
    assert "betel_tobacco" not in body["chronic_conditions"] and "diabetes" in body["chronic_conditions"]
    assert (await client.get("/api/v1/health-options")).status_code == 401


@pytest.mark.asyncio
async def test_a_patient_without_a_profile_gets_empty_defaults(client, doctor_token, test_patient):
    r = await client.get(_url(test_patient), headers=H(doctor_token))
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is False and body["updated_at"] is None
    assert (body["chronic_conditions"], body["allergies"], body["pregnant"]) == ([], [], False)


@pytest.mark.asyncio
async def test_save_replaces_the_whole_profile_and_flags_follow(client, doctor_token, test_patient):
    payload = {
        "chronic_conditions": ["diabetes", "hypertension", "diabetes"],  # duplicates collapse
        "allergies": [{"type": "drug", "substance": "  Penicillin ", "severity": "severe"}],
        "family_history": ["cancer"],
        "smoking": "former", "alcohol": "never", "betel_tobacco": "current", "diet_type": "mixed",
        "pregnant": True, "lmp_date": str(date.today() - timedelta(days=70)), "breastfeeding": False,
        "on_allopathic_medicines": True, "on_blood_thinners": True, "recent_surgery": False,
        "current_medicines_note": "Metformin 500 mg twice a day",
    }
    r = await client.put(_url(test_patient), json=payload, headers=H(doctor_token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["exists"] is True and body["updated_at"] is not None
    assert body["chronic_conditions"] == ["diabetes", "hypertension"]
    assert body["allergies"] == [{"type": "drug", "substance": "Penicillin", "severity": "severe"}]
    assert body["betel_tobacco"] == "current"
    assert {"allergy", "pregnant", "on_allopathic_medicines", "on_blood_thinners"} <= set(body["safety_flags"])

    # it is what a later read returns, and a second save replaces rather than merges
    assert (await client.get(_url(test_patient), headers=H(doctor_token))).json()["current_medicines_note"] == "Metformin 500 mg twice a day"
    r = await client.put(_url(test_patient), json={"chronic_conditions": ["asthma_copd"]}, headers=H(doctor_token))
    body = r.json()
    assert body["chronic_conditions"] == ["asthma_copd"] and body["allergies"] == [] and body["safety_flags"] == []


@pytest.mark.asyncio
async def test_closed_lists_refuse_unknown_codes_and_bad_combinations(client, doctor_token, test_patient):
    put = lambda body: client.put(_url(test_patient), json=body, headers=H(doctor_token))  # noqa: E731
    assert (await put({"chronic_conditions": ["not_a_condition"]})).status_code == 422
    assert (await put({"allergies": [{"type": "alien", "substance": "x"}]})).status_code == 422
    assert (await put({"allergies": [{"type": "drug", "substance": "   "}]})).status_code == 422
    assert (await put({"smoking": "sometimes"})).status_code == 422
    assert (await put({"lmp_date": str(date.today() - timedelta(days=10))})).status_code == 422  # not pregnant
    assert (await put({"pregnant": True, "lmp_date": str(date.today() + timedelta(days=3))})).status_code == 422
    assert (await put({"pregnant": True, "lmp_date": str(date.today() - timedelta(days=10))})).status_code == 200


@pytest.mark.asyncio
async def test_receptionist_can_read_but_not_change_and_other_clinics_see_nothing(
    client, doctor_token, test_access_token_2, test_patient, db_session, test_tenant
):
    import uuid

    from app.core.security import create_access_token, get_password_hash
    from app.shared.models import User

    await client.put(_url(test_patient), json={"chronic_conditions": ["diabetes"]}, headers=H(doctor_token))
    rec = User(id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="rec.hp@example.com", full_name="Rec", role="receptionist",
               password_hash=get_password_hash("Test@1234"), is_active=True)
    db_session.add(rec)
    await db_session.commit()
    token = create_access_token({"sub": rec.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": rec.email, "plan": "pro"})
    assert (await client.get(_url(test_patient), headers=H(token))).status_code == 200
    assert (await client.put(_url(test_patient), json={}, headers=H(token))).status_code == 403
    # another clinic cannot see this patient at all
    assert (await client.get(_url(test_patient), headers=H(test_access_token_2))).status_code == 404
    assert (await client.put(_url(test_patient), json={}, headers=H(test_access_token_2))).status_code == 404


def test_age_flags_work_without_a_saved_profile():
    today = date(2026, 10, 14)
    assert age_in_years(date(2026, 10, 14), today) == 0 and age_in_years(date(2000, 10, 15), today) == 25
    assert safety_flags(None, date.today() - timedelta(days=365 * 2)) == ["child_under_5"]
    assert safety_flags(None, date.today() - timedelta(days=365 * 70)) == ["elderly_65_plus"]
    assert safety_flags(None, None) == []


@pytest.mark.asyncio
async def test_visit_vitals_are_numbers_with_a_computed_bmi(client, doctor_token, test_patient, test_user):
    base = {"patient_id": test_patient.id, "doctor_id": test_user.id, "visit_date": str(date.today())}
    vitals = {
        "temperature_c": 38.4, "pulse_bpm": 96, "bp_systolic": 130, "bp_diastolic": 85, "respiratory_rate": 18,
        "spo2_percent": 97, "weight_kg": 70, "height_cm": 175, "blood_sugar_mmol": 7.8, "blood_sugar_type": "fasting",
        "pain_score": 4, "red_flags": ["chest_pain"], "referral_urgency": "urgent",
    }
    r = await client.post("/api/v1/appointments/visits", json={**base, **vitals}, headers=H(doctor_token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["temperature_c"], body["bp_systolic"], body["weight_kg"], body["blood_sugar_type"]) == (38.4, 130, 70.0, "fasting")
    assert body["bmi"] == 22.9
    assert body["red_flags"] == ["chest_pain"] and body["referral_urgency"] == "urgent"

    # the history list carries the vitals, so a patient's trend needs no extra requests
    items = (await client.get("/api/v1/appointments/visits", params={"patient_id": test_patient.id}, headers=H(doctor_token))).json()
    assert items[0]["pulse_bpm"] == 96 and items[0]["red_flags"] == ["chest_pain"]

    # no height, no BMI
    r = await client.post("/api/v1/appointments/visits", json={**base, "weight_kg": 70}, headers=H(doctor_token))
    assert r.json()["bmi"] is None


@pytest.mark.asyncio
async def test_implausible_or_inconsistent_vitals_are_refused(client, doctor_token, test_patient, test_user):
    base = {"patient_id": test_patient.id, "doctor_id": test_user.id, "visit_date": str(date.today())}
    post = lambda body: client.post("/api/v1/appointments/visits", json={**base, **body}, headers=H(doctor_token))  # noqa: E731
    for bad in (
        {"temperature_c": 98.6},  # Fahrenheit typed into a Celsius field
        {"pulse_bpm": 700}, {"spo2_percent": 130}, {"pain_score": 11}, {"weight_kg": -3},
        {"bp_systolic": 120},  # one half of a pair
        {"bp_systolic": 80, "bp_diastolic": 120},
        {"blood_sugar_type": "fasting"},  # a type without a value
        {"red_flags": ["made_up_flag"]}, {"referral_urgency": "whenever"},
    ):
        assert (await post(bad)).status_code == 422, bad
    assert (await post({"temperature_c": 37, "bp_systolic": 120, "bp_diastolic": 80})).status_code == 201
