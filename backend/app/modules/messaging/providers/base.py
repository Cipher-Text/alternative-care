"""Base provider service interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseProviderService(ABC):
    """Base class for all provider services."""

    def __init__(self, credentials: dict, config: dict | None = None):
        """Initialize provider with credentials.

        Args:
            credentials: Decrypted credentials dict
            config: Optional provider configuration
        """
        self.credentials = credentials
        self.config = config or {}

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test provider connection/credentials.

        Returns:
            Dict with test results
        """
        pass
