import asyncio
from typing import AsyncGenerator
from loguru import logger
from app.config import settings

class MarketScanner:
    def __init__(self):
        self.bearer_token = settings.TWITTER_BEARER_TOKEN

    async def stream_social_narratives(self) -> AsyncGenerator[str, None]:
        """
        Streams market social signals.
        Yields raw content strings for AI processing.
        """
        logger.info("Initializing social narrative scanner feed...")
        
        # Initial boot sample signal for validation
        yield "Breaking: Solana meme community going crazy over $PEPEHAT mint address: 7EYnhQoR9YM3N7UoaKRoA44Uy8JeaencoqurzbR6gk5P"

        while True:
            # Polling loop for active market chatter
            await asyncio.sleep(60)
