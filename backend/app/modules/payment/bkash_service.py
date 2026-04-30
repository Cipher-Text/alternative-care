"""bKash Payment Gateway integration service."""

import httpx
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings


class BkashService:
    """Service for bKash Payment Gateway API integration.

    API Documentation: https://developer.bka.sh/docs/tokenized-checkout
    Version: v1.2.0-beta
    """

    def __init__(self):
        """Initialize bKash service with configuration."""
        self.base_url = settings.BKASH_BASE_URL
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD

        # Token cache
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_headers(self, include_auth: bool = True) -> dict:
        """Get request headers for bKash API."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if include_auth:
            token = await self._get_token()
            headers["Authorization"] = token
            headers["X-APP-Key"] = self.app_key

        return headers

    async def _get_token(self) -> str:
        """Get or refresh bKash access token.

        Returns:
            Access token string

        Raises:
            HTTPException: If token grant fails
        """
        # Return cached token if still valid
        if self._token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._token

        # Request new token
        url = f"{self.base_url}/tokenized/checkout/token/grant"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "username": self.username,
            "password": self.password,
        }
        data = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()
                self._token = result.get("id_token")
                expires_in = result.get("expires_in", 3600)  # Default 1 hour

                # Cache token with 5-minute buffer
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)

                return self._token

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash token grant failed: {e.response.text}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash connection error: {str(e)}",
                )

    async def create_payment(
        self,
        amount: float,
        invoice_number: str,
        callback_url: str = None,
        intent: str = "sale",
    ) -> dict:
        """Create a bKash payment.

        Args:
            amount: Payment amount in BDT
            invoice_number: Merchant invoice number (unique)
            callback_url: URL to redirect after payment (optional)
            intent: Payment intent - "sale" or "authorization"

        Returns:
            dict with paymentID and bkashURL

        Raises:
            HTTPException: If payment creation fails
        """
        url = f"{self.base_url}/tokenized/checkout/create"
        headers = await self._get_headers(include_auth=True)

        data = {
            "mode": "0011",  # Wallet payment
            "payerReference": " ",  # Optional customer reference
            "callbackURL": callback_url or "https://altcare.health/payment/callback",
            "amount": str(amount),
            "currency": "BDT",
            "intent": intent,
            "merchantInvoiceNumber": invoice_number,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                # Check for errors in response
                if result.get("statusCode") != "0000":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"bKash error: {result.get('statusMessage', 'Unknown error')}",
                    )

                return {
                    "paymentID": result.get("paymentID"),
                    "bkashURL": result.get("bkashURL"),
                    "callbackURL": result.get("callbackURL"),
                    "amount": result.get("amount"),
                    "intent": result.get("intent"),
                    "merchantInvoiceNumber": result.get("merchantInvoiceNumber"),
                }

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash create payment failed: {e.response.text}",
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash connection error: {str(e)}",
                )

    async def execute_payment(self, payment_id: str) -> dict:
        """Execute a bKash payment after user completes payment.

        Args:
            payment_id: Payment ID from create response

        Returns:
            dict with transaction details

        Raises:
            HTTPException: If payment execution fails
        """
        url = f"{self.base_url}/tokenized/checkout/execute"
        headers = await self._get_headers(include_auth=True)
        data = {"paymentID": payment_id}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                # Check execution status
                if result.get("statusCode") != "0000":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"bKash execution failed: {result.get('statusMessage', 'Unknown error')}",
                    )

                return {
                    "paymentID": result.get("paymentID"),
                    "trxID": result.get("trxID"),
                    "transactionStatus": result.get("transactionStatus"),
                    "amount": result.get("amount"),
                    "merchantInvoiceNumber": result.get("merchantInvoiceNumber"),
                    "customerMsisdn": result.get("customerMsisdn"),
                    "paymentExecuteTime": result.get("paymentExecuteTime"),
                }

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash execute payment failed: {e.response.text}",
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash connection error: {str(e)}",
                )

    async def query_payment(self, payment_id: str) -> dict:
        """Query bKash payment status.

        Args:
            payment_id: Payment ID to query

        Returns:
            dict with payment status

        Raises:
            HTTPException: If query fails
        """
        url = f"{self.base_url}/tokenized/checkout/payment/status"
        headers = await self._get_headers(include_auth=True)
        data = {"paymentID": payment_id}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                return {
                    "paymentID": result.get("paymentID"),
                    "trxID": result.get("trxID"),
                    "transactionStatus": result.get("transactionStatus"),
                    "amount": result.get("amount"),
                    "merchantInvoiceNumber": result.get("merchantInvoiceNumber"),
                    "customerMsisdn": result.get("customerMsisdn"),
                    "verificationStatus": result.get("verificationStatus"),
                    "paymentExecuteTime": result.get("paymentExecuteTime"),
                }

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash query payment failed: {e.response.text}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash connection error: {str(e)}",
                )

    async def refund_payment(
        self,
        payment_id: str,
        amount: float,
        trx_id: str,
        sku: str = "payment",
        reason: str = "Refund requested",
    ) -> dict:
        """Refund a bKash payment.

        Args:
            payment_id: Original payment ID
            amount: Refund amount in BDT
            trx_id: Transaction ID from execute response
            sku: SKU reference (default: "payment")
            reason: Refund reason

        Returns:
            dict with refund details

        Raises:
            HTTPException: If refund fails
        """
        url = f"{self.base_url}/tokenized/checkout/payment/refund"
        headers = await self._get_headers(include_auth=True)

        data = {
            "paymentID": payment_id,
            "amount": str(amount),
            "trxID": trx_id,
            "sku": sku,
            "reason": reason,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                # Check refund status
                if result.get("statusCode") != "0000":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"bKash refund failed: {result.get('statusMessage', 'Unknown error')}",
                    )

                return {
                    "originalTrxID": result.get("originalTrxID"),
                    "refundTrxID": result.get("refundTrxID"),
                    "transactionStatus": result.get("transactionStatus"),
                    "amount": result.get("amount"),
                    "completedTime": result.get("completedTime"),
                }

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash refund failed: {e.response.text}",
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"bKash connection error: {str(e)}",
                )


# Singleton instance
bkash_service = BkashService()
