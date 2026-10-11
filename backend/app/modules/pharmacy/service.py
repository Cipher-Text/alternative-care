"""Pharmacy directory service — admin-curated, always-global (no tenant scoping)."""

import csv
import io
import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import District, Pharmacy
from app.shared.schemas import (
    PharmacyCreate,
    PharmacyImportResult,
    PharmacyImportRowError,
    PharmacyUpdate,
)

EARTH_RADIUS_KM = 6371.0
KM_PER_DEGREE_LAT = 111.32

MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 1000
IMPORT_COLUMNS = (
    "name_en,name_bn,pharmacy_type,disciplines,address,district,latitude,longitude,phone,"
    "whatsapp,email,website_url,opening_hours,delivers,notes_en,notes_bn,source_url"
)
_TRUE = {"1", "true", "yes", "y"}


def distance_km_expr(lat: float, lon: float):
    """Great-circle (haversine/spherical law of cosines) distance in km, as a SQL expression."""
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    cos_angle = func.cos(lat_r) * func.cos(func.radians(Pharmacy.latitude)) * func.cos(
        func.radians(Pharmacy.longitude) - lon_r
    ) + math.sin(lat_r) * func.sin(func.radians(Pharmacy.latitude))
    # rounding can push the value a hair past 1, which would make acos() error
    return EARTH_RADIUS_KM * func.acos(func.least(1.0, func.greatest(-1.0, cos_angle)))


