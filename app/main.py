import asyncio
from datetime import datetime
from typing import List, Dict, Any
from aiohttp import web
from loguru import logger

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

def log_event(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    STORE["logs"].insert(0, {"time": timestamp, "msg": msg, "level": level})
    if len(STORE["logs"]) > 50:
        STORE["logs"].pop()

class MemeRadarApp:
    def __init__(self):
        self.scanner = MarketNarrativeScanner()
        self.telegram = TelegramAlertService()

    async def handle_home(self, request):
        return web.Response(text=HTML_DASHBOARD, content_type='text/html')

    async def handle_stream_api(self, request):
        return web.json_response({
            "tokens": STORE["tokens"],
            "total_discovered": STORE["total_discovered"],
            "total_alerts": STORE["total_alerts"],
            "logs": STORE["logs"]
        })

    async def scanner_background_loop(self):
        log_event("Scanner started. Polling DexScreener & X for real viral meme coins...", "INFO")
        
        # Clean startup message without fake $0 coin cards
        await self.telegram.send_system_message(
            "🟢 *Solana Meme Radar is ONLINE!*\n"
            "Actively monitoring DexScreener, Pump.fun & X. Only verified high-liquidity meme alerts will appear below."
        )

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
                        
                        log_event(f"Viral Token Found: ${token['symbol']} (Liq: ${token['liquidity_usd']:,.0f})", "ALERT")
                        
                        # Send Real Coin Alert to Telegram
                        await self.telegram.send_token_alert(token, session=session)
                        await asyncio.sleep(1.5)

                except Exception as e:
                    logger.error(f"Scanner error: {e}")
                    log_event(f"Scanner iteration error: {str(e)}", "WARN")

                await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)

    async def start_server(self):
        app = web.Application()
        app.router.add_get("/", self.handle_home)
        app.router.add_get("/api/stream", self.handle_stream_api)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", settings.PORT)
        await site.start()
        log_event(f"Dashboard server active on port {settings.PORT}", "INFO")

    async def run(self):
        await self.start_server()
        asyncio.create_task(self.scanner_background_loop())
        while True:
            await asyncio.sleep(3600)

async def main():
    server = MemeRadarApp()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
