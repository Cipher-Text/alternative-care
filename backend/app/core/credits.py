"""Messaging credits: plan allowance first, then purchased credits, never below zero.

A clinic's SMS/email budget is (a) the plan's monthly allowance, measured against `usage_tracking`,
and (b) credits it bought, held in `credit_balances` with an append-only `credit_ledger`.
`spend()` takes from the allowance while any is left, then from purchased credits with a single
conditional UPDATE (so two concurrent sends cannot spend the same last credit), and otherwise
raises a structured 403 the UI turns into a "buy credits / upgrade" prompt.
"""

from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entitlements import EntitlementService
from app.core.usage_tracking import UsageService
from app.shared.models import CreditBalance, CreditLedger

Channel = Literal["sms", "email"]
Source = Literal["allowance", "purchased"]

ENTITLEMENT_KEY = {"sms": "monthly_sms", "email": "monthly_email"}
USAGE_FIELD = {"sms": "sms_sent", "email": "emails_sent"}


@dataclass
class ChannelSummary:
    channel: str
    allowance_limit: int | None  # None = unlimited
    allowance_used: int
    allowance_remaining: int | None
    purchased: int
    plan: str


class CreditService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def _allowance(self, channel: Channel) -> tuple[int | None, int, str]:
        """(limit, used this month, applied plan). A plan without the entitlement has limit 0."""
        plan, _expired, effective = await EntitlementService(self.db).resolve(self.tenant_id)
        item = effective[ENTITLEMENT_KEY[channel]]
        limit = item.limit if item.enabled else 0
        month = await UsageService(self.db, self.tenant_id).get_month_to_date()
        return limit, int(month[USAGE_FIELD[channel]]), plan

    async def balance(self, channel: Channel) -> int:
        row = (
            await self.db.execute(
                select(CreditBalance.balance).where(
                    CreditBalance.tenant_id == self.tenant_id, CreditBalance.channel == channel
                )
            )
        ).scalar_one_or_none()
        return int(row or 0)

    async def summary(self) -> list[ChannelSummary]:
        out = []
        for channel in ("sms", "email"):
            limit, used, plan = await self._allowance(channel)
            out.append(
                ChannelSummary(
                    channel=channel,
                    allowance_limit=limit,
                    allowance_used=used,
                    allowance_remaining=None if limit is None else max(0, limit - used),
                    purchased=await self.balance(channel),
                    plan=plan,
                )
            )
        return out

    async def spend(self, channel: Channel, n: int = 1, reference: str | None = None) -> Source:
        limit, used, plan = await self._allowance(channel)
        if limit is None or used + n <= limit:
            await UsageService(self.db, self.tenant_id).increment(USAGE_FIELD[channel], n)
            return "allowance"

        # Allowance spent: take from purchased credits atomically (balance can never go negative)
        updated = (
            await self.db.execute(
                update(CreditBalance)
                .where(
                    CreditBalance.tenant_id == self.tenant_id,
                    CreditBalance.channel == channel,
                    CreditBalance.balance >= n,
                )
                .values(balance=CreditBalance.balance - n)
                .returning(CreditBalance.balance)
            )
        ).first()
        if updated is None:
            purchased = await self.balance(channel)
            await self.db.rollback()
            noun = "SMS" if channel == "sms" else "emails"
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "credits_exhausted",
                    "message": (
                        f"You have used your monthly {noun} allowance ({used} of {limit}) and have no "
                        "purchased credits left. Buy credits or upgrade your plan to continue."
                    ),
                    "channel": channel,
                    "allowance_limit": limit,
                    "allowance_used": used,
                    "purchased": purchased,
                    "plan": plan,
                },
            )
        self.db.add(
            CreditLedger(
                tenant_id=self.tenant_id,
                channel=channel,
                kind="use",
                quantity=-n,
                balance_after=updated[0],
                reference=reference,
            )
        )
        await self.db.commit()
        return "purchased"

    async def refund(
        self, channel: Channel, source: Source, n: int = 1, reference: str | None = None
    ) -> None:
        """Give back a credit for a send that failed for good."""
        if source == "allowance":
            await UsageService(self.db, self.tenant_id).increment(USAGE_FIELD[channel], -n)
            return
        await self._add_purchased(channel, n, "refund", reference, None, None)

    async def grant(
        self,
        channel: Channel,
        n: int,
        kind: Literal["purchase", "adjustment"],
        reference: str | None = None,
        note: str | None = None,
        created_by: str | None = None,
    ) -> int:
        """Add (or, for an admin adjustment, remove) purchased credits. Returns the new balance."""
        return await self._add_purchased(channel, n, kind, reference, note, created_by)

    async def _add_purchased(self, channel, n, kind, reference, note, created_by) -> int:
        # Upsert so the first purchase creates the row; the CHECK (balance >= 0) rejects over-removal
        try:
            new_balance = (
                await self.db.execute(
                    text(
                        "INSERT INTO credit_balances (tenant_id, channel, balance) "
                        "VALUES (:t, :c, :n) "
                        "ON CONFLICT (tenant_id, channel) DO UPDATE "
                        "SET balance = credit_balances.balance + :n, updated_at = now() "
                        "RETURNING balance"
                    ),
                    {"t": self.tenant_id, "c": channel, "n": n},
                )
            ).scalar_one()
        except Exception as exc:  # CHECK violation on over-removal, or a bad tenant
            await self.db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Adjustment would make the credit balance negative",
            ) from exc
        self.db.add(
            CreditLedger(
                tenant_id=self.tenant_id,
                channel=channel,
                kind=kind,
                quantity=n,
                balance_after=new_balance,
                reference=reference,
                note=note,
                created_by=created_by,
            )
        )
        await self.db.commit()
        return int(new_balance)

    async def ledger(self, limit: int = 50, offset: int = 0) -> list[CreditLedger]:
        rows = await self.db.execute(
            select(CreditLedger)
            .where(CreditLedger.tenant_id == self.tenant_id)
            .order_by(CreditLedger.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().all())
