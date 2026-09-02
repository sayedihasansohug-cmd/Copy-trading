import sys
import os
import asyncio
from typing import Dict, Any
from aiohttp import web
import aiohttp
from loguru import logger

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.config import settings
from app.scanner import MarketNarrativeScanner
from app.telegram_service import TelegramAlertService
from app.ui import HTML_DASHBOARD

STORE: Dict[str, Any] = {
    "tokens": [],
    "total_discovered": 0,
    "total_alerts": 0,
    "logs": []
}

class MemeRadarApp:
    def __init__(self):
        self.scanner = MarketNarrativeScanner()
        self.telegram = TelegramAlertService()

    async def handle_home(self, request):
        return web.Response(text=HTML_DASHBOARD, content_type='text/html')

    async def handle_health(self, request):
        return web.Response(text="OK", content_type='text/plain')

    async def handle_manifest(self, request):
        return web.json_response({
            "name": "Axiom Alpha Radar",
            "short_name": "AlphaRadar",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#050505",
            "theme_color": "#ff2a4d"
        })

    async def handle_stream_api(self, request):
        return web.json_response({
            "tokens": STORE["tokens"],
            "total_discovered": STORE["total_discovered"],
            "total_alerts": STORE["total_alerts"],
            "logs": STORE["logs"]
        })

    async def keep_alive_self_ping_loop(self):
        await asyncio.sleep(20)
        self_url = f"http://127.0.0.1:{settings.PORT}/health"
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(self_url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                        pass
                except Exception:
                    pass
                await asyncio.sleep(240)

    async def scanner_background_loop(self):
        logger.info("Alpha Signal Radar initiated. Live streaming Pump.fun & DexScreener...")

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    new_tokens = await self.scanner.scan_latest_viral_tokens(session)
                    for token in new_tokens:
                        STORE["tokens"].insert(0, token)
                        if len(STORE["tokens"]) > 40:
                            STORE["tokens"].pop()

                        STORE["total_discovered"] += 1
                        STORE["total_alerts"] += 1

                        # Send Real Coin Signal
                        await self.telegram.send_token_alert(token, session=session)
                        await asyncio.sleep(1.5)

                except Exception as e:
                    logger.debug(f"Scanner cycle retry: {e}")

                await asyncio.sleep(6)

    async def start_server(self):
        app = web.Application()
        app.router.add_get("/", self.handle_home)
        app.router.add_get("/health", self.handle_health)
        app.router.add_get("/manifest.json", self.handle_manifest)
        app.router.add_get("/api/stream", self.handle_stream_api)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", settings.PORT)
        await site.start()

    async def run(self):
        await self.start_server()
        asyncio.create_task(self.keep_alive_self_ping_loop())
        asyncio.create_task(self.scanner_background_loop())
        while True:
            await asyncio.sleep(3600)

async def main():
    server = MemeRadarApp()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
