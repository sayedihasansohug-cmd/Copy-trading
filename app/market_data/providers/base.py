python
Copy
from abc import ABC, abstractmethod
from typing import Any, Dict

class MarketDataProviderError(Exception):
    """Base exception for market data provider errors."""

class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    """

    @abstractmethod
    def fetch(self, token_address: str) -> Dict[str, Any]:
        """
        Fetch raw market data for the given token_address.
        Should return a dict that can be passed to normalize_market_data.
        """
        pass
