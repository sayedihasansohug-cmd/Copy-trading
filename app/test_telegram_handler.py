"""
Tests for Telegram token-address extraction.

No real Telegram connection is used.
No real trade is executed.
"""

from __future__ import annotations

import unittest

from app.telegram_handler import (
    TelegramHandler,
)


class TelegramHandlerTests(unittest.TestCase):

    def test_extract_token_address(self) -> None:

        address = (
            "So11111111111111111111111111111111111111112"
        )

        message = (
            f"BUY this token: {address}"
        )

        result = (
            TelegramHandler.extract_token_address(
                message
            )
        )

        self.assertEqual(
            result,
            address,
        )

    def test_no_address(self) -> None:

        message = (
            "This message contains no token address."
        )

        result = (
            TelegramHandler.extract_token_address(
                message
            )
        )

        self.assertIsNone(
            result,
        )


if __name__ == "__main__":
    unittest.main()
