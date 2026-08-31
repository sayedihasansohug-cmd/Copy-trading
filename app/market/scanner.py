import asyncio
import json
import re
import httpx
from datetime import datetime

STREAM_URL = "https://api.twitter.com/2/tweets/search/stream"
RULES_URL = f"{STREAM_URL}/rules"

CASHTAG_RE = re.compile(r"\$([A-Za-z]{2,10})\b")
MINT_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")


class TwitterListener:
    def __init__(self, bearer_token: str, signal_queue: asyncio.Queue):
        self.bearer_token = bearer_token
        self.signal_queue = signal_queue
        self.headers = {"Authorization": f"Bearer {bearer_token}"}

    async def setup_rules(self, rules: list[str]):
        async with httpx.AsyncClient() as client:
            existing = await client.get(RULES_URL, headers=self.headers)
            existing_ids = [r["id"] for r in existing.json().get("data", [])]
            if existing_ids:
                await client.post(
                    RULES_URL,
                    headers=self.headers,
                    json={"delete": {"ids": existing_ids}},
                )
            await client.post(
                RULES_URL,
                headers=self.headers,
                json={"add": [{"value": r} for r in rules]},
            )

    def _parse_signal(self, tweet_data: dict) -> dict | None:
        text = tweet_data.get("data", {}).get("text", "")
        cashtags = CASHTAG_RE.findall(text)
        mints = MINT_RE.findall(text)
        if not cashtags and not mints:
            return None
        return {
            "source": "twitter",
            "tweet_id": tweet_data["data"]["id"],
            "text": text,
            "cashtags": cashtags,
            "possible_mints": mints,
            "seen_at": datetime.utcnow().isoformat(),
            "author_id": tweet_data["data"].get("author_id"),
        }

    async def run(self):
        params = {"tweet.fields": "author_id,created_at"}
        backoff = 1
        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "GET", STREAM_URL, headers=self.headers, params=params
                    ) as response:
                        backoff = 1
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            try:
                                tweet_data = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            signal = self._parse_signal(tweet_data)
                            if signal:
                                await self.signal_queue.put(signal)
            except (httpx.HTTPError, asyncio.CancelledError):
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
