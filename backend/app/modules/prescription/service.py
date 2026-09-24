"""Prescription service layer with business logic."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.usage_tracking import UsageService
from app.shared.models import Prescription, PrescriptionItem
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
        limit: int = 100,
        offset: int = 0,
    ) -> list[Prescription]:
        """
        List prescriptions with filtering.

        Args:
            patient_id: Filter by patient ID
            visit_id: Filter by visit ID
            status: Filter by status (draft, issued, voided)
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

        # Order by created date (newest first)
        query = query.order_by(Prescription.created_at.desc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

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

    async def generate_pdf(self, prescription_id: str) -> str:
        """
        Generate PDF for a prescription.

        Args:
            prescription_id: Prescription ID

        Returns:
            PDF URL

        Raises:
            HTTPException: If prescription not found

        TODO: Implement actual PDF generation using ReportLab or WeasyPrint
        """
        prescription = await self.get_prescription(prescription_id)

        if prescription.status == "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot generate PDF for draft prescription. Please issue it first.",
            )

        # TODO: Implement PDF generation
        # 1. Fetch patient details
        # 2. Fetch doctor details
        # 3. Generate PDF using template
        # 4. Upload to MinIO/S3
        # 5. Update prescription with pdf_url and pdf_generated_at

        # Placeholder implementation
        pdf_url = f"https://storage.example.com/prescriptions/{prescription_id}.pdf"
        prescription.pdf_url = pdf_url
        prescription.pdf_generated_at = datetime.utcnow().isoformat()

        await self.db.commit()
        await self.db.refresh(prescription)

        return pdf_url

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
