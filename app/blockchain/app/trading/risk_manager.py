import logging

logger = logging.getLogger("solana-ai-bot")

class RiskManager:
    def __init__(self, min_liquidity=5000.0, min_score=80):
        self.min_liquidity = min_liquidity
        self.min_score = min_score

    def validate_trade(self, token_data: dict, ai_analysis: dict) -> bool:
        liquidity = token_data.get("liquidity", 0)
        score = ai_analysis.get("score", 0)
        decision = ai_analysis.get("decision", "HOLD")

        if liquidity < self.min_liquidity:
            logger.warning("Trade rejected: Liquidity ($%s) below minimum threshold.", liquidity)
            return False

        if score < self.min_score or decision != "BUY":
            logger.info("Trade rejected: AI Score (%s) below threshold (%s).", score, self.min_score)
            return False

        return True
      
