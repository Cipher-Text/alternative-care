"""Guards on seed_data/pharmacies.json — the data practitioners will phone and drive to."""

import json
import re
from pathlib import Path

import pytest

from app.shared.schemas import PharmacyCreate

SEED = Path(__file__).resolve().parents[2] / "seed_data"
ROWS = json.loads((SEED / "pharmacies.json").read_text(encoding="utf-8"))["pharmacies"]
DISTRICTS = {
    d["name_en"].lower(): d
    for d in json.loads((SEED / "geographic_data.json").read_text(encoding="utf-8"))["districts"]
}
BD_LAT, BD_LON = (20.5, 26.7), (88.0, 92.7)  # Bangladesh's bounding box


def _km(a_lat, a_lon, b_lat, b_lon):
    from math import asin, cos, radians, sin, sqrt

    h = sin(radians(b_lat - a_lat) / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(
        radians(b_lon - a_lon) / 2
    ) ** 2
    return 12742 * asin(sqrt(h))


def test_there_are_fifty_rows():
    assert len(ROWS) == 50


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["name_en"])
def test_each_row_passes_the_api_schema(row):
    body = {k: v for k, v in row.items() if k != "district"}
    PharmacyCreate(**body)  # raises on a bad type, discipline, email, half-pin ...


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["name_en"])
def test_each_row_is_traceable_and_unverified_by_default(row):
    assert re.fullmatch(r"https://\S+", row["source_url"]), "every row must cite an https source"
    assert "is_verified" not in row and "last_confirmed_at" not in row, (
        "seed rows start unverified and unconfirmed; an admin does that"
    )


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["name_en"])
def test_district_exists_and_pin_is_plausibly_inside_it(row):
    district = DISTRICTS.get(row["district"].lower())
    assert district, f"unknown district {row['district']!r} (the seeder resolves by English name)"
    if row["latitude"] is not None:
        assert BD_LAT[0] < row["latitude"] < BD_LAT[1] and BD_LON[0] < row["longitude"] < BD_LON[1]
        # A wrong map link would put the pin in another part of the country
        assert _km(row["latitude"], row["longitude"], district["latitude"], district["longitude"]) < 70


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["name_en"])
def test_phone_numbers_are_well_formed(row):
    assert row["phone"] is None or re.fullmatch(r"\+8801\d{9}", row["phone"]), row["phone"]


def test_names_and_pins_are_unique():
    names = [r["name_en"].lower() for r in ROWS]
    assert len(set(names)) == len(names)
    pins = [(r["latitude"], r["longitude"]) for r in ROWS if r["latitude"] is not None]
    assert len(set(pins)) == len(pins), "two rows share a pin (a copied map link?)"
