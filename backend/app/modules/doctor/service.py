"""Doctor service layer with business logic."""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import User, Tenant, DoctorDegree, DoctorTraining
from app.shared.schemas import (
    DoctorProfileUpdate,
    DoctorDegreeCreate,
    DoctorDegreeUpdate,
    DoctorTrainingCreate,
    DoctorTrainingUpdate,
)


class DoctorService:
    """Service for managing doctor profiles, degrees, and trainings."""

    def __init__(self, db: AsyncSession, user_id: str, tenant_id: str):
        """Initialize service with database session, user ID, and tenant context."""
        self.db = db
        self.user_id = user_id
        self.tenant_id = tenant_id

    # ===== Doctor Profile Methods =====

    async def get_profile(self) -> dict:
        """
        Get doctor profile (combines User + Tenant data).

        Returns:
            Dictionary with combined user and tenant fields
        """
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == self.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Get tenant
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Combine data
        return {
            # User fields
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "language": user.language,
            "is_active": user.is_active,
            # Tenant fields
            "tenant_id": tenant.id,
            "clinic_name": tenant.clinic_name,
            "clinic_address": tenant.clinic_address,
            "division_id": tenant.division_id,
            "district_id": tenant.district_id,
            "upazila_id": tenant.upazila_id,
            "specializations": tenant.specializations,
            "license_number": tenant.license_number,
            "is_verified": tenant.is_verified,
            "verified_at": tenant.verified_at,
            "plan": tenant.plan,
            "plan_started_at": tenant.plan_started_at,
            "plan_expires_at": tenant.plan_expires_at,
        }

    async def update_profile(
        self, data: DoctorProfileUpdate, updated_by: str
    ) -> dict:
        """
        Update doctor profile (updates User and/or Tenant).

        Args:
            data: Profile update data
            updated_by: User ID updating the profile

        Returns:
            Updated profile dictionary
        """
        # Get user and tenant
        user_result = await self.db.execute(
            select(User).where(User.id == self.user_id)
        )
        user = user_result.scalar_one_or_none()

        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()

        if not user or not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        # Update user fields
        user_fields = ["full_name", "phone", "avatar_url", "language"]
        for field in user_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(user, field, value)

        user.updated_by = updated_by

        # Update tenant fields
        tenant_fields = [
            "clinic_name",
            "clinic_address",
            "division_id",
            "district_id",
            "upazila_id",
            "license_number",
        ]
        for field in tenant_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(tenant, field, value)

        tenant.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(tenant)

        # Return combined profile
        return await self.get_profile()

    # ===== Doctor Degree Methods =====

    async def create_degree(
        self, data: DoctorDegreeCreate, created_by: str
    ) -> DoctorDegree:
        """Create a new doctor degree."""
        degree = DoctorDegree(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            degree_type=data.degree_type,
            degree_name=data.degree_name,
            specialization=data.specialization,
            institution_name=data.institution_name,
            institution_location=data.institution_location,
            start_year=data.start_year,
            completion_year=data.completion_year,
            certificate_url=data.certificate_url,
            display_order=data.display_order,
            is_verified=False,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(degree)
        await self.db.commit()
        await self.db.refresh(degree)

        return degree

    async def list_degrees(self) -> List[DoctorDegree]:
        """List all degrees for the doctor."""
        result = await self.db.execute(
            select(DoctorDegree)
            .where(
                and_(
                    DoctorDegree.user_id == self.user_id,
                    DoctorDegree.tenant_id == self.tenant_id,
                )
            )
            .order_by(DoctorDegree.display_order, DoctorDegree.completion_year.desc())
        )

        return list(result.scalars().all())

    async def get_degree(self, degree_id: int) -> DoctorDegree:
        """Get degree by ID."""
        result = await self.db.execute(
            select(DoctorDegree).where(
                and_(
                    DoctorDegree.id == degree_id,
                    DoctorDegree.user_id == self.user_id,
                    DoctorDegree.tenant_id == self.tenant_id,
                )
            )
        )
        degree = result.scalar_one_or_none()

        if not degree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Degree not found",
            )

        return degree

    async def update_degree(
        self, degree_id: int, data: DoctorDegreeUpdate, updated_by: str
    ) -> DoctorDegree:
        """Update doctor degree."""
        degree = await self.get_degree(degree_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(degree, field, value)

        degree.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(degree)

        return degree

    async def delete_degree(self, degree_id: int) -> None:
        """Delete doctor degree."""
        degree = await self.get_degree(degree_id)
        await self.db.delete(degree)
        await self.db.commit()

    # ===== Doctor Training Methods =====

    async def create_training(
        self, data: DoctorTrainingCreate, created_by: str
    ) -> DoctorTraining:
        """Create a new doctor training."""
        training = DoctorTraining(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            training_type=data.training_type,
            title=data.title,
            provider=data.provider,
            description=data.description,
            skills=data.skills,
            start_date=data.start_date,
            completion_date=data.completion_date,
            expiry_date=data.expiry_date,
            certificate_url=data.certificate_url,
            credential_id=data.credential_id,
            display_order=data.display_order,
            is_verified=False,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(training)
        await self.db.commit()
        await self.db.refresh(training)

        return training

    async def list_trainings(self, active_only: bool = False) -> List[DoctorTraining]:
        """List all trainings for the doctor."""
        from datetime import date

        query = select(DoctorTraining).where(
            and_(
                DoctorTraining.user_id == self.user_id,
                DoctorTraining.tenant_id == self.tenant_id,
            )
        )

        # Filter expired certifications
        if active_only:
            today = date.today()
            query = query.where(
                (DoctorTraining.expiry_date.is_(None))
                | (DoctorTraining.expiry_date >= today)
            )

        query = query.order_by(
            DoctorTraining.display_order, DoctorTraining.completion_date.desc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_training(self, training_id: int) -> DoctorTraining:
        """Get training by ID."""
        result = await self.db.execute(
            select(DoctorTraining).where(
                and_(
                    DoctorTraining.id == training_id,
                    DoctorTraining.user_id == self.user_id,
                    DoctorTraining.tenant_id == self.tenant_id,
                )
            )
        )
        training = result.scalar_one_or_none()

        if not training:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training not found",
            )

        return training

    async def update_training(
        self, training_id: int, data: DoctorTrainingUpdate, updated_by: str
    ) -> DoctorTraining:
        """Update doctor training."""
        training = await self.get_training(training_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(training, field, value)

        training.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(training)

        return training

    async def delete_training(self, training_id: int) -> None:
        """Delete doctor training."""
        training = await self.get_training(training_id)
        await self.db.delete(training)
        await self.db.commit()
