"""Integration regressions for API route path sync."""

from datetime import date, timedelta

import pytest

from app.shared.models import Medicine, MedicineAlias, Symptom, SymptomAlias


@pytest.mark.asyncio
async def test_appointments_endpoint_uses_canonical_path(
    authenticated_client,
    test_patient,
    test_user,
):
    response = await authenticated_client.post(
        "/api/v1/appointments",
        json={
            "patient_id": test_patient.id,
            "doctor_id": test_user.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "11:00:00",
            "duration_minutes": 30,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == test_patient.id

    legacy_response = await authenticated_client.get("/api/v1/appointments/appointments")
    assert legacy_response.status_code == 404


@pytest.mark.asyncio
async def test_medicine_search_endpoint_is_not_captured_by_id_route(
    authenticated_client,
    db_session,
    test_tenant,
    test_user,
):
    medicine = Medicine(
        tenant_id=test_tenant.id,
        name_en="Arnica Montana",
        name_bn="আর্নিকা",
        system="homeopathy",
        category="Plant",
        potency="30C",
        is_active=True,
        created_by=test_user.id,
    )
    db_session.add(medicine)
    await db_session.flush()
    db_session.add(
        MedicineAlias(
            tenant_id=test_tenant.id,
            medicine_id=medicine.id,
            alias_en="Bruise remedy",
            alias_type="common_name",
            is_active=True,
            created_by=test_user.id,
        )
    )
    await db_session.commit()

    response = await authenticated_client.get(
        "/api/v1/medicines/search",
        params={"q": "bruise"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == medicine.id
    assert body[0]["matched_alias"] == "Bruise remedy"


@pytest.mark.asyncio
async def test_symptom_search_endpoint_is_not_captured_by_id_route(
    authenticated_client,
    db_session,
    test_tenant,
    test_user,
):
    symptom = Symptom(
        tenant_id=test_tenant.id,
        name_en="Headache",
        name_bn="মাথাব্যথা",
        description_en=None,
        description_bn=None,
        category="neurological",
        is_global=False,
        is_active=True,
        created_by=test_user.id,
    )
    db_session.add(symptom)
    await db_session.flush()
    db_session.add(
        SymptomAlias(
            tenant_id=test_tenant.id,
            symptom_id=symptom.id,
            alias_en="Migraine",
            alias_type="common_name",
            is_active=True,
            created_by=test_user.id,
        )
    )
    await db_session.commit()

    response = await authenticated_client.get(
        "/api/v1/symptoms/search",
        params={"q": "migraine"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["symptom"]["id"] == symptom.id
    assert body[0]["matched_term"] == "Migraine"
