"""System-specific case-taking: the registry, its labels, and the endpoints (homeopathy)."""

import json
import uuid
from datetime import date
from pathlib import Path

import pytest

from app.core.security import create_access_token, get_password_hash
from app.shared.case_taking import CaseValidationError, definitions, validate
from app.shared.case_taking.systems import SYSTEMS
from app.shared.models import User

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
MESSAGES = Path(__file__).resolve().parents[3] / "frontend" / "src" / "messages"
HOMEO = SYSTEMS["homeopathy"]


def _labels(lang: str) -> dict:
    return json.loads((MESSAGES / lang / "caseTaking.json").read_text(encoding="utf-8"))["caseTakingUi"]["homeopathy"]


@pytest.mark.parametrize("lang", ["en", "bn"])
def test_every_field_group_and_option_has_a_label(lang):
    labels = _labels(lang)
    assert labels["title"]
    assert {g for g, _ in HOMEO.groups} == set(labels["groups"])
    assert len({f.key for f in HOMEO.fields}) == len(HOMEO.fields)  # keys are unique
    for f in HOMEO.fields:
        entry = labels["fields"][f.key]
        assert entry["label"].strip(), f.key
        assert f.group in labels["groups"], f.key
        for code in f.options or f.units:
            assert entry["options"][code].strip(), (f.key, code)
        for column in f.columns:
            assert entry["columns"][column.key].strip(), (f.key, column.key)
            for code in column.options:
                assert entry["options"][code].strip(), (f.key, code)
    # no label for a field that no longer exists
    assert set(labels["fields"]) == {f.key for f in HOMEO.fields}


def test_validate_cleans_and_refuses():
    ok = validate(HOMEO, "visit", {
        "duration": {"value": 3, "unit": "weeks"}, "worse_from": ["night", "cold", "night"], "location": " head ",
        "side_affected": "", "sensation": [], "remedy": "Belladonna",
    })
    assert ok == {"duration": {"value": 3, "unit": "weeks"}, "worse_from": ["night", "cold"], "location": "head", "remedy": "Belladonna"}

    with pytest.raises(CaseValidationError) as e:
        validate(HOMEO, "patient", {
            "thermal_state": "lukewarm", "nope": 1, "fears": ["dark", "ghosts"], "previous_remedies": [{"remedy": "Nux", "response": "meh"}],
        })
    assert set(e.value.errors) == {"thermal_state", "nope", "fears", "previous_remedies"}
    # a visit-scoped key is not valid on the patient form, and the other way round
    with pytest.raises(CaseValidationError):
        validate(HOMEO, "patient", {"remedy": "Belladonna"})
    with pytest.raises(CaseValidationError):
        validate(HOMEO, "visit", {"thermal_state": "chilly"})
    for bad in ({"value": 0, "unit": "days"}, {"value": 5, "unit": "fortnights"}, {"value": True, "unit": "days"}, {"value": 2}, "3 days"):
        with pytest.raises(CaseValidationError):
            validate(HOMEO, "visit", {"duration": bad})
    with pytest.raises(CaseValidationError):
        validate(HOMEO, "visit", {"location": "x" * 501})
    with pytest.raises(CaseValidationError):
        validate(HOMEO, "patient", {"previous_remedies": [{"remedy": "x"}] * 21})


def test_definitions_describe_the_forms():
    d = definitions(HOMEO)
    assert d["system"] == "homeopathy" and d["schema_version"] == 1
    assert [g["key"] for g in d["groups"]] == ["complaint", "generals", "mind", "history", "prescription"]
    by_key = {f["key"]: f for f in d["fields"]}
    assert by_key["thermal_state"]["options"] == ["chilly", "hot", "ambithermal"] and by_key["thermal_state"]["scope"] == "patient"
    assert by_key["duration"]["type"] == "quantity" and by_key["duration"]["units"] == ["days", "weeks", "months", "years"]
    assert [c["key"] for c in by_key["previous_remedies"]["columns"]] == ["remedy", "potency", "response"]
    assert by_key["remedy"]["scope"] == "visit" and by_key["remedy"]["max_length"] == 500


@pytest.mark.asyncio
async def test_definitions_endpoint(client, doctor_token):
    r = await client.get("/api/v1/case-taking/homeopathy", headers=H(doctor_token))
    assert r.status_code == 200 and r.json()["system"] == "homeopathy" and len(r.json()["fields"]) == 38
    assert (await client.get("/api/v1/case-taking/ayurvedic", headers=H(doctor_token))).status_code == 404
    assert (await client.get("/api/v1/case-taking/homeopathy")).status_code == 401


