import time
import json
import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.market_data.providers.base import MarketDataProvider, MarketDataProviderError

logger = logging.getLogger(__name__)

class HTTPProviderError(MarketDataProviderError):
    """HTTP provider base exception."""

class HTTPProviderRequestError(HTTPProviderError):
    """Raised when the HTTP request fails."""

class HTTPProviderValidationError(HTTPProviderError):
    """Raised when the response data is invalid or missing fields."""

class HTTPProvider(MarketDataProvider):
    """
    A simple HTTP provider that fetches market data from a REST endpoint.
    Parameters:
        base_url: The base API endpoint (e.g. "https://api.example.com/token")
        api_key: Optional API key for authorization.
        timeout: Request timeout in seconds.
        max_retries: Number of retries for transient errors.
        backoff_factor: Backoff multiplier between retries.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 5,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        # Set API key in header if provided
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f"Bearer {api_key}"

        # Configure retries with backoff
      retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def fetch(self, token_address: str) -> Dict[str, Any]:
        """
        Fetch raw market data for the token. Returns JSON-decoded dict.
        """
        url = f"{self.base_url}?mint={token_address}"
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise HTTPProviderRequestError(f"HTTP request failed: {e}")

        if response.status_code != 200:
            logger.error(f"Non-200 status code {response.status_code}: {response.text}")
            raise HTTPProviderRequestError(f"Unexpected status {response.status_code}")

        try:
          data = response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise HTTPProviderValidationError(f"Response is not valid JSON: {e}")

        # Basic validation: ensure essential fields are present
        if not isinstance(data, dict) or 'symbol' not in data or 'price' not in data:
            logger.error(f"Missing required fields in response: {data}")
            raise HTTPProviderValidationError("Response JSON missing required fields")

        return data
