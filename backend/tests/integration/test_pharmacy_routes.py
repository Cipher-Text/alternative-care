"""Pharmacy directory: admin-curated, read-only for practitioners, near-me search, CSV import."""

import io
import uuid

import pytest

from app.core.security import create_access_token
from app.shared.models import District, Pharmacy, User

DHAKA = (23.7808, 90.4167)
NEAR_DHAKA = (23.7925, 90.4078)  # ~1.7 km away
MYMENSINGH = (24.7471, 90.4203)  # ~107 km away
CHATTOGRAM = (22.3569, 91.7832)  # ~215 km away — beyond the 200 km maximum radius


def _body(**overrides):
    base = {
        "name_en": "Green Cross Homeo Hall",
        "pharmacy_type": "retail",
        "disciplines": ["homeopathy"],
        "address": "Mitford Road, Dhaka",
        "latitude": DHAKA[0],
        "longitude": DHAKA[1],
        "phone": "01711000000",
    }
    base.update(overrides)
    return base


async def _add(db, **overrides):
    row = Pharmacy(
        **{
            "name_en": "Seed Pharmacy",
            "pharmacy_type": "retail",
            "disciplines": ["homeopathy"],
            **overrides,
        }
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@pytest.fixture
async def district(db_session):
    d = District(id=9001, division_id=1, name_en="Pharmacytest District", name_bn="ঢাকা")
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


class As:
    """A client bound to one user's token — `admin_client` and `authenticated_client` share one
    underlying client object, so using both in a test would overwrite each other's header."""

    def __init__(self, client, token):
        self._c, self._h = client, {"Authorization": f"Bearer {token}"}

    def get(self, *a, **k):
        return self._c.get(*a, headers=self._h, **k)

    def post(self, *a, **k):
        return self._c.post(*a, headers=self._h, **k)

    def patch(self, *a, **k):
        return self._c.patch(*a, headers=self._h, **k)

    def delete(self, *a, **k):
        return self._c.delete(*a, headers=self._h, **k)


@pytest.fixture
def admin_client(client, admin_access_token):
    return As(client, admin_access_token)


@pytest.fixture
def authenticated_client(client, test_access_token):
    return As(client, test_access_token)


def _headers_for(role, tenant_id=None):
    user_id = str(uuid.uuid4())
    token = create_access_token(
        {"sub": user_id, "email": f"{role}@t.test", "role": role, "tenant_id": tenant_id}
    )
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestAccess:
    async def test_admin_creates_and_doctor_reads(self, admin_client, authenticated_client):
        created = await admin_client.post("/api/v1/pharmacies/", json=_body())
        assert created.status_code == 201
        body = created.json()
        assert body["is_verified"] is False
        assert body["last_confirmed_at"] is not None  # whoever enters it has just looked at it

        listed = await authenticated_client.get("/api/v1/pharmacies/")
        assert [p["name_en"] for p in listed.json()] == ["Green Cross Homeo Hall"]
        detail = await authenticated_client.get(f"/api/v1/pharmacies/{body['id']}")
        assert detail.status_code == 200

    async def test_doctor_cannot_write(self, authenticated_client, db_session):
        row = await _add(db_session)
        assert (await authenticated_client.post("/api/v1/pharmacies/", json=_body())).status_code == 403
        assert (
            await authenticated_client.patch(f"/api/v1/pharmacies/{row.id}", json={"name_en": "X"})
        ).status_code == 403
        assert (await authenticated_client.delete(f"/api/v1/pharmacies/{row.id}")).status_code == 403
        files = {"file": ("p.csv", b"name_en\nX", "text/csv")}
        assert (await authenticated_client.post("/api/v1/pharmacies/import", files=files)).status_code == 403

    async def test_receptionist_and_operator_can_read_but_not_write(self, client, test_tenant, db_session):
        await _add(db_session)
        _, rec = _headers_for("receptionist", test_tenant.id)
        _, op = _headers_for("operator")
        for headers in (rec, op):
            assert (await client.get("/api/v1/pharmacies/", headers=headers)).status_code == 200
            assert (
                await client.post("/api/v1/pharmacies/", json=_body(), headers=headers)
            ).status_code == 403

    async def test_requires_login(self, client):
        client.headers.pop("Authorization", None)
        assert (await client.get("/api/v1/pharmacies/")).status_code in (401, 403)

    async def test_unknown_id_is_404(self, authenticated_client):
        assert (await authenticated_client.get("/api/v1/pharmacies/999999")).status_code == 404


@pytest.mark.asyncio
class TestFilters:
    async def test_search_discipline_district_delivery_and_type(
        self, authenticated_client, db_session, district
    ):
        await _add(db_session, name_en="Alpha Homeo", name_bn="আলফা হোমিও", district_id=district.id,
                   delivers=True, address="Farmgate")
        await _add(db_session, name_en="Beta Unani", disciplines=["unani"], pharmacy_type="wholesale")
        get = authenticated_client.get

        assert [p["name_en"] for p in (await get("/api/v1/pharmacies/", params={"search": "alpha"})).json()] == ["Alpha Homeo"]
        assert len((await get("/api/v1/pharmacies/", params={"search": "আলফা"})).json()) == 1
        assert len((await get("/api/v1/pharmacies/", params={"search": "farmgate"})).json()) == 1
        assert [p["name_en"] for p in (await get("/api/v1/pharmacies/", params={"discipline": "unani"})).json()] == ["Beta Unani"]
        assert len((await get("/api/v1/pharmacies/", params={"district_id": district.id})).json()) == 1
        assert [p["name_en"] for p in (await get("/api/v1/pharmacies/", params={"delivers": True})).json()] == ["Alpha Homeo"]
        assert [p["name_en"] for p in (await get("/api/v1/pharmacies/", params={"pharmacy_type": "wholesale"})).json()] == ["Beta Unani"]

    async def test_pagination_does_not_overlap(self, authenticated_client, db_session):
        for i in range(5):
            await _add(db_session, name_en=f"Paged {i}")
        seen = []
        for offset in (0, 2, 4):
            page = await authenticated_client.get("/api/v1/pharmacies/", params={"limit": 2, "offset": offset})
            seen.extend(p["id"] for p in page.json())
        assert len(seen) == 5 and len(set(seen)) == 5

    async def test_deactivated_listings_are_hidden(self, admin_client, authenticated_client, db_session):
        row = await _add(db_session, name_en="Closing Down")
        assert (await admin_client.delete(f"/api/v1/pharmacies/{row.id}")).status_code == 204
        assert (await authenticated_client.get("/api/v1/pharmacies/")).json() == []
        inactive = await authenticated_client.get("/api/v1/pharmacies/", params={"is_active": False})
        assert [p["name_en"] for p in inactive.json()] == ["Closing Down"]


@pytest.mark.asyncio
class TestNearMe:
    async def test_returns_nearest_first_within_radius_with_distance(
        self, authenticated_client, db_session
    ):
        await _add(db_session, name_en="Near", latitude=NEAR_DHAKA[0], longitude=NEAR_DHAKA[1])
        await _add(db_session, name_en="Here", latitude=DHAKA[0], longitude=DHAKA[1])
        await _add(db_session, name_en="Far", latitude=MYMENSINGH[0], longitude=MYMENSINGH[1])
        await _add(db_session, name_en="Too far", latitude=CHATTOGRAM[0], longitude=CHATTOGRAM[1])
        await _add(db_session, name_en="No pin")

        r = await authenticated_client.get(
            "/api/v1/pharmacies/", params={"lat": DHAKA[0], "lon": DHAKA[1], "radius_km": 10}
        )
        assert r.status_code == 200, r.text
        rows = r.json()
        assert [p["name_en"] for p in rows] == ["Here", "Near"]
        assert rows[0]["distance_km"] == 0.0
        assert 1.0 < rows[1]["distance_km"] < 2.5

        wide = await authenticated_client.get(
            "/api/v1/pharmacies/", params={"lat": DHAKA[0], "lon": DHAKA[1], "radius_km": 200}
        )
        names = [p["name_en"] for p in wide.json()]
        far = [p for p in wide.json() if p["name_en"] == "Far"][0]
        assert 100 < far["distance_km"] < 115  # Dhaka -> Mymensingh is ~107 km by air
        assert names[-1] == "Far"  # nearest first, so the farthest is last
        assert "Too far" not in names and "No pin" not in names

    async def test_without_a_location_distance_is_absent(self, authenticated_client, db_session):
        await _add(db_session, latitude=DHAKA[0], longitude=DHAKA[1])
        rows = (await authenticated_client.get("/api/v1/pharmacies/")).json()
        assert rows[0]["distance_km"] is None

    async def test_lat_without_lon_is_rejected(self, authenticated_client):
        r = await authenticated_client.get("/api/v1/pharmacies/", params={"lat": 23.7})
        assert r.status_code == 422

    @pytest.mark.parametrize("params", [{"lat": 91, "lon": 90}, {"lat": 23, "lon": 181}, {"lat": 23, "lon": 90, "radius_km": 0}, {"lat": 23, "lon": 90, "radius_km": 201}])
    async def test_out_of_range_inputs_are_rejected(self, authenticated_client, params):
        assert (await authenticated_client.get("/api/v1/pharmacies/", params=params)).status_code == 422


@pytest.mark.asyncio
class TestPinValidation:
    async def test_create_requires_both_coordinates_or_neither(self, admin_client):
        assert (await admin_client.post("/api/v1/pharmacies/", json=_body(longitude=None))).status_code == 422
        assert (await admin_client.post("/api/v1/pharmacies/", json=_body(latitude=95))).status_code == 422
        no_pin = await admin_client.post("/api/v1/pharmacies/", json=_body(latitude=None, longitude=None))
        assert no_pin.status_code == 201

    async def test_partial_update_cannot_leave_half_a_pin(self, admin_client, db_session):
        row = await _add(db_session)  # no pin
        r = await admin_client.patch(f"/api/v1/pharmacies/{row.id}", json={"latitude": 23.7})
        assert r.status_code == 422
        both = await admin_client.patch(f"/api/v1/pharmacies/{row.id}", json={"latitude": 23.7, "longitude": 90.4})
        assert both.status_code == 200

    async def test_rejects_bad_type_discipline_and_email(self, admin_client):
        assert (await admin_client.post("/api/v1/pharmacies/", json=_body(pharmacy_type="kiosk"))).status_code == 422
        assert (await admin_client.post("/api/v1/pharmacies/", json=_body(disciplines=[]))).status_code == 422
        assert (await admin_client.post("/api/v1/pharmacies/", json=_body(disciplines=["reiki"]))).status_code == 422
        assert (await admin_client.post("/api/v1/pharmacies/", json=_body(email="not-an-email"))).status_code == 422


@pytest.mark.asyncio
class TestVerification:
    async def test_verifying_stamps_who_and_when(self, admin_client, platform_admin, db_session):
        row = await _add(db_session)
        r = await admin_client.patch(f"/api/v1/pharmacies/{row.id}", json={"is_verified": True})
        body = r.json()
        assert body["is_verified"] is True
        assert body["verified_by"] == platform_admin.id
        assert body["verified_at"] and body["last_confirmed_at"]

    async def test_mark_confirmed_restamps_freshness_only(self, admin_client, db_session):
        row = await _add(db_session)
        assert row.last_confirmed_at is None
        r = await admin_client.patch(f"/api/v1/pharmacies/{row.id}", json={"mark_confirmed": True})
        body = r.json()
        assert body["last_confirmed_at"] is not None
        assert body["is_verified"] is False and body["verified_at"] is None


def _csv(*lines):
    header = "name_en,name_bn,pharmacy_type,disciplines,address,district,latitude,longitude,phone,delivers"
    return ("\n".join([header, *lines]) + "\n").encode("utf-8")


async def _import(client, data: bytes):
    return await client.post(
        "/api/v1/pharmacies/import",
        files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
    )


@pytest.mark.asyncio
class TestCsvImport:
    async def test_imports_valid_rows_including_bengali_and_multi_discipline(
        self, admin_client, authenticated_client, district
    ):
        data = _csv(
            "Alpha Homeo,আলফা হোমিও,retail,homeopathy;unani,Farmgate,Pharmacytest District,23.76,90.39,0171,yes",
            "Beta Wholesale,,wholesale,herbal,,,,,,",
        )
        r = await _import(admin_client, data)
        assert r.status_code == 200
        assert r.json() == {"created": 2, "skipped": 0, "errors": []}

        rows = {p["name_en"]: p for p in (await authenticated_client.get("/api/v1/pharmacies/")).json()}
        alpha = rows["Alpha Homeo"]
        assert alpha["name_bn"] == "আলফা হোমিও"
        assert sorted(alpha["disciplines"]) == ["homeopathy", "unani"]
        assert alpha["district_id"] == district.id and alpha["delivers"] is True
        assert rows["Beta Wholesale"]["latitude"] is None

    async def test_is_all_or_nothing_and_reports_every_bad_row_with_its_line(
        self, admin_client, authenticated_client
    ):
        data = _csv(
            "Good One,,retail,homeopathy,,,,,,",
            "Bad Type,,kiosk,homeopathy,,,,,,",
            "Bad District,,retail,unani,,Atlantis,,,,",
            "Half Pin,,retail,unani,,,23.7,,,",
            "Not A Number,,retail,unani,,,abc,90,,",
        )
        r = await _import(admin_client, data)
        body = r.json()
        assert body["created"] == 0
        assert sorted(e["row"] for e in body["errors"]) == [3, 4, 5, 6]
        assert any("Atlantis" in e["message"] for e in body["errors"])
        # messages are short and readable, not a pydantic dump with a docs link
        for e in body["errors"]:
            assert "pydantic.dev" not in e["message"] and "\n" not in e["message"], e
        assert any("pharmacy_type" in e["message"] for e in body["errors"] if e["row"] == 3)
        assert (await authenticated_client.get("/api/v1/pharmacies/")).json() == []  # nothing saved

    async def test_reuploading_skips_existing_rows(self, admin_client):
        data = _csv("Same Name,,retail,homeopathy,,,,,,", "Same Name,,retail,homeopathy,,,,,,")
        first = (await _import(admin_client, data)).json()
        assert first["created"] == 1 and first["skipped"] == 1  # duplicate inside the file too
        again = (await _import(admin_client, data)).json()
        assert again["created"] == 0 and again["skipped"] == 2

    async def test_accepts_excel_bom_and_rejects_non_utf8_or_missing_header(self, admin_client):
        bom = b"\xef\xbb\xbf" + _csv("Bom Pharmacy,,retail,herbal,,,,,,")
        assert (await _import(admin_client, bom)).json()["created"] == 1
        assert (await _import(admin_client, "name_en\nশ".encode("utf-16"))).status_code == 422
        assert (await _import(admin_client, b"foo,bar\n1,2\n")).status_code == 422

    async def test_row_cap(self, admin_client):
        lines = [f"P{i},,retail,herbal,,,,,," for i in range(1001)]
        assert (await _import(admin_client, _csv(*lines))).status_code == 422
