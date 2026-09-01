import os
import asyncio
from datetime import datetime
from aiohttp import web
from sqlalchemy import select
from loguru import logger

from app.config import settings
from app.database.database import init_db, AsyncSessionLocal
from app.database.models import Position
from app.ai.analyzer import AIAnalyzer
from app.market.scanner import MarketScanner
from app.market.token_data import TokenDataFetcher
from app.trading.risk_manager import RiskManager
from app.trading.executor import TradeExecutor
from app.trading.position_manager import PositionManager
from app.telegram.bot import TelegramNotifier
from app.blockchain.solana import SolanaManager
from app.blockchain.wallet_monitor import WalletMonitor
from app.ui import HTML_DASHBOARD

APP_STATE = {
    "bot_active": True,
    "logs": []
}

def add_log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    APP_STATE["logs"].insert(0, {"time": timestamp, "msg": message, "level": level})
    if len(APP_STATE["logs"]) > 40:
        APP_STATE["logs"].pop()

class TradingBotApp:
    def __init__(self):
        self.ai = AIAnalyzer()
        self.scanner = MarketScanner()
        self.executor = TradeExecutor()
        self.position_manager = PositionManager()
        self.notifier = TelegramNotifier()
        self.solana_manager = SolanaManager()
        self.wallet_monitor = WalletMonitor(self.solana_manager)

    async def handle_dashboard(self, request):
        return web.Response(text=HTML_DASHBOARD, content_type='text/html')

    async def handle_status_api(self, request):
        balance = await self.wallet_monitor.get_sol_balance()
        async with AsyncSessionLocal() as session:
            stmt = select(Position).where(Position.is_active == True)
            result = await session.execute(stmt)
            open_pos = result.scalars().all()
            positions_data = [
                {
                    "symbol": p.symbol,
                    "mint": p.token_mint,
                    "entry_price": p.entry_price_usd,
                    "sol_invested": p.sol_invested
                }
                for p in open_pos
            ]

        return web.json_response({
            "bot_active": APP_STATE["bot_active"],
            "wallet_address": self.solana_manager.public_key_str,
            "wallet_balance": balance,
            "trade_size": settings.TRADE_AMOUNT_SOL,
            "positions": positions_data,
            "logs": APP_STATE["logs"]
        })

    async def handle_toggle_bot(self, request):
        APP_STATE["bot_active"] = not APP_STATE["bot_active"]
        state_str = "ACTIVE" if APP_STATE["bot_active"] else "PAUSED"
        add_log(f"Bot status: {state_str}", "INFO")
        return web.json_response({"success": True, "bot_active": APP_STATE["bot_active"]})

    async def handle_manual_scan(self, request):
        data = await request.json()
        raw_text = data.get("text", "")
        add_log(f"Signal received: {raw_text[:35]}...", "INFO")
        
        analysis = await self.ai.analyze_sentiment(raw_text)
        if not analysis.get("is_tradable_meme") or analysis.get("confidence_score", 0) < 70:
            add_log(f"Rejected: Low confidence ({analysis.get('confidence_score')}%)", "WARNING")
            return web.json_response({"success": False, "message": f"Low Hype Score ({analysis.get('confidence_score')}%)"})

        ticker = analysis.get("ticker")
        ca = analysis.get("contract_address")
        pair_data = await TokenDataFetcher.get_pair_by_address(ca) if ca else await TokenDataFetcher.get_pair_by_ticker(ticker)

        is_safe, reason = RiskManager.evaluate_token(pair_data)
        if not is_safe:
            add_log(f"Risk Rejected: {reason}", "ERROR")
            return web.json_response({"success": False, "message": f"Risk Check Failed: {reason}"})

        token_mint = pair_data["baseToken"]["address"]
        symbol = pair_data["baseToken"]["symbol"]
        price_usd = float(pair_data.get("priceUsd", 0) or 0)

        try:
            tx_hash = await self.executor.execute_buy(token_mint, settings.TRADE_AMOUNT_SOL)
            estimated_tokens = (settings.TRADE_AMOUNT_SOL * 150.0) / price_usd if price_usd > 0 else 0

            await self.position_manager.register_position(
                token_mint=token_mint,
                symbol=symbol,
                entry_price=price_usd,
                token_amount=estimated_tokens,
                sol_invested=settings.TRADE_AMOUNT_SOL,
                tx_hash=tx_hash
            )
            add_log(f"Bought {symbol}! TX: {tx_hash[:12]}...", "SUCCESS")
            return web.json_response({"success": True, "message": f"Successfully Sniped {symbol}!"})
        except Exception as e:
            add_log(f"Trade failed: {str(e)}", "ERROR")
            return web.json_response({"success": False, "message": f"Error: {str(e)}"})

    async def handle_close_position(self, request):
        data = await request.json()
        mint = data.get("mint")
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Position).where(Position.token_mint == mint, Position.is_active == True)
                result = await session.execute(stmt)
                pos = result.scalars().first()
                if pos:
                    raw_units = int(pos.token_amount * 1_000_000)
                    tx_hash = await self.executor.execute_sell(pos.token_mint, raw_units)
                    pos.is_active = False
                    pos.sell_tx_hash = tx_hash
                    pos.closed_at = datetime.utcnow()
                    await session.commit()
                    add_log(f"Sold position {pos.symbol}", "SUCCESS")
                    return web.json_response({"success": True, "message": f"Sold {pos.symbol} successfully!"})
            return web.json_response({"success": False, "message": "Position not found"})
        except Exception as e:
            return web.json_response({"success": False, "message": f"Sell error: {str(e)}"})

    async def start_server(self):
        app = web.Application()
        app.router.add_get("/", self.handle_dashboard)
        app.router.add_get("/api/status", self.handle_status_api)
        app.router.add_post("/api/bot/toggle", self.handle_toggle_bot)
        app.router.add_post("/api/scan/manual", self.handle_manual_scan)
        app.router.add_post("/api/position/close", self.handle_close_position)

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 10000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        add_log(f"Trading UI & API online on port {port}", "SUCCESS")

    async def run(self):
        await init_db()
        await self.start_server()
        balance = await self.wallet_monitor.get_sol_balance()
        add_log(f"Wallet: {self.solana_manager.public_key_str[:6]}... | {balance:.4f} SOL", "SUCCESS")
        asyncio.create_task(self.position_manager.monitor_positions_loop())

        async for post in self.scanner.stream_social_narratives():
            if APP_STATE["bot_active"]:
                analysis = await self.ai.analyze_sentiment(post)
                if analysis.get("is_tradable_meme") and analysis.get("confidence_score", 0) >= 75:
                    add_log(f"Auto-Sniping: {analysis.get('ticker')}", "SUCCESS")

async def main():
    bot = TradingBotApp()
    await bot.run()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
