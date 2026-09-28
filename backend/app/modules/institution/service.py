"""College catalog service — admin-curated, always-global institution directory."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import College
from app.shared.schemas import CollegeCreate, CollegeUpdate


class CollegeService:
    """
    No tenant scoping — colleges aren't tenants (ADR-008,
    docs/planning/future-scope-2026-09.md Track D), so every row is visible
    to every caller, unlike Medicine/Symptom's hybrid global-or-tenant model.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_colleges(
        self,
        discipline: str | None = None,
        college_type: str | None = None,
        district_id: int | None = None,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[College]:
        """List colleges, optionally filtered by discipline, type, or district."""
        query = select(College)

        if discipline:
            query = query.where(College.disciplines.any(discipline))

        if college_type:
            query = query.where(College.college_type == college_type)

        if district_id is not None:
            query = query.where(College.district_id == district_id)

        if is_active is not None:
            query = query.where(College.is_active == is_active)

        query = query.order_by(College.name_en).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_college(self, college_id: int) -> College:
        """Get a college by ID."""
        result = await self.db.execute(select(College).where(College.id == college_id))
        college = result.scalar_one_or_none()

        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="College not found"
            )

        return college

    async def create_college(self, data: CollegeCreate, created_by: str) -> College:
        """Create a college. Admin-only at the route level."""
        college = College(**data.model_dump(), created_by=created_by)

        self.db.add(college)
        await self.db.commit()
        await self.db.refresh(college)

        return college

    async def update_college(
        self, college_id: int, data: CollegeUpdate, updated_by: str
    ) -> College:
        """Update a college. Admin-only at the route level."""
        college = await self.get_college(college_id)

        update_data = data.model_dump(exclude_unset=True)
        newly_verified = update_data.get("is_verified") is True and not college.is_verified

        for field, value in update_data.items():
            setattr(college, field, value)

        if newly_verified:
            college.verified_at = datetime.now(timezone.utc)
            college.verified_by = updated_by

        college.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(college)

        return college

    async def deactivate_college(self, college_id: int, updated_by: str) -> None:
        """Deactivate a college. Admin-only at the route level."""
        college = await self.get_college(college_id)

        college.is_active = False
        college.updated_by = updated_by

        await self.db.commit()
