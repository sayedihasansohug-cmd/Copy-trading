import sys
import os
import time
import asyncio
from datetime import datetime
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
from app.market.token_data import TokenDataFetcher
from app.market.filter_engine import FilterEngine
from app.ai.analyzer import AIAnalyzer
from app.telegram.bot import TelegramNotifier

if settings.LIVE_TRADING:
    raise RuntimeError("CRITICAL: LIVE_TRADING must remain False for Signal Radar Mode.")

STATE: Dict[str, Any] = {
    "bot_status": "ONLINE",
    "scanner_status": "SCANNING",
    "ai_status": "ACTIVE",
    "telegram_status": "CONNECTED",
    "coins_scanned": 0,
    "signals_generated": 0,
    "signals_rejected": 0,
    "last_scan_time": "Never",
    "last_signal_time": "Never",
    "last_error": "None",
    "cooldown_tracker": {}
}

def is_in_cooldown(mint: str) -> bool:
    now = time.time()
    last_sent = STATE["cooldown_tracker"].get(mint)
    if not last_sent:
        return False
    return (now - last_sent) < (settings.SIGNAL_COOLDOWN_MINUTES * 60)

def record_cooldown(mint: str):
    STATE["cooldown_tracker"][mint] = time.time()
    if len(STATE["cooldown_tracker"]) > 3000:
        now = time.time()
        STATE["cooldown_tracker"] = {
            k: v for k, v in STATE["cooldown_tracker"].items()
            if (now - v) < (settings.SIGNAL_COOLDOWN_MINUTES * 60)
        }

class SignalRadarOrchestrator:
    def __init__(self):
        self.ai = AIAnalyzer()
        self.telegram = TelegramNotifier()

    async def handle_status(self, request):
        return web.json_response({
            "bot_status": STATE["bot_status"],
            "scanner_status": STATE["scanner_status"],
            "ai_status": STATE["ai_status"],
            "telegram_status": STATE["telegram_status"],
            "coins_scanned": STATE["coins_scanned"],
            "signals_generated": STATE["signals_generated"],
            "signals_rejected": STATE["signals_rejected"],
            "last_scan": STATE["last_scan_time"],
            "last_signal": STATE["last_signal_time"],
            "last_error": STATE["last_error"]
        })

    async def handle_health(self, request):
        return web.Response(text="OK", content_type="text/plain")

    async def handle_home(self, request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Solana Viral Signal Radar</title>
            <meta http-equiv="refresh" content="5">
            <style>
                body {{ background: #07090e; color: #fff; font-family: monospace; padding: 24px; }}
                .card {{ background: #111624; border: 1px solid #1e293b; padding: 20px; border-radius: 12px; max-width: 600px; }}
                .stat {{ color: #10b981; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>📡 SOLANA VIRAL RADAR (MANUAL TRADING MODE)</h2>
                <p>Status: <span class="stat">{STATE["bot_status"]}</span></p>
                <p>Coins Scanned: <span class="stat">{STATE["coins_scanned"]}</span></p>
                <p>Signals Generated: <span class="stat">{STATE["signals_generated"]}</span></p>
                <p>Signals Rejected: <span class="stat">{STATE["signals_rejected"]}</span></p>
                <p>Last Scan: <span>{STATE["last_scan_time"]}</span></p>
                <p>Last Signal: <span>{STATE["last_signal_time"]}</span></p>
                <p>Last Error: <span style="color:#ef4444;">{STATE["last_error"]}</span></p>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    async def process_token_pipeline(self, session: aiohttp.ClientSession, mint: str):
        if is_in_cooldown(mint):
            return

        metrics = await TokenDataFetcher.fetch_token_metrics(session, mint)
        if not metrics:
            return

        STATE["coins_scanned"] += 1
        symbol = metrics.get("symbol", "UNKNOWN")

        # 1. Deterministic Multi-Filter Check
        passed, reject_reason = FilterEngine.evaluate(metrics)
        if not passed:
            STATE["signals_rejected"] += 1
            logger.info(f"[REJECT] {reject_reason}")
            return

        logger.info(f"[FILTER] ${symbol} passed metrics. Running Social & Viral AI Analysis...")

        # 2. AI Scoring & Viral Cross-Validation
        ai_result = await self.ai.analyze_token(metrics)
        if not ai_result:
            STATE["signals_rejected"] += 1
            logger.warning(f"[REJECT] ${symbol} Reason: AI Analysis unavailable")
            return

        decision = ai_result.get("decision", "REJECT")
        overall_score = ai_result.get("overall_score", 0)
        confidence = ai_result.get("confidence", 0)
        viral_score = ai_result.get("viral_analysis", {}).get("viral_score", 0)
        on_chain_conf = ai_result.get("viral_analysis", {}).get("on_chain_confirmation", "FAIL")

        logger.info(f"[AI] ${symbol} decision={decision} score={overall_score} viral={viral_score} conf={confidence}% cross={on_chain_conf}")

        # 3. Final Quality & Viral Gate
        if (decision == "BUY_WATCH" and 
            overall_score >= settings.MIN_AI_SCORE and 
            confidence >= settings.MIN_CONFIDENCE and 
            viral_score >= settings.MIN_VIRAL_SCORE and 
            on_chain_conf == "PASS"):

            logger.info(f"[SIGNAL] ${symbol} ACCEPTED (Score: {overall_score}, Viral: {viral_score})")
            record_cooldown(mint)
            STATE["signals_generated"] += 1
            STATE["last_signal_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            await self.telegram.send_signal(metrics, ai_result, session=session)
        else:
            STATE["signals_rejected"] += 1
            reason_msg = f"Score ({overall_score}), Viral ({viral_score}), or Cross-Confirmation ({on_chain_conf}) below threshold"
            logger.info(f"[REJECT] ${symbol} Reason: {reason_msg}")

    async def scanner_loop(self):
        logger.info("Radar Loop running. 24/7 Social & On-Chain Cross-Validation Active.")
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    STATE["last_scan_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    candidate_mints = await TokenDataFetcher.get_market_candidates(session)
                    logger.info(f"[SCAN] {len(candidate_mints)} candidate tokens discovered")

                    for mint in candidate_mints:
                        try:
                            await self.process_token_pipeline(session, mint)
                            await asyncio.sleep(0.4)
                        except Exception as token_err:
                            logger.error(f"Error evaluating mint {mint}: {token_err}")
                            continue

                except Exception as e:
                    STATE["last_error"] = str(e)
                    logger.error(f"Scanner iteration error: {e}")

                await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)

    async def start_server(self):
        app = web.Application()
        app.router.add_get("/", self.handle_home)
        app.router.add_get("/health", self.handle_health)
        app.router.add_get("/status", self.handle_status)
        app.router.add_get("/api", self.handle_status)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", settings.PORT)
        await site.start()
        logger.info(f"Dashboard and Status API online on port {settings.PORT}")

    async def run(self):
        await self.start_server()
        asyncio.create_task(self.scanner_loop())
        while True:
            await asyncio.sleep(3600)

async def main():
    orchestrator = SignalRadarOrchestrator()
    await orchestrator.run()

if __name__ == "__main__":
    asyncio.run(main())