class PharmacyService:
    """No tenant scoping: every row is visible to every authenticated caller."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_pharmacies(
        self,
        search: str | None = None,
        discipline: str | None = None,
        pharmacy_type: str | None = None,
        district_id: int | None = None,
        delivers: bool | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float = 10,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Pharmacy]:
        """
        List pharmacies. With `lat` and `lon`, only listings with a pin inside `radius_km` are
        returned, nearest first, each carrying `distance_km`; otherwise ordered by name.
        """
        near_me = lat is not None and lon is not None
        distance = distance_km_expr(lat, lon) if near_me else None

        query = select(Pharmacy, distance.label("distance_km")) if near_me else select(Pharmacy)

        if is_active is not None:
            query = query.where(Pharmacy.is_active == is_active)
        if discipline:
            query = query.where(Pharmacy.disciplines.any(discipline))
        if pharmacy_type:
            query = query.where(Pharmacy.pharmacy_type == pharmacy_type)
        if district_id is not None:
            query = query.where(Pharmacy.district_id == district_id)
        if delivers is not None:
            query = query.where(Pharmacy.delivers == delivers)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Pharmacy.name_en.ilike(pattern),
                    Pharmacy.name_bn.ilike(pattern),
                    Pharmacy.address.ilike(pattern),
                )
            )

        if near_me:
            # Cheap bounding box first (uses the lat/lon index), exact distance second
            lat_delta = radius_km / KM_PER_DEGREE_LAT
            lon_delta = radius_km / (KM_PER_DEGREE_LAT * max(math.cos(math.radians(lat)), 0.01))
            query = query.where(
                Pharmacy.latitude.between(lat - lat_delta, lat + lat_delta),
                Pharmacy.longitude.between(lon - lon_delta, lon + lon_delta),
                distance <= radius_km,
            ).order_by(distance, Pharmacy.id)
        else:
            query = query.order_by(Pharmacy.name_en, Pharmacy.id)

        result = await self.db.execute(query.limit(limit).offset(offset))

        if not near_me:
            return list(result.scalars().all())

        rows = []
        for pharmacy, km in result.all():
            pharmacy.distance_km = round(float(km), 2)
            rows.append(pharmacy)
        return rows

    async def get_pharmacy(self, pharmacy_id: int) -> Pharmacy:
        result = await self.db.execute(select(Pharmacy).where(Pharmacy.id == pharmacy_id))
        pharmacy = result.scalar_one_or_none()
        if not pharmacy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pharmacy not found")
        return pharmacy

    async def create_pharmacy(self, data: PharmacyCreate, created_by: str) -> Pharmacy:
        pharmacy = Pharmacy(
            **data.model_dump(),
            created_by=created_by,
            # Whoever enters a listing has just looked at it
            last_confirmed_at=datetime.now(timezone.utc),
        )
        self.db.add(pharmacy)
        await self.db.commit()
        await self.db.refresh(pharmacy)
        return pharmacy

    async def update_pharmacy(
        self, pharmacy_id: int, data: PharmacyUpdate, updated_by: str
    ) -> Pharmacy:
        pharmacy = await self.get_pharmacy(pharmacy_id)

        update_data = data.model_dump(exclude_unset=True)
        mark_confirmed = update_data.pop("mark_confirmed", None)
        newly_verified = update_data.get("is_verified") is True and not pharmacy.is_verified

        # The pin is only valid as a pair, even across partial updates — checked before anything
        # is changed so a rejected request leaves the record untouched
        new_lat = update_data.get("latitude", pharmacy.latitude)
        new_lon = update_data.get("longitude", pharmacy.longitude)
        if (new_lat is None) != (new_lon is None):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="latitude and longitude must be set together",
            )

        for field, value in update_data.items():
            setattr(pharmacy, field, value)

        now = datetime.now(timezone.utc)
        if newly_verified:
            pharmacy.verified_at = now
            pharmacy.verified_by = updated_by
        if mark_confirmed or newly_verified:
            pharmacy.last_confirmed_at = now
        pharmacy.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(pharmacy)
        return pharmacy

    async def deactivate_pharmacy(self, pharmacy_id: int, updated_by: str) -> None:
        pharmacy = await self.get_pharmacy(pharmacy_id)
        pharmacy.is_active = False
        pharmacy.updated_by = updated_by
        await self.db.commit()

    # ===== CSV import =====

    async def import_csv(self, raw: bytes, created_by: str) -> PharmacyImportResult:
        """
        Bulk-create pharmacies from a CSV (header row required; columns: IMPORT_COLUMNS).

        All-or-nothing: every row is validated first and, if any row is invalid, nothing is saved
        and the per-row errors are returned. Rows that already exist (same name in the same
        district, case-insensitive) are skipped, so re-uploading a corrected file is safe.
        """
        if len(raw) > MAX_IMPORT_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"CSV is larger than {MAX_IMPORT_BYTES // (1024 * 1024)} MB",
            )
        try:
            text = raw.decode("utf-8-sig")  # tolerate the BOM Excel adds
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CSV must be UTF-8 encoded (needed for Bengali text)",
            )

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or "name_en" not in reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CSV needs a header row with at least name_en. Columns: {IMPORT_COLUMNS}",
            )
        rows = list(reader)
        if len(rows) > MAX_IMPORT_ROWS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"At most {MAX_IMPORT_ROWS} rows per import",
            )

        districts = {
            name.strip().lower(): district_id
            for district_id, name in (
                await self.db.execute(select(District.id, District.name_en))
            ).all()
        }

        parsed: list[tuple[int, PharmacyCreate]] = []
        errors: list[PharmacyImportRowError] = []

        for line, row in enumerate(rows, start=2):
            try:
                parsed.append((line, self._parse_row(row, districts)))
            except ValidationError as exc:
                # Must come before ValueError: pydantic's ValidationError is a ValueError, and its
                # str() is a multi-line dump with a docs URL, not something to show an admin
                detail = "; ".join(
                    f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
                )
                errors.append(PharmacyImportRowError(row=line, message=detail))
            except ValueError as exc:
                errors.append(PharmacyImportRowError(row=line, message=str(exc)))

        if errors:
            return PharmacyImportResult(created=0, skipped=0, errors=errors)

        existing = {
            (name.lower(), district_id)
            for name, district_id in (
                await self.db.execute(select(Pharmacy.name_en, Pharmacy.district_id))
            ).all()
        }

        created = skipped = 0
        now = datetime.now(timezone.utc)
        for _, data in parsed:
            key = (data.name_en.lower(), data.district_id)
            if key in existing:
                skipped += 1
                continue
            existing.add(key)  # also catches duplicates inside the same file
            self.db.add(
                Pharmacy(**data.model_dump(), created_by=created_by, last_confirmed_at=now)
            )
            created += 1

        await self.db.commit()
        return PharmacyImportResult(created=created, skipped=skipped, errors=[])

    @staticmethod
    def _parse_row(row: dict, districts: dict[str, int]) -> PharmacyCreate:
        def cell(name: str) -> str | None:
            value = (row.get(name) or "").strip()
            return value or None

        district_name = cell("district")
        district_id = None
        if district_name:
            district_id = districts.get(district_name.lower())
            if district_id is None:
                raise ValueError(f"unknown district '{district_name}'")

        def number(name: str) -> float | None:
            value = cell(name)
            if value is None:
                return None
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"{name} '{value}' is not a number")

        disciplines = [d.strip().lower() for d in (cell("disciplines") or "").replace("|", ";").split(";") if d.strip()]

        return PharmacyCreate(
            name_en=cell("name_en") or "",
            name_bn=cell("name_bn"),
            pharmacy_type=(cell("pharmacy_type") or "").lower(),
            disciplines=disciplines,
            address=cell("address"),
            district_id=district_id,
            latitude=number("latitude"),
            longitude=number("longitude"),
            phone=cell("phone"),
            whatsapp=cell("whatsapp"),
            email=cell("email"),
            website_url=cell("website_url"),
            opening_hours=cell("opening_hours"),
            delivers=(cell("delivers") or "").lower() in _TRUE,
            notes_en=cell("notes_en"),
            notes_bn=cell("notes_bn"),
            source_url=cell("source_url"),
        )
