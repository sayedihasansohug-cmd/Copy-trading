import logging

logger = logging.getLogger("solana-ai-bot")

class PaperTrader:
    def __init__(self, starting_balance=500.0):
        self.balance = float(starting_balance)
        self.positions = {}

    def get_balance(self):
        return self.balance

    def buy(self, token_address, symbol, confidence, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.positions[token_address] = {
                "symbol": symbol,
                "amount": amount,
                "buy_confidence": confidence
            }
            logger.info("PAPER BUY Successful: %s | Spent: $%s", symbol, amount)
            return True
        return False

    def sell(self, token_address, price):
        if token_address in self.positions:
            pos = self.positions.pop(token_address)
            pnl = pos["amount"] * 0.10  # Mock 10% profit margin
            self.balance += (pos["amount"] + pnl)
            logger.info("PAPER SELL Successful: %s | PNL: $%s", pos["symbol"], pnl)
            return pnl
        return False
      
