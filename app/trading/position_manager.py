import logging

logger = logging.getLogger("solana-ai-bot")

class PositionManager:
    def __init__(self, take_profit_pct=0.10, stop_loss_pct=0.05):
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct

    def check_exit_signals(self, buy_price: float, current_price: float) -> str:
        change = (current_price - buy_price) / buy_price
        
        if change >= self.take_profit_pct:
            logger.info("Take-profit triggered at +%.2f%%", change * 100)
            return "SELL_PROFIT"
        elif change <= -self.stop_loss_pct:
            logger.warning("Stop-loss triggered at %.2f%%", change * 100)
            return "SELL_LOSS"
            
        return "HOLD"
      
