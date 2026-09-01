import asyncio
from loguru import logger
from app.config import settings
from app.database.database import init_db
from app.ai.analyzer import AIAnalyzer
from app.market.scanner import MarketScanner
from app.market.token_data import TokenDataFetcher
from app.trading.risk_manager import RiskManager
from app.trading.executor import TradeExecutor
from app.trading.position_manager import PositionManager
from app.telegram.bot import TelegramNotifier
from app.blockchain.solana import SolanaManager
from app.blockchain.wallet_monitor import WalletMonitor

class TradingBotApp:
    def __init__(self):
        self.ai = AIAnalyzer()
        self.scanner = MarketScanner()
        self.executor = TradeExecutor()
        self.position_manager = PositionManager()
        self.notifier = TelegramNotifier()
        self.solana_manager = SolanaManager()
        self.wallet_monitor = WalletMonitor(self.solana_manager)

    async def process_signal(self, raw_text: str):
        logger.info("Evaluating incoming market signal...")
        
        analysis = await self.ai.analyze_sentiment(raw_text)
        if not analysis.get("is_tradable_meme") or analysis.get("confidence_score", 0) < 75:
            logger.debug(f"Signal filtered out. Score: {analysis.get('confidence_score')}")
            return

        ticker = analysis.get("ticker")
        ca = analysis.get("contract_address")
        logger.info(f"Target identified -> Ticker: {ticker}, CA: {ca}, Score: {analysis['confidence_score']}%")

        pair_data = None
        if ca:
            pair_data = await TokenDataFetcher.get_pair_by_address(ca)
        elif ticker:
            pair_data = await TokenDataFetcher.get_pair_by_ticker(ticker)

        is_safe, reason = RiskManager.evaluate_token(pair_data)
        if not is_safe:
            logger.warning(f"Risk rejected trade: {reason}")
            return

        token_mint = pair_data["baseToken"]["address"]
        symbol = pair_data["baseToken"]["symbol"]
        price_usd = float(pair_data.get("priceUsd", 0) or 0)

        try:
            tx_hash = await self.executor.execute_buy(token_mint, settings.TRADE_AMOUNT_SOL)
            
            # Estimate token units acquired
            sol_price_est = 150.0
            estimated_tokens = (settings.TRADE_AMOUNT_SOL * sol_price_est) / price_usd if price_usd > 0 else 0

            await self.position_manager.register_position(
                token_mint=token_mint,
                symbol=symbol,
                entry_price=price_usd,
                token_amount=estimated_tokens,
                sol_invested=settings.TRADE_AMOUNT_SOL,
                tx_hash=tx_hash
            )

            await self.notifier.send_alert(
                f"⚡ *NEW POSITION OPENED*\n\n"
                f"🪙 *Token:* {symbol}\n"
                f"📍 *Mint:* `{token_mint}`\n"
                f"💰 *Size:* {settings.TRADE_AMOUNT_SOL} SOL\n"
                f"💵 *Entry Price:* ${price_usd:.6f}\n"
                f"🎯 *AI Score:* {analysis['confidence_score']}%\n\n"
                f"🔗 [Solscan](https://solscan.io/tx/{tx_hash})"
            )
        except Exception as e:
            logger.error(f"Buy trade execution failed: {e}")
            await self.notifier.send_alert(f"❌ *Buy Order Failed:* `{str(e)}`")

    async def run(self):
        logger.info("Initializing AI Meme Trading Bot Engine...")
        await init_db()

        balance = await self.wallet_monitor.get_sol_balance()
        logger.info(f"Wallet connected: {self.solana_manager.public_key_str} | Balance: {balance:.4f} SOL")

        # Start position manager loop in background
        asyncio.create_task(self.position_manager.monitor_positions_loop())

        # Start narrative scanner loop
        async for post in self.scanner.stream_social_narratives():
            await self.process_signal(post)

async def main():
    app = TradingBotApp()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
