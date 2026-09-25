"""Symptom service - business logic for the symptom catalog and aliases."""

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select

from app.core.base_service import GlobalCatalogService
from app.shared.models import Symptom, SymptomAlias
from app.shared.schemas import (
    SymptomAliasCreate,
    SymptomCreate,
    SymptomSearchResult,
    SymptomUpdate,
)


class SymptomService(GlobalCatalogService[Symptom]):
    """Symptom catalog service — global-or-tenant symptoms and aliases."""

    model = Symptom

    # ========================================================================
    # Symptom CRUD
    # ========================================================================

    async def list_symptoms(
        self,
        category: str | None = None,
        is_global: bool | None = None,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Symptom]:
        """List symptoms visible to the caller (global + tenant-specific)."""
        query = self._visible_query()

        if category:
            query = query.where(Symptom.category == category)

        if is_global is not None:
            query = query.where(Symptom.is_global == is_global)

        if is_active is not None:
            query = query.where(Symptom.is_active == is_active)

        query = query.order_by(Symptom.name_en).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_symptom(
        self, data: SymptomCreate, created_by: str, role: str
    ) -> Symptom:
        """Create a symptom. Only admins can create global ones."""
        if data.is_global and role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create global symptoms",
            )

        symptom = Symptom(
            **data.model_dump(),
            tenant_id=None if data.is_global else self.tenant_id,
            created_by=created_by,
        )

        self.db.add(symptom)
        await self.db.commit()
        await self.db.refresh(symptom)

        return symptom

    async def get_symptom(self, symptom_id: int) -> Symptom:
        """Get symptom details (global or own-tenant)."""
        return await self.get_visible_or_404(symptom_id, detail="Symptom not found")

    async def update_symptom(
        self, symptom_id: int, data: SymptomUpdate, updated_by: str
    ) -> Symptom:
        """Update a tenant-owned symptom (not global)."""
        symptom = await self.get_own_or_404(
            symptom_id, detail="Symptom not found or cannot be updated"
        )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(symptom, field, value)

        symptom.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(symptom)

        return symptom

    async def deactivate_symptom(self, symptom_id: int, updated_by: str) -> None:
        """Deactivate a tenant-owned symptom (not global)."""
        symptom = await self.get_own_or_404(
            symptom_id, detail="Symptom not found or cannot be deleted"
        )

        symptom.is_active = False
        symptom.updated_by = updated_by
        await self.db.commit()

    # ========================================================================
    # Symptom Search
    # ========================================================================

    async def search_symptoms(
        self, q: str, category: str | None = None, limit: int = 20
    ) -> list[SymptomSearchResult]:
        """Search symptoms by name or alias, with autocomplete-style ranking."""
        search_term = f"%{q.lower()}%"

        name_query = self._visible_query().where(
            Symptom.is_active == True,  # noqa: E712
            or_(
                func.lower(Symptom.name_en).like(search_term),
                func.lower(Symptom.name_bn).like(search_term),
            ),
        )

        if category:
            name_query = name_query.where(Symptom.category == category)

        name_results = await self.db.execute(name_query.limit(limit))
        symptoms_from_name = name_results.scalars().all()

        alias_query = (
            select(Symptom, SymptomAlias.alias_en)
            .join(SymptomAlias, Symptom.id == SymptomAlias.symptom_id)
            .where(
                Symptom.is_active == True,  # noqa: E712
                SymptomAlias.is_active == True,  # noqa: E712
                or_(Symptom.is_global == True, Symptom.tenant_id == self.tenant_id),  # noqa: E712
                or_(
                    func.lower(SymptomAlias.alias_en).like(search_term),
                    func.lower(SymptomAlias.alias_bn).like(search_term),
                ),
            )
        )

        if category:
            alias_query = alias_query.where(Symptom.category == category)

        alias_results = await self.db.execute(alias_query.limit(limit))
        symptoms_from_alias = [(symptom, alias) for symptom, alias in alias_results.all()]

        results: list[SymptomSearchResult] = []

        for symptom in symptoms_from_name:
            results.append(
                SymptomSearchResult(
                    symptom=symptom,
                    matched_term=symptom.name_en,
                    match_type="exact",
                    relevance_score=1.0,
                )
            )

        for symptom, matched_alias in symptoms_from_alias:
            if symptom.id not in [r.symptom.id for r in results]:
                results.append(
                    SymptomSearchResult(
                        symptom=symptom,
                        matched_term=matched_alias,
                        match_type="alias",
                        relevance_score=0.8,
                    )
                )

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    # ========================================================================
    # Symptom Aliases
    # ========================================================================

    async def create_alias(
        self, symptom_id: int, data: SymptomAliasCreate, created_by: str
    ) -> SymptomAlias:
        """Create an alias for a visible symptom."""
        await self.get_visible_or_404(symptom_id, detail="Symptom not found")

        alias = SymptomAlias(
            **data.model_dump(exclude={"symptom_id"}),
            symptom_id=symptom_id,
            tenant_id=self.tenant_id,
            created_by=created_by,
        )

        self.db.add(alias)
        await self.db.commit()
        await self.db.refresh(alias)

        return alias

    async def list_aliases(self, symptom_id: int) -> list[SymptomAlias]:
        """List aliases for a visible symptom."""
        await self.get_visible_or_404(symptom_id, detail="Symptom not found")

        result = await self.db.execute(
            select(SymptomAlias)
            .where(
                SymptomAlias.symptom_id == symptom_id,
                SymptomAlias.is_active == True,  # noqa: E712
            )
            .order_by(SymptomAlias.priority.desc())
        )

        return list(result.scalars().all())

    async def delete_alias(self, alias_id: int) -> None:
        """Delete an alias created by the caller's tenant."""
        result = await self.db.execute(
            select(SymptomAlias).where(
                SymptomAlias.id == alias_id,
                SymptomAlias.tenant_id == self.tenant_id,
            )
        )

        alias = result.scalar_one_or_none()

        if not alias:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Alias not found"
            )

        await self.db.delete(alias)
        await self.db.commit()
