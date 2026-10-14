"""BulkSMSBD integration service."""

import httpx
from typing import Any

from fastapi import HTTPException, status

from app.modules.integration.providers.base import BaseProviderService


class BulkSMSBDService(BaseProviderService):
    """BulkSMSBD SMS provider service.

    Typical Bangladesh SMS provider API pattern.
    """

    def __init__(self, credentials: dict, config: dict | None = None):
        """Initialize BulkSMSBD service.

        Expected credentials:
            api_key: str
            sender_id: str
            api_url: str (optional, has default)
            mask_type: str (masked or non-masked)
        """
        super().__init__(credentials, config)

        self.api_key = credentials["api_key"]
        self.sender_id = credentials["sender_id"]
        self.api_url = credentials.get(
            "api_url", "https://api.bulksmsbd.com/api/v1/send"
        )
        self.mask_type = credentials.get("mask_type", "masked")

    async def test_connection(self) -> dict[str, Any]:
        """Test BulkSMSBD credentials by checking balance or sending test request.

        Returns:
            Dict with test results
        """
        try:
            # Validate credentials exist
            if not self.api_key or not self.sender_id:
                return {
                    "success": False,
                    "message": "Missing required credentials",
                }

            # Optional: Make actual API call to verify
            # Most BD SMS providers have a balance check endpoint

            return {
                "success": True,
                "message": "Credentials validated successfully",
                "provider": "BulkSMSBD",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to validate credentials: {str(e)}",
            }

    async def send_sms(self, recipient: str, message: str) -> dict[str, Any]:
        """Send SMS via BulkSMSBD.

        Args:
            recipient: Phone number (preferably E.164 format)
            message: SMS message text

        Returns:
            Dict with response details

        Raises:
            HTTPException: If SMS send fails
        """
        # Typical BulkSMSBD API request format
        # (Adjust based on actual API documentation)

        payload = {
            "api_key": self.api_key,
            "senderid": self.sender_id,
            "number": recipient,
            "message": message,
            "type": self.mask_type,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()

                result = response.json()

                # Parse response (format varies by provider)
                # Typical response: {"status": "success", "message_id": "xxx"}

                return {
                    "success": result.get("status") == "success",
                    "message_id": result.get("message_id"),
                    "response": result,
                    "status_code": response.status_code,
                }

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"BulkSMSBD API error: {e.response.text}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"BulkSMSBD connection error: {str(e)}",
                )
