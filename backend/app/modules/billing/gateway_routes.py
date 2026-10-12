"""Public callbacks for real payment gateways. No login: these are called by the customer's browser
and by the providers' servers.

NOTHING here trusts what it is sent. Each callback only identifies the order, then asks the provider
(server to server) what happened and settles from that answer, so a forged "success" for an unpaid
order changes nothing. Settling is idempotent, so repeated or racing callbacks are harmless."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.billing.gateways import get_gateway
from app.modules.billing.gateways.base import GatewayResult
from app.modules.billing.orders import OrderService
from app.shared.models import BillingOrder

logger = structlog.get_logger()
router = APIRouter()


def _return_to(order: BillingOrder | None) -> RedirectResponse:
    """Send the browser back to the app, where the return page shows the settled outcome."""
    base = settings.FRONTEND_URL.rstrip("/")
    url = f"{base}/billing/return?order={order.id}" if order else f"{base}/billing"
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


async def _params(request: Request) -> dict:
    """Form fields (the providers POST) merged with the query string."""
    merged = dict(request.query_params)
    if request.method == "POST":
        try:
            merged.update({k: v for k, v in (await request.form()).items() if isinstance(v, str)})
        except Exception:  # noqa: BLE001 — a body that is not a form is simply ignored
            pass
    return merged


async def _by_receipt(db: AsyncSession, receipt_no: str | None, gateway: str) -> BillingOrder | None:
    if not receipt_no:
        return None
    return (
        await db.execute(
            select(BillingOrder).where(BillingOrder.receipt_no == receipt_no, BillingOrder.gateway == gateway)
        )
    ).scalar_one_or_none()


@router.api_route("/sslcommerz/{outcome}", methods=["GET", "POST"])
async def sslcommerz_return(
    outcome: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    """success / fail / cancel (the browser) and ipn (SSLCommerz's server)."""
    if outcome not in ("success", "fail", "cancel", "ipn"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    try:
        gateway = get_gateway("sslcommerz")
    except HTTPException as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found") from exc

    params = await _params(request)
    order = await _by_receipt(db, params.get("tran_id"), "sslcommerz")
    if order is None:
        logger.warning("sslcommerz_callback_unknown_order", outcome=outcome)
        return JSONResponse({"ok": False}) if outcome == "ipn" else _return_to(None)

    service = OrderService(db)
    try:
        result = await gateway.verify(order)  # the provider's answer, not the callback's claim
    except HTTPException:
        # The provider is unreachable: change nothing. The return page polls and settles when it is back.
        return JSONResponse({"ok": False}, status_code=503) if outcome == "ipn" else _return_to(order)
    if result.status == "pending" and outcome in ("fail", "cancel"):
        # The customer says they did not pay and SSLCommerz has no valid payment for it
        result = GatewayResult(status="cancelled" if outcome == "cancel" else "failed", raw={"callback": outcome})
    order = await service.settle(order.id, result)
    return JSONResponse({"ok": True}) if outcome == "ipn" else _return_to(order)


@router.get("/bkash/callback")
async def bkash_callback(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    """bKash redirects the browser here with paymentID and status (success, failure or cancel)."""
    try:
        gateway = get_gateway("bkash")
    except HTTPException as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found") from exc

    params = dict(request.query_params)
    payment_id = params.get("paymentID")
    order = None
    if payment_id:
        order = (
            await db.execute(
                select(BillingOrder)
                .where(
                    BillingOrder.gateway == "bkash",
                    func.json_extract_path_text(BillingOrder.gateway_data, "session_id") == payment_id,
                )
                .limit(1)
            )
        ).scalars().first()
    if order is None:
        logger.warning("bkash_callback_unknown_payment")
        return _return_to(None)

    try:
        result = await gateway.handle_return(order, params)
    except HTTPException:
        return _return_to(order)  # provider unreachable: nothing changes; the return page keeps checking
    order = await OrderService(db).settle(order.id, result)
    return _return_to(order)
