"""
Market data service for Solana tokens.

Responsibilities:

- Fetch token market information
- Normalize API responses
- Validate market data
- Calculate basic market metrics
- Never execute trades
"""

from __future__ import annotations

import logging
import time
from typing import Any, Mapping

import requests

logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    """Base exception for market data errors."""


class MarketDataRequestError(MarketDataError):
    """Raised when a market data request fails."""


class MarketDataValidationError(MarketDataError):
    """Raised when market data is invalid."""


class MarketDataService:
    """
    Central market-data service.

    This class only collects and normalizes information.
    It does not buy or sell tokens.
    """

    def __init__(
        self,
        timeout: int = 10,
        session: requests.Session | None = None,
    ) -> None:

        self.timeout = timeout

        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "Solana-Copy-Trading-Bot/1.0",
            }
        )

    # =====================================================
    # PUBLIC API
    # =====================================================

    def get_token_market_data(
        self,
        token_address: str,
    ) -> dict[str, Any]:

        self._validate_token_address(
            token_address
        )

        raise NotImplementedError(
            "Market-data provider integration will be added "
            "in the provider module."
        )

    # =====================================================
    # NORMALIZATION
    # =====================================================

    @staticmethod
    def normalize_market_data(
        token_address: str,
        raw_data: Mapping[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(
            raw_data,
            Mapping,
        ):
            raise MarketDataValidationError(
                "raw_data must be a mapping."
            )

        normalized: dict[str, Any] = {
            "token_address": token_address,
            "symbol": _safe_string(
                raw_data.get("symbol")
            ),
            "name": _safe_string(
                raw_data.get("name")
            ),
            "chain": "solana",
            "price": _safe_float(
                raw_data.get("price")
            ),
            "price_change_1m": _safe_float(
                raw_data.get("price_change_1m")
            ),
            "price_change_5m": _safe_float(
                raw_data.get("price_change_5m")
            ),
            "price_change_15m": _safe_float(
                raw_data.get("price_change_15m")
            ),
            "price_change_1h": _safe_float(
                raw_data.get("price_change_1h")
            ),
            "volume_1m": _safe_float(
                raw_data.get("volume_1m")
            ),
            "volume_5m": _safe_float(
                raw_data.get("volume_5m")
            ),
            "volume_15m": _safe_float(
                raw_data.get("volume_15m")
            ),
            "volume_1h": _safe_float(
                raw_data.get("volume_1h")
            ),
            "market_cap": _safe_float(
                raw_data.get("market_cap")
            ),
            "fdv": _safe_float(
                raw_data.get("fdv")
            ),
            "liquidity_usd": _safe_float(
                raw_data.get("liquidity_usd")
            ),
            "holders": _safe_int(
                raw_data.get("holders")
            ),
            "top_holder_percent": _safe_float(
                raw_data.get("top_holder_percent")
            ),
            "top_10_holder_percent": _safe_float(
                raw_data.get("top_10_holder_percent")
            ),
            "buy_count": _safe_int(
                raw_data.get("buy_count")
            ),
            "sell_count": _safe_int(
                raw_data.get("sell_count")
            ),
            "buy_sell_ratio": _safe_float(
                raw_data.get("buy_sell_ratio")
            ),
            "tx_count": _safe_int(
                raw_data.get("tx_count")
            ),
            "age_minutes": _safe_float(
                raw_data.get("age_minutes")
            ),
            "pair_address": _safe_string(
                raw_data.get("pair_address")
            ),
            "dex": _safe_string(
                raw_data.get("dex")
            ),
            "token_created_at": raw_data.get(
                "token_created_at"
            ),
            "mint_authority": _safe_string(
                raw_data.get("mint_authority")
            ),
            "freeze_authority": _safe_string(
                raw_data.get("freeze_authority")
            ),
            "lp_locked": _safe_bool(
                raw_data.get("lp_locked")
            ),
            "lp_burned": _safe_bool(
                raw_data.get("lp_burned")
            ),
            "contract_verified": _safe_bool(
                raw_data.get("contract_verified")
            ),
            "honeypot_check": _safe_bool(
                raw_data.get("honeypot_check")
            ),
            "tax_buy": _safe_float(
                raw_data.get("tax_buy")
            ),
            "tax_sell": _safe_float(
                raw_data.get("tax_sell")
            ),
            "developer_holding_percent": _safe_float(
                raw_data.get(
                    "developer_holding_percent"
                )
            ),
            "insider_holding_percent": _safe_float(
                raw_data.get(
                    "insider_holding_percent"
                )
            ),
            "social_score": _safe_float(
                raw_data.get("social_score")
            ),
            "website": _safe_string(
                raw_data.get("website")
            ),
            "telegram": _safe_string(
                raw_data.get("telegram")
            ),
            "twitter": _safe_string(
                raw_data.get("twitter")
            ),
            "data_timestamp": time.time(),
        }

        return normalized

    # =====================================================
    # VALIDATION
    # =====================================================

    @staticmethod
    def validate_market_data(
        data: Mapping[str, Any],
    ) -> None:

        if not isinstance(
            data,
            Mapping,
        ):
            raise MarketDataValidationError(
                "Market data must be a mapping."
            )

        token_address = data.get(
            "token_address"
        )

        if not isinstance(
            token_address,
            str,
        ):
            raise MarketDataValidationError(
                "token_address is required."
            )

        if len(token_address) < 32:
            raise MarketDataValidationError(
                "token_address appears invalid."
            )

        price = data.get("price")

        if price is not None:

            try:
                price_value = float(price)
            except (TypeError, ValueError) as exc:
                raise MarketDataValidationError(
                    "price must be numeric."
                ) from exc

            if price_value < 0:
                raise MarketDataValidationError(
                    "price cannot be negative."
                )

        liquidity = data.get(
            "liquidity_usd"
        )

        if liquidity is not None:

            try:
                liquidity_value = float(
                    liquidity
                )
            except (TypeError, ValueError) as exc:
                raise MarketDataValidationError(
                    "liquidity_usd must be numeric."
                ) from exc

            if liquidity_value < 0:
                raise MarketDataValidationError(
                    "liquidity_usd cannot be negative."
                )

    # =====================================================
    # TOKEN ADDRESS VALIDATION
    # =====================================================

    @staticmethod
    def _validate_token_address(
        token_address: str,
    ) -> None:

        if not isinstance(
            token_address,
            str,
        ):
            raise MarketDataValidationError(
                "token_address must be a string."
            )

        token_address = token_address.strip()

        if not token_address:
            raise MarketDataValidationError(
                "token_address cannot be empty."
            )

        if len(token_address) < 32:
            raise MarketDataValidationError(
                "Invalid Solana token address."
            )


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def _safe_string(
    value: Any,
) -> str | None:

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def _safe_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(
    value: Any,
) -> bool | None:

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str,
    ):

        normalized = value.strip().lower()

        if normalized in {
            "true",
            "1",
            "yes",
            "on",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
            "off",
        }:
            return False

    return None
