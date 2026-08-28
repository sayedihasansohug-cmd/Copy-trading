"""
Read-only market data provider for Solana tokens.

This module:
- Fetches public market data
- Extracts liquidity, volume, price and market cap
- Normalizes the data for the AI analyzer
- Never executes trades
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest/dex"

DEFAULT_TIMEOUT = 15


class MarketDataError(Exception):
    """Base exception for market data errors."""


class MarketDataRequestError(MarketDataError):
    """Raised when the market data request fails."""


class MarketDataResponseError(MarketDataError):
    """Raised when the market data response is invalid."""


class SolanaMarketData:
    """
    Read-only Solana market data provider.

    IMPORTANT:
    This class only reads market information.
    It does not buy, sell, swap, or execute transactions.
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:

        self.timeout = timeout

    # ========================================================
    # PUBLIC API
    # ========================================================

    def get_token_data(
        self,
        token_address: str,
    ) -> dict[str, Any]:
        """
        Fetch normalized market data for one Solana token.
        """

        address = token_address.strip()

        if not address:
            raise ValueError(
                "token_address cannot be empty."
            )

        pairs = self._fetch_token_pairs(address)

        pair = self._select_best_pair(pairs)

        if pair is None:
            raise MarketDataResponseError(
                "No valid Solana trading pair was found."
            )

        return self._normalize_pair(
            pair=pair,
            token_address=address,
        )

    # ========================================================
    # HTTP REQUEST
    # ========================================================

    def _fetch_token_pairs(
        self,
        token_address: str,
    ) -> list[dict[str, Any]]:

        url = (
            f"{DEXSCREENER_BASE_URL}/tokens/"
            f"{token_address}"
        )

        try:

            response = requests.get(
                url,
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            logger.exception(
                "Market data request failed."
            )

            raise MarketDataRequestError(
                f"Market data request failed: {exc}"
            ) from exc

        if response.status_code >= 400:

            raise MarketDataRequestError(
                "Market data API returned HTTP "
                f"{response.status_code}: "
                f"{response.text[:500]}"
            )

        try:

            data = response.json()

        except ValueError as exc:

            raise MarketDataResponseError(
                "Market data API returned invalid JSON."
            ) from exc

        pairs = data.get("pairs")

        if pairs is None:
            return []

        if not isinstance(pairs, list):

            raise MarketDataResponseError(
                "Market data 'pairs' field is invalid."
            )

        valid_pairs: list[dict[str, Any]] = []

        for pair in pairs:

            if not isinstance(
                pair,
                dict,
            ):
                continue

            if pair.get("chainId") != "solana":
                continue

            valid_pairs.append(pair)

        return valid_pairs

    # ========================================================
    # PAIR SELECTION
    # ========================================================

    @staticmethod
    def _select_best_pair(
        pairs: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        if not pairs:
            return None

        def liquidity_value(
            pair: dict[str, Any],
        ) -> float:

            liquidity = pair.get(
                "liquidity"
            )

            if not isinstance(
                liquidity,
                dict,
            ):
                return 0.0

            value = liquidity.get(
                "usd"
            )

            try:
                return float(value or 0)
            except (
                TypeError,
                ValueError,
            ):
                return 0.0

        return max(
            pairs,
            key=liquidity_value,
        )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_pair(
        pair: dict[str, Any],
        token_address: str,
    ) -> dict[str, Any]:

        base_token = pair.get(
            "baseToken"
        )

        if not isinstance(
            base_token,
            dict,
        ):
            base_token = {}

        quote_token = pair.get(
            "quoteToken"
        )

        if not isinstance(
            quote_token,
            dict,
        ):
            quote_token = {}

        liquidity = pair.get(
            "liquidity"
        )

        if not isinstance(
            liquidity,
            dict,
        ):
            liquidity = {}

        volume = pair.get(
            "volume"
        )

        if not isinstance(
            volume,
            dict,
        ):
            volume = {}

        txns = pair.get(
            "txns"
        )

        if not isinstance(
            txns,
            dict,
        ):
            txns = {}

        price_usd = _to_float(
            pair.get("priceUsd")
        )

        liquidity_usd = _to_float(
            liquidity.get("usd")
        )

        market_cap = _to_float(
            pair.get("marketCap")
        )

        fdv = _to_float(
            pair.get("fdv")
        )

        volume_24h = _to_float(
            volume.get("h24")
        )

        price_change_24h = _to_float(
            (pair.get("priceChange") or {}).get("h24")
        )

        buys_24h = _extract_transaction_count(
            txns,
            "h24",
            "buys",
        )

        sells_24h = _extract_transaction_count(
            txns,
            "h24",
            "sells",
        )

        return {
            "chain": "solana",
            "token_address": token_address,
            "pair_address": pair.get(
                "pairAddress"
            ),
            "dex": pair.get(
                "dexId"
            ),
            "base_symbol": base_token.get(
                "symbol"
            ),
            "base_name": base_token.get(
                "name"
            ),
            "quote_symbol": quote_token.get(
                "symbol"
            ),
            "price_usd": price_usd,
            "liquidity_usd": liquidity_usd,
            "market_cap": market_cap,
            "fdv": fdv,
            "volume_24h": volume_24h,
            "price_change_24h": price_change_24h,
            "buys_24h": buys_24h,
            "sells_24h": sells_24h,
            "url": pair.get(
                "url"
            ),
        }


# ============================================================
# HELPERS
# ============================================================

def _to_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


def _extract_transaction_count(
    txns: dict[str, Any],
    period: str,
    transaction_type: str,
) -> int:

    period_data = txns.get(
        period
    )

    if not isinstance(
        period_data,
        dict,
    ):
        return 0

    value = period_data.get(
        transaction_type
    )

    try:
        return int(value or 0)

    except (
        TypeError,
        ValueError,
    ):
        return 0