@pytest.mark.asyncio
async def test_patient_case_profile_round_trip(client, doctor_token, test_patient):
    url = f"/api/v1/case-taking/patients/{test_patient.id}/homeopathy"
    empty = (await client.get(url, headers=H(doctor_token))).json()
    assert empty["exists"] is False and empty["data"] == {} and empty["updated_at"] is None

    body = {"data": {
        "thermal_state": "chilly", "thirst": "large", "food_desires": ["sweet", "salty"], "fears": ["dark"],
        "previous_remedies": [{"remedy": "Nux vomica", "potency": "30C", "response": "better"}, {}],
        "dominant_miasm": "psora",
    }}
    r = await client.put(url, json=body, headers=H(doctor_token))
    assert r.status_code == 200, r.text
    saved = r.json()
    assert saved["exists"] is True and saved["updated_at"] is not None
    assert saved["data"]["previous_remedies"] == [{"remedy": "Nux vomica", "potency": "30C", "response": "better"}]  # the empty row is dropped
    assert (await client.get(url, headers=H(doctor_token))).json()["data"]["food_desires"] == ["sweet", "salty"]

    # a second save replaces rather than merges
    r = await client.put(url, json={"data": {"thermal_state": "hot"}}, headers=H(doctor_token))
    assert r.json()["data"] == {"thermal_state": "hot"}

    # bad answers are refused with the field named, and nothing is changed
    r = await client.put(url, json={"data": {"thermal_state": "lukewarm", "remedy": "x"}}, headers=H(doctor_token))
    assert r.status_code == 422
    assert set(r.json()["detail"]["errors"]) == {"thermal_state", "remedy"}
    assert (await client.get(url, headers=H(doctor_token))).json()["data"] == {"thermal_state": "hot"}


@pytest.mark.asyncio
async def test_visit_assessment_round_trip(client, doctor_token, test_patient, test_user):
    visit = (await client.post("/api/v1/appointments/visits", headers=H(doctor_token), json={
        "patient_id": test_patient.id, "doctor_id": test_user.id, "visit_date": str(date.today()),
    })).json()
    url = f"/api/v1/case-taking/visits/{visit['id']}/homeopathy"
    assert (await client.get(url, headers=H(doctor_token))).json()["exists"] is False

    body = {"data": {
        "location": "Right temple", "sensation": ["throbbing"], "duration": {"value": 3, "unit": "days"}, "worse_from": ["heat", "motion"],
        "better_from": ["rest"], "remedy": "Belladonna", "potency": "200c", "repetition": "twice_daily", "avoid": ["coffee", "camphor"],
    }}
    r = await client.put(url, json=body, headers=H(doctor_token))
    assert r.status_code == 200, r.text
    assert r.json()["patient_id"] == test_patient.id and r.json()["visit_id"] == visit["id"]
    assert (await client.get(url, headers=H(doctor_token))).json()["data"]["worse_from"] == ["heat", "motion"]
    # a patient-scoped answer does not belong on a visit
    assert (await client.put(url, json={"data": {"thermal_state": "chilly"}}, headers=H(doctor_token))).status_code == 422


@pytest.mark.asyncio
async def test_receptionist_reads_but_cannot_write_and_other_clinics_see_nothing(
    client, doctor_token, test_access_token_2, test_patient, test_user, db_session, test_tenant
):
    visit = (await client.post("/api/v1/appointments/visits", headers=H(doctor_token), json={
        "patient_id": test_patient.id, "doctor_id": test_user.id, "visit_date": str(date.today()),
    })).json()
    rec = User(id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="rec.case@example.com", full_name="Rec", role="receptionist",
               password_hash=get_password_hash("Test@1234"), is_active=True)
    db_session.add(rec)
    await db_session.commit()
    token = create_access_token({"sub": rec.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": rec.email, "plan": "pro"})
    p_url = f"/api/v1/case-taking/patients/{test_patient.id}/homeopathy"
    v_url = f"/api/v1/case-taking/visits/{visit['id']}/homeopathy"
    assert (await client.get(p_url, headers=H(token))).status_code == 200
    assert (await client.put(p_url, json={"data": {}}, headers=H(token))).status_code == 403
    assert (await client.put(v_url, json={"data": {}}, headers=H(token))).status_code == 403
    # another clinic cannot reach this patient or visit
    for url in (p_url, v_url):
        assert (await client.get(url, headers=H(test_access_token_2))).status_code == 404
        assert (await client.put(url, json={"data": {}}, headers=H(test_access_token_2))).status_code == 404
