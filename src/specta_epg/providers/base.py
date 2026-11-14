from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Programme


class ProviderAdapter(ABC):
    provider_id: str

    @abstractmethod
    def list_channels(self) -> list[dict]:
        """Return source channel records with stable provider IDs and names."""

    @abstractmethod
    def fetch_programmes(self, provider_channel_id: str, days: int) -> list[Programme]:
        """Fetch normalized programmes for one provider channel."""
