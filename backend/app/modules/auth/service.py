"""Authentication service - business logic for auth operations."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    get_password_hash,
    get_totp_uri,
    verify_password,
    verify_totp,
)
from app.modules.auth.schemas import (
    AdminCreateTenantDoctorRequest,
    AdminClientDetailResponse,
    AdminClientDoctorResponse,
    AdminClientListItem,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    Setup2FAResponse,
    TokenResponse,
    UserProfileResponse,
    UserResponse,
    TenantResponse,
)
from app.shared.models.tenant import Tenant, User, UserSession


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Registration
    # ========================================================================

    async def register_doctor(self, data: RegisterRequest) -> RegisterResponse:
        """
        Register a new doctor with tenant creation.

        Args:
            data: Registration data

        Returns:
            Registration response

        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create tenant
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=data.full_name,
            email=data.email,
            phone=data.phone,
            clinic_name=data.clinic_name,
            clinic_address=data.clinic_address,
            division_id=data.division_id,
            district_id=data.district_id,
            upazila_id=data.upazila_id,
            specializations=data.specializations,
            license_number=data.license_number,
            is_verified=False,
            is_approved=False,  # Requires admin approval
            is_active=True,
            plan="free",
        )
        self.db.add(tenant)

        # Create user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            role="doctor",
            full_name=data.full_name,
            phone=data.phone,
            language=data.language,
            is_active=True,
            is_email_verified=False,
        )
        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)

        # TODO: Send verification email
        # TODO: Notify admins of new registration

        return RegisterResponse(
            message="Registration successful. Your account is pending admin approval.",
            user_id=user.id,
            tenant_id=tenant.id,
            email=user.email,
            requires_approval=True,
        )

    async def admin_create_tenant_doctor(
        self,
        data: AdminCreateTenantDoctorRequest,
        admin_user_id: str,
    ) -> RegisterResponse:
        """
        Admin-only provisioning flow for a new client account.

        Creates tenant (clinic) and primary doctor in one operation.
        """
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=data.tenant_name or data.full_name,
            email=data.email,
            phone=data.phone,
            clinic_name=data.clinic_name,
            clinic_address=data.clinic_address,
            division_id=data.division_id,
            district_id=data.district_id,
            upazila_id=data.upazila_id,
            specializations=data.specializations,
            license_number=data.license_number,
            is_verified=False,
            is_approved=data.auto_approve,
            approved_at=datetime.now(timezone.utc) if data.auto_approve else None,
            approved_by=admin_user_id if data.auto_approve else None,
            is_active=True,
            plan=data.plan,
        )
        self.db.add(tenant)

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            role="doctor",
            full_name=data.full_name,
            phone=data.phone,
            language=data.language,
            is_active=True,
            is_email_verified=False,
        )
        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)

        requires_approval = not tenant.is_approved
        return RegisterResponse(
            message=(
                "Client account created successfully."
                if tenant.is_approved
                else "Client account created. Tenant is pending approval."
            ),
            user_id=user.id,
            tenant_id=tenant.id,
            email=user.email,
            requires_approval=requires_approval,
        )

    # ========================================================================
    # Login
    # ========================================================================

    async def login(
        self,
        data: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        """
        Authenticate user and create session.

        Args:
            data: Login credentials
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Login response with tokens

        Raises:
            HTTPException: If credentials invalid or account not approved
        """
        # Get user by email
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        # Check if tenant is approved (for doctors)
        if user.tenant_id:
            result = await self.db.execute(
                select(Tenant).where(Tenant.id == user.tenant_id)
            )
            tenant = result.scalar_one_or_none()
            if not tenant or not tenant.is_approved:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account is pending admin approval",
                )

        # Check 2FA
        if user.is_2fa_enabled:
            if not data.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA code required",
                )
            if not user.totp_secret or not verify_totp(user.totp_secret, data.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code",
                )

        # Get tenant plan for JWT
        plan = None
        if user.tenant_id:
            result = await self.db.execute(
                select(Tenant.plan).where(Tenant.id == user.tenant_id)
            )
            plan = result.scalar_one_or_none()

        # Create tokens
        token_data = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "email": user.email,
            "plan": plan,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": user.id})

        # Create session
        session_id = str(uuid.uuid4())
        session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=get_password_hash(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
        self.db.add(session)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return LoginResponse(
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            user=UserResponse.model_validate(user),
            requires_2fa=False,
        )

    # ========================================================================
    # Token Refresh
    # ========================================================================

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token pair

        Raises:
            HTTPException: If refresh token is invalid or revoked
        """
        try:
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Verify session exists and not revoked
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.is_revoked == False,  # noqa: E712
            )
        )
        sessions = result.scalars().all()

        # Find matching session
        valid_session = None
        for session in sessions:
            if verify_password(refresh_token, session.refresh_token_hash):
                valid_session = session
                break

        if not valid_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        # Check expiration
        if valid_session.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # Get tenant plan
        plan = None
        if user.tenant_id:
            result = await self.db.execute(
                select(Tenant.plan).where(Tenant.id == user.tenant_id)
            )
            plan = result.scalar_one_or_none()

        # Create new tokens
        token_data = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "email": user.email,
            "plan": plan,
        }
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": user.id})

        # Update session with new refresh token (token rotation)
        valid_session.refresh_token_hash = get_password_hash(new_refresh_token)
        valid_session.last_activity_at = datetime.now(timezone.utc)

        await self.db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ========================================================================
    # Logout
    # ========================================================================

    async def logout(self, user_id: str, refresh_token: str | None = None) -> None:
        """
        Logout user by revoking session.

        Args:
            user_id: User ID
            refresh_token: Optional specific refresh token to revoke
        """
        if refresh_token:
            # Revoke specific session
            result = await self.db.execute(
                select(UserSession).where(
                    UserSession.user_id == user_id,
                    UserSession.is_revoked == False,  # noqa: E712
                )
            )
            sessions = result.scalars().all()

            for session in sessions:
                if verify_password(refresh_token, session.refresh_token_hash):
                    session.is_revoked = True
                    session.revoked_at = datetime.now(timezone.utc)
                    break
        else:
            # Revoke all sessions for user
            result = await self.db.execute(
                select(UserSession).where(
                    UserSession.user_id == user_id,
                    UserSession.is_revoked == False,  # noqa: E712
                )
            )
            sessions = result.scalars().all()

            for session in sessions:
                session.is_revoked = True
                session.revoked_at = datetime.now(timezone.utc)

        await self.db.commit()

    # ========================================================================
    # 2FA
    # ========================================================================

    async def setup_2fa(self, user_id: str) -> Setup2FAResponse:
        """
        Setup 2FA for user.

        Args:
            user_id: User ID

        Returns:
            TOTP secret and QR code URI

        Raises:
            HTTPException: If user not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Generate new TOTP secret
        secret = generate_totp_secret()
        qr_uri = get_totp_uri(secret, user.email)

        # Save secret (not enabled yet)
        user.totp_secret = secret

        await self.db.commit()

        return Setup2FAResponse(
            secret=secret,
            qr_code_uri=qr_uri,
        )

    async def verify_and_enable_2fa(self, user_id: str, totp_code: str) -> bool:
        """
        Verify TOTP code and enable 2FA.

        Args:
            user_id: User ID
            totp_code: 6-digit TOTP code

        Returns:
            True if successful

        Raises:
            HTTPException: If code invalid
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not set up",
            )

        if not verify_totp(user.totp_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code",
            )

        # Enable 2FA
        user.is_2fa_enabled = True

        await self.db.commit()

        return True

    async def disable_2fa(self, user_id: str, password: str, totp_code: str) -> bool:
        """
        Disable 2FA after password and TOTP verification.

        Args:
            user_id: User ID
            password: User password
            totp_code: 6-digit TOTP code

        Returns:
            True if successful

        Raises:
            HTTPException: If verification fails
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )

        # Verify TOTP
        if not user.totp_secret or not verify_totp(user.totp_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
            )

        # Disable 2FA
        user.is_2fa_enabled = False
        user.totp_secret = None

        await self.db.commit()

        return True

    # ========================================================================
    # Password Management
    # ========================================================================

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            HTTPException: If current password is incorrect
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        # Update password
        user.password_hash = get_password_hash(new_password)

        # Revoke all active sessions after password change.
        # This invalidates all existing refresh tokens across devices.
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.is_revoked == False,  # noqa: E712
            )
        )
        sessions = result.scalars().all()
        for session in sessions:
            session.is_revoked = True
            session.revoked_at = datetime.now(timezone.utc)

        await self.db.commit()

        return True

    # ========================================================================
    # User Profile
    # ========================================================================

    async def get_user_profile(self, user_id: str) -> UserProfileResponse:
        """
        Get user profile with tenant info.

        Args:
            user_id: User ID

        Returns:
            User profile

        Raises:
            HTTPException: If user not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        tenant = None
        if user.tenant_id:
            result = await self.db.execute(
                select(Tenant).where(Tenant.id == user.tenant_id)
            )
            tenant_obj = result.scalar_one_or_none()
            if tenant_obj:
                tenant = TenantResponse.model_validate(tenant_obj)

        return UserProfileResponse(
            user=UserResponse.model_validate(user),
            tenant=tenant,
        )

    async def list_pending_tenants(self) -> list[TenantResponse]:
        """List tenants waiting for approval."""
        result = await self.db.execute(
            select(Tenant)
            .where(Tenant.is_approved == False)  # noqa: E712
            .order_by(Tenant.created_at.desc())
        )
        tenants = result.scalars().all()
        return [TenantResponse.model_validate(tenant) for tenant in tenants]

    async def list_admin_clients(self) -> list[AdminClientListItem]:
        """List all tenant clients with primary doctor summaries."""
        tenant_result = await self.db.execute(
            select(Tenant).order_by(Tenant.created_at.desc())
        )
        tenants = tenant_result.scalars().all()

        if not tenants:
            return []

        tenant_ids = [tenant.id for tenant in tenants]
        user_result = await self.db.execute(
            select(User)
            .where(User.tenant_id.in_(tenant_ids), User.role == "doctor")
            .order_by(User.created_at.asc())
        )
        doctors = user_result.scalars().all()

        doctors_by_tenant: dict[str, list[User]] = {}
        for doctor in doctors:
            if doctor.tenant_id:
                doctors_by_tenant.setdefault(doctor.tenant_id, []).append(doctor)

        return [
            AdminClientListItem(
                tenant=TenantResponse.model_validate(tenant),
                primary_doctor=(
                    AdminClientDoctorResponse.model_validate(doctors_by_tenant[tenant.id][0])
                    if doctors_by_tenant.get(tenant.id)
                    else None
                ),
                doctor_count=len(doctors_by_tenant.get(tenant.id, [])),
                created_at=tenant.created_at,
            )
            for tenant in tenants
        ]

    async def get_admin_client_detail(self, tenant_id: str) -> AdminClientDetailResponse:
        """Get tenant client details with all doctor users for platform admins."""
        tenant_result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        doctor_result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant.id, User.role == "doctor")
            .order_by(User.created_at.asc())
        )
        doctors = doctor_result.scalars().all()

        return AdminClientDetailResponse(
            tenant=TenantResponse.model_validate(tenant),
            doctors=[AdminClientDoctorResponse.model_validate(doctor) for doctor in doctors],
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            approved_at=tenant.approved_at,
            approved_by=tenant.approved_by,
        )

    async def approve_tenant(self, tenant_id: str, admin_user_id: str) -> TenantResponse:
        """Approve a pending tenant so users can log in."""
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        tenant.is_approved = True
        tenant.approved_at = datetime.now(timezone.utc)
        tenant.approved_by = admin_user_id

        await self.db.commit()
        await self.db.refresh(tenant)
        return TenantResponse.model_validate(tenant)
