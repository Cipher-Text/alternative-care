"""Prescription service layer with business logic."""

from datetime import datetime
from types import SimpleNamespace
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pdf import render_pdf
from app.core.usage_tracking import UsageService
from app.modules.prescription.pdf import build_prescription_html
from app.shared.models import (
    DoctorDegree,
    Medicine,
    Patient,
    Prescription,
    PrescriptionItem,
    Tenant,
    User,
    Visit,
)
from app.shared.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionItemCreate,
)


class PrescriptionService:
    """Service for managing prescriptions and prescription items."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    # ===== Prescription Methods =====

    async def create_prescription(
        self, data: PrescriptionCreate, prescribed_by: str
    ) -> Prescription:
        """
        Create a new prescription with items.

        Args:
            data: Prescription creation data with items
            prescribed_by: User ID of the prescribing doctor

        Returns:
            Created prescription with items
        """
        await self._check_links(data.patient_id, data.visit_id)

        # Create prescription
        prescription = Prescription(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            prescribed_by=prescribed_by,
            diagnosis=data.diagnosis,
            doctors_notes=data.doctors_notes,
            advice=data.advice,
            status=data.status,
            created_by=prescribed_by,
            updated_by=prescribed_by,
        )

        self.db.add(prescription)

        # Create prescription items
        for idx, item_data in enumerate(data.items):
            item = PrescriptionItem(
                prescription_id=prescription.id,
                tenant_id=self.tenant_id,
                medicine_id=item_data.medicine_id,
                medicine_name=item_data.medicine_name,
                dosage=item_data.dosage,
                frequency=item_data.frequency,
                duration=item_data.duration,
                quantity=item_data.quantity,
                instructions=item_data.instructions,
                display_order=item_data.display_order if item_data.display_order else idx,
                created_by=prescribed_by,
                updated_by=prescribed_by,
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(prescription)

        # Load items relationship
        await self.db.refresh(prescription, ["items"])

        if prescription.status == "issued":
            await UsageService(self.db, self.tenant_id).increment("prescriptions_created")

        return prescription

    async def _check_links(self, patient_id: str, visit_id: Optional[str]) -> None:
        """The patient must be this clinic's, and a visit (if given) must be that patient's: a prescription cannot point at
        another clinic's records, and cannot be tied to somebody else's visit."""
        patient = (
            await self.db.execute(select(Patient.id).where(Patient.id == patient_id, Patient.tenant_id == self.tenant_id))
        ).scalar_one_or_none()
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        if visit_id:
            visit = (
                await self.db.execute(
                    select(Visit.id).where(Visit.id == visit_id, Visit.tenant_id == self.tenant_id, Visit.patient_id == patient_id)
                )
            ).scalar_one_or_none()
            if visit is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="That visit does not belong to this patient")

    async def with_context(self, prescriptions: list[Prescription]) -> list[Prescription]:
        """Attach the patient's and prescriber's names and the linked visit's date and complaint, so screens never show raw ids."""
        if not prescriptions:
            return prescriptions
        patient_ids = {p.patient_id for p in prescriptions}
        names = dict(
            (await self.db.execute(select(Patient.id, Patient.full_name).where(Patient.id.in_(patient_ids), Patient.tenant_id == self.tenant_id))).all()
        )
        visit_ids = {p.visit_id for p in prescriptions if p.visit_id}
        visits = {}
        if visit_ids:
            rows = await self.db.execute(
                select(Visit.id, Visit.visit_date, Visit.chief_complaint).where(Visit.id.in_(visit_ids), Visit.tenant_id == self.tenant_id)
            )
            visits = {vid: (vdate, complaint) for vid, vdate, complaint in rows.all()}
        doctor_names = dict(
            (await self.db.execute(select(User.id, User.full_name).where(User.id.in_({p.prescribed_by for p in prescriptions}), User.tenant_id == self.tenant_id))).all()
        )
        for p in prescriptions:
            p.patient_name = names.get(p.patient_id)
            p.prescribed_by_name = doctor_names.get(p.prescribed_by)
            p.visit_date, p.visit_complaint = visits.get(p.visit_id, (None, None))
        return prescriptions

    async def get_prescription(self, prescription_id: str) -> Prescription:
        """
        Get prescription by ID with tenant filtering and items loaded.

        Args:
            prescription_id: Prescription ID

        Returns:
            Prescription with items

        Raises:
            HTTPException: If prescription not found
        """
        result = await self.db.execute(
            select(Prescription)
            .options(selectinload(Prescription.items))
            .where(
                and_(
                    Prescription.id == prescription_id,
                    Prescription.tenant_id == self.tenant_id,
                )
            )
        )
        prescription = result.scalar_one_or_none()

        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )

        return prescription

    async def list_prescriptions(
        self,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Prescription]:
        """
        List prescriptions with filtering.

        Args:
            patient_id: Filter by patient ID
            visit_id: Filter by visit ID
            status: Filter by status (draft, issued, voided)
            search: Case-insensitive match on prescription ID, patient ID or diagnosis
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of prescriptions (without items loaded for performance)
        """
        query = select(Prescription).where(
            Prescription.tenant_id == self.tenant_id
        )

        # Apply filters
        if patient_id:
            query = query.where(Prescription.patient_id == patient_id)
        if visit_id:
            query = query.where(Prescription.visit_id == visit_id)
        if status:
            query = query.where(Prescription.status == status)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            # A doctor looks for a person, not an id: match the patient's name or phone too
            people = select(Patient.id).where(
                Patient.tenant_id == self.tenant_id,
                or_(Patient.full_name.ilike(pattern), Patient.phone.ilike(pattern)),
            )
            query = query.where(
                or_(
                    Prescription.id.ilike(pattern),
                    Prescription.patient_id.ilike(pattern),
                    Prescription.diagnosis.ilike(pattern),
                    Prescription.patient_id.in_(people),
                )
            )

        # Order by created date (newest first)
        query = query.order_by(Prescription.created_at.desc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return await self.with_context(list(result.scalars().all()))

    async def update_prescription(
        self, prescription_id: str, data: PrescriptionUpdate, updated_by: str
    ) -> Prescription:
        """
        Update a prescription (only drafts can be updated).

        Args:
            prescription_id: Prescription ID
            data: Update data
            updated_by: User ID making the update

        Returns:
            Updated prescription

        Raises:
            HTTPException: If prescription not found or not editable
        """
        prescription = await self.get_prescription(prescription_id)

        # Check if prescription is editable
        if prescription.status not in ["draft"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update prescription with status '{prescription.status}'. Only draft prescriptions can be updated.",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        new_items = update_data.pop("items", None)
        if new_items is not None:
            # Replace the draft's medicines with exactly the list sent (what the builder shows)
            await self.db.execute(delete(PrescriptionItem).where(PrescriptionItem.prescription_id == prescription_id))
            for idx, item_data in enumerate(new_items):
                self.db.add(
                    PrescriptionItem(
                        prescription_id=prescription_id,
                        tenant_id=self.tenant_id,
                        medicine_id=item_data.get("medicine_id"),
                        medicine_name=item_data.get("medicine_name"),
                        dosage=item_data["dosage"],
                        frequency=item_data["frequency"],
                        duration=item_data.get("duration"),
                        quantity=item_data.get("quantity"),
                        instructions=item_data.get("instructions"),
                        display_order=idx,
                        created_by=updated_by,
                        updated_by=updated_by,
                    )
                )
        for field, value in update_data.items():
            setattr(prescription, field, value)

        prescription.updated_by = updated_by
        prescription.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(prescription)
        await self.db.refresh(prescription, ["items"])

        if prescription.status == "issued":
            await UsageService(self.db, self.tenant_id).increment("prescriptions_created")

        return prescription

    async def void_prescription(
        self, prescription_id: str, updated_by: str
    ) -> Prescription:
        """
        Void a prescription (mark as voided, cannot be undone).

        Args:
            prescription_id: Prescription ID
            updated_by: User ID voiding the prescription

        Returns:
            Voided prescription

        Raises:
            HTTPException: If prescription not found or already voided
        """
        prescription = await self.get_prescription(prescription_id)

        if prescription.status == "voided":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prescription is already voided",
            )

        prescription.status = "voided"
        prescription.updated_by = updated_by
        prescription.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(prescription)
        await self.db.refresh(prescription, ["items"])

        return prescription

    async def build_pdf(self, prescription_id: str) -> tuple[bytes, str]:
        """
        Render a prescription as a PDF document.

        Returns (pdf bytes, suggested filename). Generated on demand and not stored: issued
        prescriptions are immutable, and an on-demand render is always current (a voided one gets
        a VOID stamp), has no stale links, and needs no object storage.

        Raises:
            HTTPException: 404 if not found, 400 for drafts, 503 if PDF rendering is unavailable
        """
        prescription = await self.get_prescription(prescription_id)

        if prescription.status == "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot generate PDF for draft prescription. Please issue it first.",
            )

        patient = (
            await self.db.execute(
                select(Patient).where(
                    Patient.id == prescription.patient_id, Patient.tenant_id == self.tenant_id
                )
            )
        ).scalar_one()
        tenant = (
            await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))
        ).scalar_one()
        doctor = (
            await self.db.execute(select(User).where(User.id == prescription.prescribed_by))
        ).scalar_one_or_none()
        degrees = []
        if doctor is not None:
            degrees = (
                await self.db.execute(
                    select(DoctorDegree)
                    .where(DoctorDegree.user_id == doctor.id)
                    .order_by(DoctorDegree.completion_year.desc())
                    .limit(4)
                )
            ).scalars().all()
        else:
            # The prescriber's account may have been removed; fall back to the clinic's name.
            doctor = SimpleNamespace(full_name=tenant.name)

        medicine_ids = {i.medicine_id for i in prescription.items if i.medicine_id is not None}
        medicines_by_id = {}
        if medicine_ids:
            rows = await self.db.execute(select(Medicine).where(Medicine.id.in_(medicine_ids)))
            medicines_by_id = {m.id: m for m in rows.scalars().all()}

        html = build_prescription_html(
            prescription=prescription,
            patient=patient,
            doctor=doctor,
            tenant=tenant,
            degrees=degrees,
            medicines_by_id=medicines_by_id,
        )
        pdf = await render_pdf(html)

        await UsageService(self.db, self.tenant_id).increment("pdfs_generated")
        return pdf, f"prescription-{prescription.id[:8]}.pdf"

    # ===== Prescription Item Methods =====

    async def add_prescription_item(
        self, prescription_id: str, data: PrescriptionItemCreate, created_by: str
    ) -> PrescriptionItem:
        """
        Add an item to a prescription (only for draft prescriptions).

        Args:
            prescription_id: Prescription ID
            data: Item creation data
            created_by: User ID adding the item

        Returns:
            Created prescription item

        Raises:
            HTTPException: If prescription not found or not editable
        """
        prescription = await self.get_prescription(prescription_id)

        if prescription.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add items to non-draft prescription",
            )

        item = PrescriptionItem(
            prescription_id=prescription_id,
            tenant_id=self.tenant_id,
            medicine_id=data.medicine_id,
            medicine_name=data.medicine_name,
            dosage=data.dosage,
            frequency=data.frequency,
            duration=data.duration,
            quantity=data.quantity,
            instructions=data.instructions,
            display_order=data.display_order,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        return item

    async def delete_prescription_item(
        self, prescription_id: str, item_id: int, deleted_by: str
    ) -> None:
        """
        Delete an item from a prescription (only for draft prescriptions).

        Args:
            prescription_id: Prescription ID
            item_id: Item ID to delete
            deleted_by: User ID deleting the item

        Raises:
            HTTPException: If prescription not editable or item not found
        """
        prescription = await self.get_prescription(prescription_id)

        if prescription.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete items from non-draft prescription",
            )

        result = await self.db.execute(
            select(PrescriptionItem).where(
                and_(
                    PrescriptionItem.id == item_id,
                    PrescriptionItem.prescription_id == prescription_id,
                    PrescriptionItem.tenant_id == self.tenant_id,
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription item not found",
            )

        await self.db.delete(item)
        await self.db.commit()
