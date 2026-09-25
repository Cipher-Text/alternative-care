"""Medicine service - business logic for the medicine catalog, aliases, and symptom mappings."""

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select

from app.core.base_service import GlobalCatalogService
from app.shared.models import Medicine, MedicineAlias, MedicineSymptomMapping, Symptom
from app.shared.schemas import (
    MedicineAliasCreate,
    MedicineCreate,
    MedicineSearchResult,
    MedicineSymptomMappingCreate,
    MedicineSymptomMappingUpdate,
    MedicineUpdate,
)


class MedicineService(GlobalCatalogService[Medicine]):
    """Medicine catalog service — global-or-tenant medicines, aliases, and symptom mappings."""

    model = Medicine

    # ========================================================================
    # Medicine CRUD
    # ========================================================================

    async def list_medicines(
        self,
        system: str | None = None,
        category: str | None = None,
        is_global: bool | None = None,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Medicine]:
        """List medicines visible to the caller (global + tenant-specific)."""
        query = self._visible_query()

        if system:
            query = query.where(Medicine.system == system)

        if category:
            query = query.where(Medicine.category == category)

        if is_global is not None:
            query = query.where(Medicine.is_global == is_global)

        if is_active is not None:
            query = query.where(Medicine.is_active == is_active)

        query = query.order_by(Medicine.name_en).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_medicine(
        self, data: MedicineCreate, created_by: str, role: str
    ) -> Medicine:
        """Create a medicine. Only admins can create global ones."""
        if data.is_global and role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create global medicines",
            )

        medicine = Medicine(
            **data.model_dump(),
            tenant_id=None if data.is_global else self.tenant_id,
            created_by=created_by,
        )

        self.db.add(medicine)
        await self.db.commit()
        await self.db.refresh(medicine)

        return medicine

    async def get_medicine(self, medicine_id: int) -> Medicine:
        """Get medicine details (global or own-tenant)."""
        return await self.get_visible_or_404(medicine_id, detail="Medicine not found")

    async def update_medicine(
        self, medicine_id: int, data: MedicineUpdate, updated_by: str
    ) -> Medicine:
        """Update a tenant-owned medicine (not global)."""
        medicine = await self.get_own_or_404(
            medicine_id, detail="Medicine not found or cannot be updated"
        )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(medicine, field, value)

        medicine.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(medicine)

        return medicine

    async def deactivate_medicine(self, medicine_id: int, updated_by: str) -> None:
        """Deactivate a tenant-owned medicine (not global)."""
        medicine = await self.get_own_or_404(
            medicine_id, detail="Medicine not found or cannot be deleted"
        )

        medicine.is_active = False
        medicine.updated_by = updated_by
        await self.db.commit()

    # ========================================================================
    # Medicine Search
    # ========================================================================

    async def search_medicines(
        self, q: str, system: str | None = None, limit: int = 20
    ) -> list[MedicineSearchResult]:
        """Search medicines by name or alias, with autocomplete-style ranking."""
        search_term = f"%{q.lower()}%"

        name_query = self._visible_query().where(
            Medicine.is_active == True,  # noqa: E712
            or_(
                func.lower(Medicine.name_en).like(search_term),
                func.lower(Medicine.name_bn).like(search_term),
            ),
        )

        if system:
            name_query = name_query.where(Medicine.system == system)

        name_results = await self.db.execute(name_query.limit(limit))
        medicines_from_name = name_results.scalars().all()

        alias_query = (
            select(Medicine, MedicineAlias.alias_en)
            .join(MedicineAlias, Medicine.id == MedicineAlias.medicine_id)
            .where(
                Medicine.is_active == True,  # noqa: E712
                MedicineAlias.is_active == True,  # noqa: E712
                or_(Medicine.is_global == True, Medicine.tenant_id == self.tenant_id),  # noqa: E712
                or_(
                    func.lower(MedicineAlias.alias_en).like(search_term),
                    func.lower(MedicineAlias.alias_bn).like(search_term),
                ),
            )
        )

        if system:
            alias_query = alias_query.where(Medicine.system == system)

        alias_results = await self.db.execute(alias_query.limit(limit))
        medicines_from_alias = [(medicine, alias) for medicine, alias in alias_results.all()]

        results: list[MedicineSearchResult] = []

        for medicine in medicines_from_name:
            results.append(
                MedicineSearchResult(
                    id=medicine.id,
                    name_en=medicine.name_en,
                    name_bn=medicine.name_bn,
                    system=medicine.system,
                    potency=medicine.potency,
                    category=medicine.category,
                    matched_alias=None,
                    rank=1.0,  # Exact name matches get highest rank
                )
            )

        for medicine, matched_alias in medicines_from_alias:
            if medicine.id not in [r.id for r in results]:
                results.append(
                    MedicineSearchResult(
                        id=medicine.id,
                        name_en=medicine.name_en,
                        name_bn=medicine.name_bn,
                        system=medicine.system,
                        potency=medicine.potency,
                        category=medicine.category,
                        matched_alias=matched_alias,
                        rank=0.8,  # Alias matches get lower rank
                    )
                )

        results.sort(key=lambda x: x.rank, reverse=True)
        return results[:limit]

    # ========================================================================
    # Medicine Aliases
    # ========================================================================

    async def create_alias(
        self, medicine_id: int, data: MedicineAliasCreate, created_by: str
    ) -> MedicineAlias:
        """Create an alias for a visible medicine."""
        await self.get_visible_or_404(medicine_id, detail="Medicine not found")

        alias = MedicineAlias(
            **data.model_dump(exclude={"medicine_id"}),
            medicine_id=medicine_id,
            tenant_id=self.tenant_id,
            created_by=created_by,
        )

        self.db.add(alias)
        await self.db.commit()
        await self.db.refresh(alias)

        return alias

    async def list_aliases(self, medicine_id: int) -> list[MedicineAlias]:
        """List aliases for a visible medicine."""
        await self.get_visible_or_404(medicine_id, detail="Medicine not found")

        result = await self.db.execute(
            select(MedicineAlias)
            .where(
                MedicineAlias.medicine_id == medicine_id,
                MedicineAlias.is_active == True,  # noqa: E712
            )
            .order_by(MedicineAlias.priority.desc())
        )

        return list(result.scalars().all())

    async def delete_alias(self, alias_id: int) -> None:
        """Delete an alias created by the caller's tenant."""
        result = await self.db.execute(
            select(MedicineAlias).where(
                MedicineAlias.id == alias_id,
                MedicineAlias.tenant_id == self.tenant_id,
            )
        )

        alias = result.scalar_one_or_none()

        if not alias:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Alias not found"
            )

        await self.db.delete(alias)
        await self.db.commit()

    # ========================================================================
    # Medicine-Symptom Mappings
    # ========================================================================

    async def create_mapping(
        self, data: MedicineSymptomMappingCreate, created_by: str
    ) -> MedicineSymptomMapping:
        """Link a medicine to a symptom."""
        medicine_result = await self.db.execute(
            select(Medicine).where(Medicine.id == data.medicine_id)
        )
        if not medicine_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found"
            )

        symptom_result = await self.db.execute(
            select(Symptom).where(Symptom.id == data.symptom_id)
        )
        if not symptom_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Symptom not found"
            )

        existing = await self.db.execute(
            select(MedicineSymptomMapping).where(
                and_(
                    MedicineSymptomMapping.medicine_id == data.medicine_id,
                    MedicineSymptomMapping.symptom_id == data.symptom_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mapping already exists between this medicine and symptom",
            )

        mapping = MedicineSymptomMapping(
            **data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=created_by,
        )

        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)

        return mapping

    async def get_mapping(self, mapping_id: int) -> MedicineSymptomMapping:
        """Get a medicine-symptom mapping by ID."""
        result = await self.db.execute(
            select(MedicineSymptomMapping).where(MedicineSymptomMapping.id == mapping_id)
        )

        mapping = result.scalar_one_or_none()

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found"
            )

        return mapping

    async def update_mapping(
        self, mapping_id: int, data: MedicineSymptomMappingUpdate, updated_by: str
    ) -> MedicineSymptomMapping:
        """Update a medicine-symptom mapping."""
        mapping = await self.get_mapping(mapping_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(mapping, field, value)

        mapping.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(mapping)

        return mapping

    async def delete_mapping(self, mapping_id: int) -> None:
        """Delete a medicine-symptom mapping."""
        mapping = await self.get_mapping(mapping_id)

        await self.db.delete(mapping)
        await self.db.commit()

    # ========================================================================
    # Cross-lookups
    # ========================================================================

    async def get_medicine_symptoms(self, medicine_id: int, limit: int = 100) -> list[Symptom]:
        """Get all symptoms linked to a medicine, ordered by mapping strength."""
        medicine_result = await self.db.execute(
            select(Medicine).where(Medicine.id == medicine_id)
        )
        if not medicine_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found"
            )

        result = await self.db.execute(
            select(Symptom)
            .join(MedicineSymptomMapping, Symptom.id == MedicineSymptomMapping.symptom_id)
            .where(
                MedicineSymptomMapping.medicine_id == medicine_id,
                MedicineSymptomMapping.is_active == True,  # noqa: E712
            )
            .order_by(MedicineSymptomMapping.strength.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_symptom_medicines(
        self, symptom_id: int, system: str | None = None, limit: int = 100
    ) -> list[Medicine]:
        """Get all medicines linked to a symptom, ordered by mapping strength."""
        symptom_result = await self.db.execute(
            select(Symptom).where(Symptom.id == symptom_id)
        )
        if not symptom_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Symptom not found"
            )

        query = (
            select(Medicine)
            .join(MedicineSymptomMapping, Medicine.id == MedicineSymptomMapping.medicine_id)
            .where(
                MedicineSymptomMapping.symptom_id == symptom_id,
                MedicineSymptomMapping.is_active == True,  # noqa: E712
            )
        )

        if system:
            query = query.where(Medicine.system == system)

        query = query.order_by(MedicineSymptomMapping.strength.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
