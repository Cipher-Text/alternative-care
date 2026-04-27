"""Patient service layer with business logic."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Patient, PatientTag, PatientDiagnosis
from app.shared.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientTagCreate,
    PatientTagUpdate,
    PatientDiagnosisCreate,
    PatientDiagnosisUpdate,
)


class PatientService:
    """Service for managing patients, tags, and diagnoses."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    # ===== Patient Methods =====

    async def create_patient(
        self, data: PatientCreate, created_by: str
    ) -> Patient:
        """
        Create a new patient.

        Args:
            data: Patient creation data
            created_by: User ID creating the patient

        Returns:
            Created patient
        """
        patient = Patient(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_group=data.blood_group,
            phone=data.phone,
            email=data.email,
            whatsapp=data.whatsapp,
            address=data.address,
            division_id=data.division_id,
            district_id=data.district_id,
            upazila_id=data.upazila_id,
            chief_complaint=data.chief_complaint,
            medical_history=data.medical_history,
            photo_url=data.photo_url,
            next_visit_date=data.next_visit_date,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)

        return patient

    async def get_patient(self, patient_id: str) -> Patient:
        """Get patient by ID with tenant filtering."""
        result = await self.db.execute(
            select(Patient).where(
                and_(
                    Patient.id == patient_id,
                    Patient.tenant_id == self.tenant_id,
                )
            )
        )
        patient = result.scalar_one_or_none()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        return patient

    async def list_patients(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        has_upcoming_visit: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Patient]:
        """
        List patients with filters.

        Args:
            search: Search by name, phone, or email
            is_active: Filter by active status
            has_upcoming_visit: Filter patients with upcoming visits
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of patients
        """
        query = select(Patient).where(Patient.tenant_id == self.tenant_id)

        # Search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Patient.full_name.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                )
            )

        # Active filter
        if is_active is not None:
            query = query.where(Patient.is_active == is_active)

        # Upcoming visit filter
        if has_upcoming_visit is not None:
            if has_upcoming_visit:
                query = query.where(
                    and_(
                        Patient.next_visit_date.isnot(None),
                        Patient.next_visit_date >= func.current_date(),
                    )
                )
            else:
                query = query.where(
                    or_(
                        Patient.next_visit_date.is_(None),
                        Patient.next_visit_date < func.current_date(),
                    )
                )

        query = (
            query.order_by(Patient.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_patient(
        self, patient_id: str, data: PatientUpdate, updated_by: str
    ) -> Patient:
        """Update patient information."""
        patient = await self.get_patient(patient_id)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)

        patient.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(patient)

        return patient

    async def delete_patient(self, patient_id: str, updated_by: str) -> Patient:
        """Soft delete a patient (set is_active=False)."""
        patient = await self.get_patient(patient_id)

        patient.is_active = False
        patient.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(patient)

        return patient

    async def get_patient_count(self) -> int:
        """Get total count of active patients for tenant."""
        result = await self.db.execute(
            select(func.count(Patient.id)).where(
                and_(
                    Patient.tenant_id == self.tenant_id,
                    Patient.is_active == True,  # noqa: E712
                )
            )
        )
        return result.scalar_one()

    # ===== Patient Tag Methods =====

    async def create_patient_tag(
        self, data: PatientTagCreate, created_by: str
    ) -> PatientTag:
        """Create a new patient tag."""
        # Verify patient exists and belongs to tenant
        await self.get_patient(data.patient_id)

        tag = PatientTag(
            patient_id=data.patient_id,
            tenant_id=self.tenant_id,
            tag_type=data.tag_type,
            tag_value=data.tag_value,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)

        return tag

    async def list_patient_tags(self, patient_id: str) -> List[PatientTag]:
        """List all tags for a patient."""
        # Verify patient exists
        await self.get_patient(patient_id)

        result = await self.db.execute(
            select(PatientTag).where(
                and_(
                    PatientTag.patient_id == patient_id,
                    PatientTag.tenant_id == self.tenant_id,
                )
            ).order_by(PatientTag.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_patient_tag(self, tag_id: int) -> PatientTag:
        """Get patient tag by ID."""
        result = await self.db.execute(
            select(PatientTag).where(
                and_(
                    PatientTag.id == tag_id,
                    PatientTag.tenant_id == self.tenant_id,
                )
            )
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient tag not found",
            )

        return tag

    async def update_patient_tag(
        self, tag_id: int, data: PatientTagUpdate, updated_by: str
    ) -> PatientTag:
        """Update patient tag."""
        tag = await self.get_patient_tag(tag_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tag, field, value)

        tag.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(tag)

        return tag

    async def delete_patient_tag(self, tag_id: int) -> None:
        """Delete patient tag."""
        tag = await self.get_patient_tag(tag_id)
        await self.db.delete(tag)
        await self.db.commit()

    # ===== Patient Diagnosis Methods =====

    async def create_patient_diagnosis(
        self, data: PatientDiagnosisCreate, created_by: str
    ) -> PatientDiagnosis:
        """Create a new patient diagnosis."""
        # Verify patient exists
        await self.get_patient(data.patient_id)

        diagnosis = PatientDiagnosis(
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            tenant_id=self.tenant_id,
            description=data.description,
            icd_code=data.icd_code,
            diagnosed_at=data.diagnosed_at,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(diagnosis)
        await self.db.commit()
        await self.db.refresh(diagnosis)

        return diagnosis

    async def list_patient_diagnoses(
        self, patient_id: str, active_only: bool = True
    ) -> List[PatientDiagnosis]:
        """List all diagnoses for a patient."""
        # Verify patient exists
        await self.get_patient(patient_id)

        query = select(PatientDiagnosis).where(
            and_(
                PatientDiagnosis.patient_id == patient_id,
                PatientDiagnosis.tenant_id == self.tenant_id,
            )
        )

        if active_only:
            query = query.where(PatientDiagnosis.is_active == True)  # noqa: E712

        query = query.order_by(PatientDiagnosis.diagnosed_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_patient_diagnosis(self, diagnosis_id: int) -> PatientDiagnosis:
        """Get patient diagnosis by ID."""
        result = await self.db.execute(
            select(PatientDiagnosis).where(
                and_(
                    PatientDiagnosis.id == diagnosis_id,
                    PatientDiagnosis.tenant_id == self.tenant_id,
                )
            )
        )
        diagnosis = result.scalar_one_or_none()

        if not diagnosis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient diagnosis not found",
            )

        return diagnosis

    async def update_patient_diagnosis(
        self, diagnosis_id: int, data: PatientDiagnosisUpdate, updated_by: str
    ) -> PatientDiagnosis:
        """Update patient diagnosis."""
        diagnosis = await self.get_patient_diagnosis(diagnosis_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(diagnosis, field, value)

        diagnosis.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(diagnosis)

        return diagnosis

    async def delete_patient_diagnosis(self, diagnosis_id: int, updated_by: str) -> PatientDiagnosis:
        """Soft delete a diagnosis (set is_active=False)."""
        diagnosis = await self.get_patient_diagnosis(diagnosis_id)

        diagnosis.is_active = False
        diagnosis.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(diagnosis)

        return diagnosis
