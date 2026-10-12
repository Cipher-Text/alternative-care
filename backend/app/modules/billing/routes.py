"""Clinic-facing billing: messaging credit balances and history."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import CreditService
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.core.messaging import email_configured, sms_configured
from app.shared.schemas.credits import ChannelBalance, CreditSummary, LedgerEntry

router = APIRouter()

# Doctors and receptionists can see the balance (receptionists send reminders); history is the
# clinic's own. Platform users have no tenant and no balance.
TenantStaff = Annotated[CurrentUser, Depends(require_role("doctor", "receptionist"))]


@router.get("/credits", response_model=CreditSummary)
async def get_credits(db: Annotated[AsyncSession, Depends(get_db)], user: TenantStaff):
    summary = await CreditService(db, user.tenant_id).summary()
    return CreditSummary(
        channels=[ChannelBalance(**s.__dict__) for s in summary],
        sms_available=sms_configured(),
        email_available=email_configured(),
    )


@router.get("/credits/ledger", response_model=list[LedgerEntry])
async def get_credit_ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: TenantStaff,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await CreditService(db, user.tenant_id).ledger(limit, offset)
