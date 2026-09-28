"""Institution catalog service — admin-curated, always-global institution directory."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Institution
from app.shared.schemas import InstitutionCreate, InstitutionUpdate


class InstitutionService:
    """
    No tenant scoping — institutions aren't tenants (ADR-008,
    docs/planning/future-scope-2026-09.md Track D), so every row is visible
    to every caller, unlike Medicine/Symptom's hybrid global-or-tenant model.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_institutions(
        self,
        discipline: str | None = None,
        institution_type: str | None = None,
        district_id: int | None = None,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Institution]:
        """List institutions, optionally filtered by discipline, type, or district."""
        query = select(Institution)

        if discipline:
            query = query.where(Institution.disciplines.any(discipline))

        if institution_type:
            query = query.where(Institution.institution_type == institution_type)

        if district_id is not None:
            query = query.where(Institution.district_id == district_id)

        if is_active is not None:
            query = query.where(Institution.is_active == is_active)

        query = query.order_by(Institution.name_en).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_institution(self, institution_id: int) -> Institution:
        """Get an institution by ID."""
        result = await self.db.execute(
            select(Institution).where(Institution.id == institution_id)
        )
        institution = result.scalar_one_or_none()

        if not institution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found"
            )

        return institution

    async def create_institution(self, data: InstitutionCreate, created_by: str) -> Institution:
        """Create an institution. Admin-only at the route level."""
        institution = Institution(**data.model_dump(), created_by=created_by)

        self.db.add(institution)
        await self.db.commit()
        await self.db.refresh(institution)

        return institution

    async def update_institution(
        self, institution_id: int, data: InstitutionUpdate, updated_by: str
    ) -> Institution:
        """Update an institution. Admin-only at the route level."""
        institution = await self.get_institution(institution_id)

        update_data = data.model_dump(exclude_unset=True)
        newly_verified = update_data.get("is_verified") is True and not institution.is_verified

        for field, value in update_data.items():
            setattr(institution, field, value)

        if newly_verified:
            institution.verified_at = datetime.now(timezone.utc)
            institution.verified_by = updated_by

        institution.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(institution)

        return institution

    async def deactivate_institution(self, institution_id: int, updated_by: str) -> None:
        """Deactivate an institution. Admin-only at the route level."""
        institution = await self.get_institution(institution_id)

        institution.is_active = False
        institution.updated_by = updated_by

        await self.db.commit()
